ALGORITHMS USED
1. Random Forest Regressor
Purpose: Predict the final grade (numeric score)

Library: sklearn.ensemble.RandomForestRegressor

Why: Handles small data well, avoids overfitting, and supports non-linear relationships

2. Random Forest Classifier
Purpose: Predict whether a student is at risk of dropout (binary classification)

Library: sklearn.ensemble.RandomForestClassifier

Why: Robust classifier for mixed numeric features, doesn't require feature scaling

3. OpenAI GPT-3.5 (via openai.ChatCompletion)
Purpose: Generate personalized study recommendations

Input: Subject, score, result status, attendance

Why: Leverages natural language understanding to provide human-like advice tailored to academic context

METHODOLOGY

Step 1: Data Collection & Preprocessing
Input taken from student_data.csv

Final average grade calculated as mean of internal and assignment scores

Step 2: Model Training
train_model.py trains two models:

Regressor: to predict grade

Classifier: to predict dropout risk

Models saved using pickle in /model folder

Step 3: Prediction & Analysis (in app.py)
Based on user input (USN or semester), relevant records are selected

Features passed to trained models

Grade → converted to PASS/FAIL

Dropout → converted to High/Low risk

Curriculum mismatch is detected via curriculum.json

Recommendations generated via OpenAI API

Step 4: Recommendation Generation
For each subject, a prompt is created and sent to OpenAI API:

text
Copy
Edit
A student scored 42 in C Programming. Their attendance is 55%.
Recommend learning strategies in simple language.
Step 5: Result Display
Output is rendered in index.html with:

Subject name

Grade (score)

PASS/FAIL

Dropout chance

Personalized AI recommendation

Curriculum gap (if any)

