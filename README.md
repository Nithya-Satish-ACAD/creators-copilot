## 🧩 Features

### Rubric Generator
Generate structured evaluation rubrics for activities or projects, based on learning outcomes and total marks. If marks aren't provided, it defaults to 10.

### Quiz Generator
Create 5 multiple-choice questions (MCQs) for any topic, aligned with a specified Bloom’s Taxonomy level. Output includes options and clearly identified answers.

## 🛠️ Setup Instructions

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-username/creators-copilot.git
   cd creators-copilot
2. **Install required packaged**
   ```bash
   pip install streamlit openai python-dotenv
3. **Add your OpenAI API key**
  Create a .env file in the root directory:
   ```bash
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
4. **Run the App**
   ```bash
   streamlit run src/app.py

## **📁 Project Structure**
```
creators-copilot/
├── prompts/               # JSON prompt templates
├── src/
│   ├── app.py             # Streamlit entry point
│   ├── logic/             # Backend logic for prompt handling
│   └── pages/             # Streamlit UI pages
└── .env                   # API key (not pushed)

