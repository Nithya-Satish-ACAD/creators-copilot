import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_quiz_prompt():
    path = os.path.join(os.path.dirname(__file__), "../../prompts/quiz_generator.json")
    with open(path, "r") as f:
        return json.load(f)

def build_quiz_prompt(template, topic, bloom_level):
    return template.replace("{{syllabus}}", syllabus).replace("{{format}}", format)

def generate_quiz(prompt_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7
    )
    return response.choices[0].message.content
