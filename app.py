import os
from flask import Flask, redirect, render_template, request, jsonify, session, url_for,send_file
import pandas as pd
import pickle
import json
from utils import generate_study_recommendation
import csv
from flask import make_response
from xhtml2pdf import pisa
import io
import subprocess
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
app.secret_key = 'supersecret'
grade_model = pickle.load(open("model/performance_model.pkl", "rb"))
dropout_model = pickle.load(open("model/dropout_model.pkl", "rb"))
student_data = pd.read_csv("student_data.csv")
with open("curriculum.json") as f:
    curriculum = json.load(f)

curriculum_file = "curriculum.json"
STUDENT_CSV_FILE = "student_data.csv"

def load_curriculum():
    with open(curriculum_file, "r") as f:
        data = json.load(f)
        for sem in ['1', '2', '3', '4']:
            if sem not in data:
                data[sem] = []
        return data

def save_curriculum(data):
    cleaned = {sem: data.get(sem, []) for sem in ['1', '2', '3', '4']}
    with open(curriculum_file, "w") as f:
        json.dump(cleaned, f, indent=4)

def load_students():
    with open(STUDENT_CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_students(data):
    with open(STUDENT_CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'usn', 'name', 'semester', 'subject', 'attendance',
            'internal1', 'internal2', 'internal3', 'assignment'
        ])
        writer.writeheader()
        writer.writerows(data)    

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['POST'])
def login():
    uname = request.form.get('username')
    pword = request.form.get('password')
    if uname == 'admin' and pword == 'admin':
        session['logged_in'] = True
        return redirect(url_for('home'))  # redirect to /main
    else:
        return render_template("index.html", error="Invalid username or password")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/main')
def home():
    semesters = sorted(set(student_data['semester'].astype(str)))
    return render_template("main.html", semesters=semesters, result=None)


@app.route('/search', methods=['POST'])
def search():
    usn = request.form.get("usn").strip()
    sem = request.form.get("semester").strip()
    filtered = student_data

    if usn:
        filtered = filtered[filtered['usn'] == usn]
    if sem:
        filtered = filtered[filtered['semester'] == int(sem)]

    output = ""
    for usn_val in filtered['usn'].unique():
        stu_df = filtered[filtered['usn'] == usn_val]
        name = stu_df.iloc[0]['name']
        sems = stu_df['semester'].unique()
        output += f"<h3>{name} ({usn_val})</h3>"
        for s in sems:
            sem_df = stu_df[stu_df['semester'] == s]
            output += f"<b>Semester {s}</b><ul>"

            actual_subjects = set(sem_df['subject'])
            expected_subjects = set(curriculum.get(str(s), []))
            gap = expected_subjects - actual_subjects

            for _, row in sem_df.iterrows():
                cols = ['attendance', 'internal1', 'internal2', 'internal3', 'assignment']
                X = pd.DataFrame([[row[col] for col in cols]], columns=cols)

                grade = grade_model.predict(X)[0]
                dropout = dropout_model.predict(X)[0]
                status = "✅ Student has highest chance to PASS" if grade >= 50 else "❌ Student has highest chance to FAIL"

                attendance = row['attendance']
                total_score = row['internal1'] + row['internal2'] + row['internal3'] + row['assignment']
                max_score = 50 + 50 + 50 + 10
                avg_score = (total_score / max_score) * 100

                dropout_text = ""
                if attendance < 60 and avg_score < 50:
                    dropout_text = "⚠️ High dropout risk! (Low attendance + Low performance)"
                elif attendance < 60:
                    dropout_text = "⚠️ Risk due to low attendance"
                elif avg_score < 50:
                    dropout_text = "⚠️ Risk due to low average score"
                else:
                    dropout_text = "✔️ Low dropout risk"
                rec = generate_study_recommendation(row['subject'], round(grade, 2), status, row['attendance'])

                output += (
                    f"<li>{row['subject']}: {round(grade, 2)} ({status})<br>"
                    f"<b>Dropout Chance:</b> {dropout_text}<br>"
                    f"<i>{rec}</i></li>"
                )

            output += f"</ul><b>Curriculum Gap:</b> {', '.join(gap) if gap else 'None'}<hr>"

    semesters = sorted(set(student_data['semester'].astype(str)))
    return render_template("index.html", semesters=semesters, result=output)

@app.route('/curriculum', methods=['GET'])
def get_curriculum():
    return jsonify(load_curriculum())

@app.route('/curriculumui')
def curriculum_ui():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template("curriculum.html")

@app.route('/curriculumadd', methods=['POST'])
def add_subject():
    sem = request.json.get("semester")
    subject = request.json.get("subject")
    data = load_curriculum()
    if subject and sem in data and subject not in data[sem]:
        data[sem].append(subject)
        save_curriculum(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Subject exists or invalid"}), 400

@app.route('/curriculumupdate', methods=['POST'])
def update_subject():
    sem = str(request.json.get("semester")) 
    old_subject = request.json.get("old_subject")
    new_subject = request.json.get("new_subject")
    data = load_curriculum()

    if sem in data and old_subject in data[sem]:
        idx = data[sem].index(old_subject)
        data[sem][idx] = new_subject
        save_curriculum(data)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Not found"}), 404

@app.route('/curriculumdelete', methods=['POST'])
def delete_subject():
    sem = request.json.get("semester")
    subject = request.json.get("subject")
    data = load_curriculum()
    if sem in data and subject in data[sem]:
        data[sem].remove(subject)
        save_curriculum(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Not found"}), 404

@app.route('/students', methods=['GET'])
def get_students():
    return jsonify(load_students())
@app.route('/subjects/<int:semester>')
def get_subjects(semester):
    with open('curriculum.json') as f:
        curriculum = json.load(f)

    # Get subjects for that semester (stored as string keys)
    subjects = curriculum.get(str(semester), [])
    return jsonify({'subjects': subjects})


@app.route('/students/add', methods=['POST'])
def add_student():
    new_entry = request.get_json()

    if not os.path.exists(STUDENT_CSV_FILE):
        df = pd.DataFrame(columns=['usn', 'name', 'semester', 'subject', 'attendance', 'internal1', 'internal2', 'internal3', 'assignment'])
    else:
        df = pd.read_csv(STUDENT_CSV_FILE)

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(STUDENT_CSV_FILE, index=False)
    return jsonify({"status": "success"})

@app.route('/students/update', methods=['POST'])
def update_student():
    data = request.json
    df = pd.read_csv(STUDENT_CSV_FILE)

    mask_duplicate = (
        (df['usn'] == data['usn']) &
        (df['semester'] == int(data['semester'])) &
        (df['subject'] == data['new_subject']) &
        (df['subject'] != data['old_subject'])  
    )

    if mask_duplicate.any():
        return jsonify({"status": "error", "message": "Duplicate subject entry for this USN and semester"}), 400


    mask = (
        (df['usn'] == data['usn']) &
        (df['semester'] == int(data['semester'])) &
        (df['subject'] == data['old_subject'])
    )

    if not mask.any():
        return jsonify({"status": "error", "message": "Record not found"}), 404

    df.loc[mask, ['subject', 'attendance', 'internal1', 'internal2', 'internal3', 'assignment']] = [
        data['new_subject'], data['attendance'], data['internal1'], data['internal2'], data['internal3'], data['assignment']
    ]
    df.to_csv(STUDENT_CSV_FILE, index=False)
    return jsonify({"status": "success"})

@app.route('/students/delete', methods=['POST'])
def delete_student():
    payload = request.json
    data = load_students()
    new_data = [
        row for row in data
        if not (row['usn'] == payload['usn'] and
                row['semester'] == payload['semester'] and
                row['subject'] == payload['subject'])
    ]
    save_students(new_data)
    return jsonify({"status": "success"})

@app.route('/status/<usn>')
def generate_student_status(usn):

    df = pd.read_csv(STUDENT_CSV_FILE)
    filtered = df[df['usn'] == usn]

    if filtered.empty:
        return f"No data found for USN {usn}", 404

    name = filtered.iloc[0]['name']
    output = f"<h2>Student Status Report: {name} ({usn})</h2>"

    overall_grades = []
    overall_dropout_flags = []

    subjects = []
    scores = []

    for sem in sorted(filtered['semester'].unique()):
        sem_df = filtered[filtered['semester'] == sem]
        output += f"<h4>Semester {sem}</h4><ul>"

        actual_subjects = set(sem_df['subject'])
        expected_subjects = set(curriculum.get(str(sem), []))
        gap = expected_subjects - actual_subjects

        for _, row in sem_df.iterrows():
            if pd.isnull(row[['attendance', 'internal1', 'internal2', 'internal3', 'assignment']]).any():
                continue

            internals = sorted([row['internal1'], row['internal2'], row['internal3']], reverse=True)
            best_two_sum = internals[0] + internals[1]
            total_score = best_two_sum + row['assignment']
            max_score = 50
            avg_score = (total_score / max_score) * 100
            grade = total_score

            subjects.append(row['subject'])
            scores.append(total_score)

            X = pd.DataFrame([[row['attendance'], row['internal1'], row['internal2'], row['internal3'], row['assignment']]],
                             columns=['attendance', 'internal1', 'internal2', 'internal3', 'assignment'])
            dropout = dropout_model.predict(X)[0]

            overall_grades.append(grade)
            overall_dropout_flags.append(dropout)

            status = "✅ PASS" if grade > 30 else "❌ FAIL"

            if row['attendance'] < 60 and avg_score < 50:
                dropout_text = "⚠️ High dropout risk (Low attendance + Low performance)"
            elif row['attendance'] < 60:
                dropout_text = "⚠️ Risk due to low attendance"
            elif avg_score < 50:
                dropout_text = "⚠️ Risk due to low average score"
            elif grade <= 30:
                dropout_text = "⚠️ Risk due to failing grade"
            else:
                dropout_text = "✔️ Low dropout risk"

            rec = generate_study_recommendation(row['subject'], round(grade, 2), status, row['attendance'])

            output += (
                f"<li><b>{row['subject']}:</b> {round(grade, 2)} ({status})<br>"
                f"<b>Dropout:</b> {dropout_text}<br>"
                f"<i>{rec}</i></li>"
            )

        output += f"</ul><b>Curriculum Gap:</b> {', '.join(gap) if gap else 'None'}<hr>"

    if overall_grades:
        average_grade = sum(overall_grades) / len(overall_grades)
        performance_tag = "🌟 Excellent" if average_grade >= 45 else "✅ Average" if average_grade >= 30 else "❌ At Risk"
    else:
        average_grade = 0
        performance_tag = "❌ No valid grades"

    overall_dropout = any(overall_dropout_flags)
    overall_dropout_text = "✔️ High dropout risk due to curriculam gap" if len(gap) != 0 else "✔️ Low dropout risk" if not overall_dropout else "⚠️ One or more subjects show dropout risk"

    output += f"""
    <h3>📊 Overall Performance</h3>
    <p><b>Predicted Average Grade:</b> {round(average_grade, 2)} ({performance_tag})</p>
    <p><b>Overall Dropout Risk:</b> {overall_dropout_text}</p>
    """

    # Plot the chart
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(subjects, scores, color='skyblue')
    ax.set_ylim(0, 50)
    ax.set_title(f"Subject-wise Total Marks for {name}")
    ax.set_ylabel("Marks (out of 50)")
    ax.set_xticks(range(len(subjects)))
    ax.set_xticklabels(subjects, rotation=45, ha='right')

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, f'{yval:.1f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')
    chart_html = f'<img src="data:image/png;base64,{img_base64}" style="width:100%; max-width:600px;" />'

    output += f"<h3>📈 Subject-wise Marks Chart</h3>{chart_html}"

    html = f"""
    <html>
    <head>
        <title>Student Report</title>
        <style>
            body {{
                font-size: 14px;
                font-family: Times New Roman, sans-serif;
            }}
            h2 {{
                font-size: 20px;
            }}
            h4 {{
                font-size: 16px;
            }}
            ul {{
                font-size: 14px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            b {{
                font-size: 14px;
            }}
        </style>
    </head>
    <body>{output}</body>
    </html>
    """
    pdf = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        return "PDF generation failed", 500

    pdf.seek(0)
    return send_file(pdf, download_name=f"{usn}_report.pdf", as_attachment=True, mimetype='application/pdf')

@app.route('/train-model', methods=['POST'])
def train_model_route():
    try:
        subprocess.run(['python', 'train_model.py'], check=True)
        return jsonify({"status": "success", "message": "Model trained successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Training failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
