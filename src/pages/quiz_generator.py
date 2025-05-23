import streamlit as st
from logic.quiz_logic import load_quiz_prompt, build_quiz_prompt, generate_quiz

st.title("🧠 Quiz Generator")
st.markdown("Generate a set of 5 MCQs based on a topic and Bloom's level.")

topic = st.text_input("Topic")
bloom_level = st.selectbox("Bloom's Level", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"])

if st.button("Generate Quiz"):
    prompt_data = load_quiz_prompt()
    filled_prompt = build_quiz_prompt(prompt_data["prompt_template"], topic, bloom_level)

    with st.spinner("Generating quiz..."):
        try:
            result = generate_quiz(filled_prompt)
            st.success("Quiz Generated:")
            st.markdown(result)
        except Exception as e:
            st.error(f"Error: {e}")
