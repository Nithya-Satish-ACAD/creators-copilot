import pytest
from helper import parse_prompt_template

def test_parse_prompt_template_required_input_variables_happy_path():
    user_input = {
        "number_of_questions": 10,
        "syllabus": "Introduction to Programming with Python: Taking Input, Formatted Strings"
    }
    rendered_prompt = parse_prompt_template("quiz_v1", user_input)
    expected = "You are an expert in designing multiple-choice quizzes for undergraduate-level university courses. Your task is to generate 10 high-quality multiple-choice questions based on the syllabus Introduction to Programming with Python: Taking Input, Formatted Strings. - Each question must include one correct answer and three distinct, plausible distractors. - Label the options as A, B, C, and D, with the correct answer randomly positioned. Quality Guidelines: - Align all questions with the provided syllabus or learning resource. - Avoid introducing content or terminology not present in the syllabus. - Use clear, concise language appropriate for undergraduate learners. - Ensure a variety of question styles to assess different cognitive skills. - Avoid redundant or overly similar questions."
    assert rendered_prompt == expected
