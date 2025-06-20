from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Missing OPENAI_API_KEY in .env")

def generate_course_prompt(data):
    return f"""
            You are an expert course designer. Generate a course outline based on the following details:

            Course Name: {data.course_name}
            Description: {data.description}
            Duration: {data.duration_days} days
            Total Hours: {data.total_hours} hours

            Return a structured JSON containing:
            - course_description (Provide a brief introduction and overview of the Sprint, subject matter, relevance, key concepts covered, skills gained, instructional methods and assessment used, and expected course outcomes.)
            - methodology (seperated by commas and no paragraphs)
            - course_outcomes (3 - 5 bullet points)
            - job_roles_prepared_for
            - industry_skills_gained
            - Do not include any emojis
            - Keep it professional
            """

def chat_revise_prompt(edited_data, user_instruction):
    return f"""
           You are an expert course reviser. The user has a specific instruction to improve part of a course overview.

            Below is the full current course overview in JSON format. You must:
            1. Understand which section to modify based on the user's instruction.
            2. Make only the necessary changes. Leave all other parts exactly as-is.
            3. Always return a full JSON with the same keys: course_description, methodology, course_outcomes, job_roles_prepared_for, industry_skills_gained.
            4. Ensure the output is well-formatted and valid JSON. If bullet points are requested, use JSON lists.
            5. REMOVE all emojis or special characters if the user requests a professional version.

            ---

            {edited_data}

            User says: "{user_instruction}"

            Revise the course while keeping structure and formatting. Return as valid JSON.
            Return only the full updated JSON, and ensure that if the user mentions “remove emojis” or “make it professional”, you eliminate all emoji symbols.
            """

def call_openai(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a curriculum assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
