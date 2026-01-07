from openai import OpenAI
import os

client = OpenAI(api_key="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")

def generate_study_recommendation(subject, score, result, attendance):
    try:
        prompt = (
            f"A student scored {score} in {subject} with result {result} and attendance {attendance}%. "
            "Give study suggestions and strategies staright to the point.It shold be in paragraph and analyze the data and provide the accurate suggesstions and it should not be the generic one and maximum 10 sentences. What is the dropout risk of this student and how to avoid it."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful academic advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500 
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "⚠️ Unable to generate recommendation."
