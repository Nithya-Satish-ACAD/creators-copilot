import streamlit as st
from logic.quiz_logic import load_quiz_prompt, build_quiz_prompt, generate_quiz

st.title("🧠 Quiz Generator")
st.markdown("Generate a set of 5 MCQs based on a topic and Bloom's level.")

syllabus = st.text_input("Syllabus")
format = st.text_input("Format")

if st.button("Generate Quiz"):
    prompt_data = load_quiz_prompt()
    filled_prompt = build_quiz_prompt(prompt_data["prompt_template"], syllabus, format)

    with st.spinner("Generating quiz..."):
        try:
            result = generate_quiz(filled_prompt)
            st.success("Quiz Generated:")
            st.markdown(result)
        except Exception as e:
            st.error(f"Error: {e}")
