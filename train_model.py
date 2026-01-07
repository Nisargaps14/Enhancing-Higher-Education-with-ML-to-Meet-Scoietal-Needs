import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

data = pd.read_csv("student_data.csv")
data = data.dropna(subset=['attendance', 'internal1', 'internal2', 'internal3', 'assignment'])

best_two_internals = data[['internal1', 'internal2', 'internal3']].apply(
    lambda row: sum(sorted(row, reverse=True)[:2]), axis=1
)
data['final_grade'] = best_two_internals + data['assignment']

X = data[['attendance', 'internal1', 'internal2', 'internal3', 'assignment']]
y_grade = data['final_grade']
y_dropout = [1 if att < 60 and grade < 30 else 0 for att, grade in zip(data['attendance'], data['final_grade'])]

grade_model = RandomForestRegressor().fit(X, y_grade)
dropout_model = RandomForestClassifier().fit(X, y_dropout)

os.makedirs("model", exist_ok=True)
pickle.dump(grade_model, open("model/performance_model.pkl", "wb"))
pickle.dump(dropout_model, open("model/dropout_model.pkl", "wb"))

print("✅ Models trained and saved in /model directory.")
