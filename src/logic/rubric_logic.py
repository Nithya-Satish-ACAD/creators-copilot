import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (if .env is used)
load_dotenv()
# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load rubric prompt
def load_rubric_prompt():
    path = "../prompts/rubrics_generator.json"
    with open(path, "r") as f:
        return json.load(f)

# Build filled prompt
def build_prompt(template, activity_title, description, learning_outcomes, total_marks):
    marks_value = total_marks.strip() if total_marks.strip() else "10"
    prompt = template.replace("{{activity_title}}", activity_title)
    prompt = prompt.replace("{{description}}", description)
    prompt = prompt.replace("{{learning_outcomes}}", learning_outcomes)
    prompt = prompt.replace("{{total_marks}}", marks_value)
    return prompt

# Call OpenAI to generate rubric
def generate_rubric(prompt_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7
    )
    return response.choices[0].message.content
