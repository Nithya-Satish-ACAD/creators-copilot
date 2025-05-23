import streamlit as st
from dotenv import load_dotenv
import os

from logic.rubric_logic import load_rubric_prompt, build_prompt, generate_rubric

# Load environment variables
load_dotenv()

# Load prompt JSON
rubric_prompt_data = load_rubric_prompt()

# UI
st.title("🎯 Rubric Generator")
st.markdown("Fill out the form below to generate a structured evaluation rubric.")

activity_title = st.text_input("Activity / Project Title")
description = st.text_area("Description", height=120)
learning_outcomes = st.text_area("Learning Outcomes (comma-separated)", height=100)
total_marks = st.text_input("Total Marks (optional)", placeholder="Defaults to 10")

if st.button("Generate Rubric"):
    filled_prompt = build_prompt(
        rubric_prompt_data["prompt_template"],
        activity_title,
        description,
        learning_outcomes,
        total_marks
    )

    with st.spinner("Generating..."):
        try:
            result = generate_rubric(filled_prompt)
            st.success("Rubric Generated:")
            st.markdown(result)
        except Exception as e:
            st.error(f"Error: {e}")
