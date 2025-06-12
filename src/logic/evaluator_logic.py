import os
import re
import zipfile
import io
import json
import concurrent.futures
import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
from groq import Groq
import time
from typing import Dict, List, Tuple, Any, Optional
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import pprint
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
from pathlib import Path
import base64  # Added for base64 decoding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MERGED_OUTPUT_DIR = "merged_outputs"
if not os.path.exists(MERGED_OUTPUT_DIR):
    os.makedirs(MERGED_OUTPUT_DIR)
    logger.info(f"Created directory: {MERGED_OUTPUT_DIR}")
    
def load_prompt_from_json(file_path = 'prompt.json', template_key="EVALUATION_PROMPT_TEMPLATE"):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data[template_key]
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except KeyError:
        raise KeyError(f"The key '{template_key}' was not found in the JSON file.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"The file {file_path} contains invalid JSON.")
        
def init_groq_client_mark_scheme():
    try:
        api_key = os.getenv("GROQ_API_KEY", "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")
        if not api_key:
            raise ValueError("No Groq API key found.")
        client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully for mark scheme.")
        return client
    except ImportError:
        logger.error("Groq client not installed.")
        raise ImportError("Groq client not installed. Install with 'pip install groq'")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        raise

def init_groq_client_parse_mark_scheme():
    try:
        api_key = os.getenv("GROQ_API_KEY", "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")
        if not api_key:
            raise ValueError("No Groq API key found.")
        client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully for parsing mark scheme.")
        return client
    except ImportError:
        logger.error("Groq client not installed.")
        raise ImportError("Groq client not installed. Install with 'pip install groq'")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        raise

def init_groq_client_topic():
    try:
        api_key = os.getenv("GROQ_API_KEY", "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")
        if not api_key:
            raise ValueError("No Groq API key found.")
        client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully for topic analysis.")
        return client
    except ImportError:
        logger.error("Groq client not installed.")
        raise ImportError("Groq client not installed. Install with 'pip install groq'")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        raise

def init_groq_clients() -> List[Groq]:
    """
    Initialize a list of Groq clients with different API keys.
    Returns a list of initialized clients.
    """
    api_keys = [
        os.getenv("GROQ_API_KEY", "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"),
        os.getenv("GROQ_API_KEY", "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"),
        os.getenv("GROQ_API_KEY", "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"),
        os.getenv("GROQ_API_KEY", "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"),
        os.getenv("GROQ_API_KEY", "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")
    ]
    clients = []
    for i, api_key in enumerate(api_keys):
        try:
            if not api_key:
                raise ValueError(f"No Groq API key provided for client {i+1}")
            client = Groq(api_key=api_key)
            logger.info(f"Groq client {i+1} initialized successfully")
            clients.append(client)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client {i+1}: {str(e)}")
            continue
    if not clients:
        raise ValueError("No Groq clients could be initialized")
    return clients


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
        cleaned_text = text.replace('**', ' ').strip()
        logger.info("Successfully extracted and cleaned text from PDF")
        return cleaned_text
    except Exception as e:
        logger.error(f"Failed to extract and clean text from PDF: {str(e)}")
        return ""

def parse_questions_and_marks(text: str) -> dict:
    if not text:
        st.warning("Empty text provided for question parsing.")
        logger.warning("Empty text provided for question parsing")
        return {
            "marks_per_question": [],
            "total_marks": 0,
            "questions_without_marks": 0,
            "question_details": {}
        }

    patterns = [
        re.compile(
            r"(?:^|\n)\s*(?:Question\s+)?(\d+)[.:]\s*"
            r"((?:(?!\n\s*(?:Question\s+\d+[.:]|\d+[.:])).)*)",
            re.DOTALL | re.IGNORECASE
        ),
        re.compile(
            r"(?:^|\n)\s*(?:Q\.?\s*)?(\d+)[.:]\s*"
            r"((?:(?!\n\s*(?:Q\.?\s*\d+[.:]|\d+[.:])).)*)",
            re.DOTALL | re.IGNORECASE
        )
    ]
    
    sub_q_pattern = re.compile(
        r"(?:^|\n)\s*(?:(\d+)\s*\([a-z]\)|\d+\.\d+|[a-z]\))[.:]?\s*"
        r"([^\n]*(?:\n(?!\s*(?:\d+[.:]|[a-z]\)|(?:\d+\s*\([a-z]\)|\d+\.\d+)))[^\n]*)*)",
        re.MULTILINE | re.IGNORECASE
    )
    
    mark_patterns = [
        r'\((\d+)\s*(?:marks?|points?)\)',  # (5 marks)
    ]
    
    compiled_mark_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in mark_patterns]
    
    question_marks_dict = {
        "marks_per_question": [],
        "total_marks": 0,
        "questions_without_marks": 0,
        "question_details": {}
    }
    
    questions = {}
    for pattern in patterns:
        matches = list(pattern.finditer(text))
        if matches:
            for match in matches:
                try:
                    q_num = int(match.group(1))
                    q_text = match.group(2).strip()
                    
                    question_marks = 0
                    found_marks = False
                    mark_position = -1
                    
                    for mark_pattern in compiled_mark_patterns:
                        for mark_match in mark_pattern.finditer(q_text):
                            try:
                                marks = int(mark_match.group(1))
                                if mark_match.start() > mark_position:
                                    question_marks = marks
                                    mark_position = mark_match.start()
                                    found_marks = True
                            except (IndexError, ValueError):
                                logger.debug(f"Invalid mark match in question {q_num}: {mark_match.group()}")
                                continue
                    
                    sub_matches = sub_q_pattern.finditer(q_text)
                    sub_questions = []
                    sub_marks_sum = 0
                    
                    for sub_match in sub_matches:
                        sub_q_id = sub_match.group(1) or sub_match.group(0).strip()
                        sub_q_text = sub_match.group(2).strip()
                        sub_mark = 0
                        sub_mark_found = False
                        sub_mark_position = -1
                        
                        for mark_pattern in compiled_mark_patterns:
                            for mark_match in mark_pattern.finditer(sub_q_text):
                                try:
                                    marks = int(mark_match.group(1))
                                    if mark_match.start() > sub_mark_position:
                                        sub_mark = marks
                                        sub_mark_position = mark_match.start()
                                        sub_mark_found = True
                                except (IndexError, ValueError):
                                    logger.debug(f"Invalid mark match in sub-question {q_num}{sub_q_id}: {mark_match.group()}")
                                    continue
                        
                        if sub_mark:
                            sub_marks_sum += sub_mark
                        sub_questions.append({
                            "id": sub_q_id,
                            "text": sub_q_text,
                            "marks": sub_mark,
                            "has_marks": sub_mark_found
                        })
                    
                    if not found_marks and sub_questions:
                        question_marks = sub_marks_sum if sub_marks_sum > 0 else 0
                        found_marks = sub_marks_sum > 0
                    
                    questions[q_num] = {
                        "question": q_text,
                        "sub_questions": sub_questions,
                        "total_marks": question_marks,
                        "correct_answer": "",
                        "marking_scheme": "",
                        "text": q_text,
                        "marks": question_marks,
                        "has_marks": found_marks
                    }
                    logger.info(f"Parsed question {q_num} with {len(sub_questions)} sub-questions")
                except (ValueError, IndexError) as e:
                    logger.error(f"Error processing question match: {e}")
                    continue
            if questions:
                break
    
    if not questions:
        lines = text.split('\n')
        current_q_num = None
        current_text = []
        current_sub_questions = []
        current_marks = 0
        current_has_marks = False
        
        for line in lines:
            q_start_match = re.search(r'^\s*(?:Question\s+)?(\d+)[.:]', line)
            sub_q_match = sub_q_pattern.match(line)
            
            if q_start_match:
                if current_q_num is not None:
                    questions[current_q_num] = {
                        "question": '\n'.join(current_text).strip(),
                        "sub_questions": current_sub_questions,
                        "total_marks": current_marks,
                        "correct_answer": "",
                        "marking_scheme": "",
                        "text": '\n'.join(current_text).strip(),
                        "marks": current_marks,
                        "has_marks": current_has_marks
                    }
                    logger.info(f"Saved question {current_q_num} with {len(current_sub_questions)} sub-questions")
                current_q_num = int(q_start_match.group(1))
                current_text = [re.sub(r'^\s*(?:Question\s+)?\d+[.:]', '', line).strip()]
                current_sub_questions = []
                current_marks = 0
                current_has_marks = False
            elif sub_q_match and current_q_num is not None:
                sub_q_id = sub_q_match.group(1) or sub_q_match.group(0).strip()
                sub_q_text = sub_q_match.group(2).strip()
                sub_mark = 0
                sub_mark_found = False
                sub_mark_position = -1
                
                for mark_pattern in compiled_mark_patterns:
                    for mark_match in mark_pattern.finditer(sub_q_text):
                        try:
                            marks = int(mark_match.group(1))
                            if mark_match.start() > sub_mark_position:
                                sub_mark = marks
                                sub_mark_position = mark_match.start()
                                sub_mark_found = True
                        except (IndexError, ValueError):
                            logger.debug(f"Invalid mark match in sub-question {current_q_num}{sub_q_id}: {mark_match.group()}")
                            continue
                
                current_sub_questions.append({
                    "id": sub_q_id,
                    "text": sub_q_text,
                    "marks": sub_mark,
                    "has_marks": sub_mark_found
                })
                if sub_mark:
                    current_marks += sub_mark
                    current_has_marks = True
                logger.debug(f"Added sub-question {sub_q_id} for question {current_q_num}")
            elif current_q_num is not None:
                current_text.append(line.strip())
        
        if current_q_num is not None:
            questions[current_q_num] = {
                "question": '\n'.join(current_text).strip(),
                "sub_questions": current_sub_questions,
                "total_marks": current_marks,
                "correct_answer": "",
                "marking_scheme": "",
                "text": '\n'.join(current_text).strip(),
                "marks": current_marks,
                "has_marks": current_has_marks
            }
            logger.info(f"Saved final question {current_q_num} with {len(current_sub_questions)} sub-questions")
    
    question_marks_dict["question_details"] = questions
    question_marks_dict["total_marks"] = sum(details["marks"] for details in questions.values())
    question_marks_dict["questions_without_marks"] = sum(1 for details in questions.values() if not details["has_marks"])
    
    if question_marks_dict["questions_without_marks"] == len(questions) and questions:
        max_marks = st.session_state.get("final_max_paper_marks")
        max_questions = st.session_state.get("final_max_questions_to_attempt", len(questions))
        
        if max_marks is not None and max_questions is not None and max_questions > 0:
            marks_per_question = max_marks // max_questions
            question_marks_dict["total_marks"] = 0
            question_marks_dict["questions_without_marks"] = 0
            
            for q_num, details in questions.items():
                details["marks"] = marks_per_question
                details["total_marks"] = marks_per_question
                details["has_marks"] = True
                question_marks_dict["total_marks"] += marks_per_question
                for sub_q in details["sub_questions"]:
                    if not sub_q["has_marks"]:
                        sub_q["marks"] = 0
            logger.info(f"No marks detected; distributed {max_marks} marks evenly across {max_questions} questions: {marks_per_question} marks each")
        else:
            logger.warning("Cannot distribute marks: max_marks or max_questions not set or invalid")
    
    max_q_num = max(questions.keys(), default=0)
    question_marks_dict["marks_per_question"] = [0] * max_q_num
    for q_num, details in questions.items():
        if q_num <= max_q_num:
            question_marks_dict["marks_per_question"][q_num - 1] = details["marks"]
    
    logger.info(f"Parsed {len(questions)} questions with sub-questions and marks")
    try:
        with open("question_marks_dict.json", "w", encoding="utf-8") as f:
            json.dump(question_marks_dict, f, indent=2)
        logger.info("Saved question_marks_dict to question_marks_dict.json")
    except Exception as e:
        logger.error(f"Failed to save question_marks_dict.json: {str(e)}")
    
    print("question_marks_dict:")
    print(json.dumps(question_marks_dict, indent=2))
    return question_marks_dict

def parse_answer_key(text: str) -> dict:
    pattern = re.compile(
        r"(?:Question\s+)?(?P<q_num>\d+)[.:]\s*"
        r"(?P<question>.*?)" 
        r"\s*([-*#]+\s*)?\**\s*Answer\s*\**:\s*"
        r"(?P<correct_answer>.*?)" 
        r"\s*([-*#]+\s*)?\**\s*(?:Marking Scheme|Mark Scheme|Rubric)\s*\**:\s*"
        r"(?P<marking_scheme>.*?)" 
        r"(?=\s*\n\s*[-*#]*\s*\**\s*(?:Question\s+\d+[.:]|\d+[.:])|\Z)",
        re.DOTALL | re.IGNORECASE
    )
    answer_key_dict = {}
    for match in pattern.finditer(text):
        try:
            q_num = int(match.group("q_num"))
            answer_key_dict[q_num] = {
                "question": match.group("question").strip(),
                "correct_answer": match.group("correct_answer").strip(),
                "marking_scheme": match.group("marking_scheme").strip()
            }
        except (ValueError, KeyError):
            continue
    st.session_state["mark_scheme_questions"] = {q_num: details["question"] 
                                                for q_num, details in answer_key_dict.items()}
    return answer_key_dict

def create_marks_table(question_details):
    data = []
    for q_num, details in sorted(question_details.items()):
        question_text = details.get("text", "")
        marks = details.get("marks", 0)
        data.append({
            "Question Number": f"Q{q_num}",
            "Question Text": question_text,
            "Marks": marks
        })
        sub_questions = details.get("sub_questions", [])
        for sub_q in sub_questions:
            sub_q_text = sub_q.get("text", "")
            sub_q_marks = sub_q.get("marks", 0)
            data.append({
                "Question Number": f"Q{q_num}.{sub_q['id']}",
                "Question Text": sub_q_text,
                "Marks": sub_q_marks
            })
    return pd.DataFrame(data)

def apply_marks_updates(edited_df, question_marks_dict):
    try:
        if not isinstance(edited_df, pd.DataFrame) or edited_df.empty:
            raise ValueError("Edited DataFrame is empty or invalid")
        
        edited_df["Marks"] = pd.to_numeric(edited_df["Marks"], errors='coerce').fillna(0).astype(int)
        if (edited_df["Marks"] < 0).any():
            raise ValueError("Marks cannot be negative")

        updated_details = question_marks_dict["question_details"].copy()
        total_marks = 0
        questions_without_marks = 0
        
        for _, row in edited_df.iterrows():
            q_id = row["Question Number"]
            marks = int(row["Marks"])
            
            if q_id.startswith("Q") and "." not in q_id[1:]:
                q_num = int(q_id.replace("Q", ""))
                if q_num in updated_details:
                    updated_details[q_num]["marks"] = marks
                    updated_details[q_num]["total_marks"] = marks
                    updated_details[q_num]["has_marks"] = marks > 0
                    total_marks += marks
                    if marks == 0:
                        questions_without_marks += 1
            elif q_id.startswith("Q") and "." in q_id[1:]:
                q_num, sub_q_id = q_id.replace("Q", "").split(".", 1)
                q_num = int(q_num)
                if q_num in updated_details:
                    for sub_q in updated_details[q_num]["sub_questions"]:
                        if sub_q["id"] == sub_q_id:
                            sub_q["marks"] = marks
                            sub_q["has_marks"] = marks > 0
                            break
        
        for q_num, details in updated_details.items():
            sub_marks_sum = sum(sub_q["marks"] for sub_q in details["sub_questions"])
            if not details["has_marks"] and sub_marks_sum > 0:
                details["marks"] = sub_marks_sum
                details["total_marks"] = sub_marks_sum
                details["has_marks"] = True
                total_marks += sub_marks_sum
                if sub_marks_sum == 0:
                    questions_without_marks += 1
        
        max_q_num = max(updated_details.keys(), default=0)
        marks_per_question = [0] * max_q_num
        for q_num, details in updated_details.items():
            if q_num <= max_q_num:
                marks_per_question[q_num - 1] = details["marks"]
        
        updated_result = {
            "marks_per_question": marks_per_question,
            "total_marks": total_marks,
            "questions_without_marks": questions_without_marks,
            "question_details": updated_details
        }
        
        try:
            with open("question_marks_dict.json", "w", encoding="utf-8") as f:
                json.dump(updated_result, f, indent=2)
            logger.info("Saved updated question_marks_dict to question_marks_dict.json")
        except OSError as e:
            logger.error(f"Failed to save question_marks_dict.json: {str(e)}")
            st.error(f"Failed to save question_marks_dict.json: {str(e)}")
        
        return updated_result
    
    except Exception as e:
        logger.error(f"Error in apply_marks_updates: {str(e)}")
        raise ValueError(f"Failed to apply marks updates: {str(e)}")

def process_generate_mark_scheme_pdf(text):
    logger.info("Starting mark scheme processing")
    question_marks_dict = parse_questions_and_marks(text)
    logger.info(f"Extracted {len(question_marks_dict['question_details'])} questions, total marks: {question_marks_dict['total_marks']}")
    
    marks_table = create_marks_table(question_marks_dict["question_details"])
    logger.info("Generated marks table for editing")
    
    logger.info(f"Total Marks: {question_marks_dict['total_marks']}")
    logger.info(f"Questions without marks: {question_marks_dict['questions_without_marks']}")
    
    return marks_table, question_marks_dict

def process_uploaded_file(uploaded_file, mark_scheme_option):
    if uploaded_file is not None and not st.session_state["uploaded_file_processed"]:
        logger.info(f"Processing uploaded file: {uploaded_file.name}")
        with st.spinner(f"Processing '{uploaded_file.name}'..."):
            pdf_bytes = uploaded_file.getvalue()
            text = extract_text_from_pdf(pdf_bytes)
            if text:
                if mark_scheme_option == "Upload full mark scheme":
                    answer_key_dict = parse_answer_key(text)
                    if answer_key_dict:
                        logger.info(f"Extracted {len(answer_key_dict)} questions from mark scheme")
                        logger.debug(f"Mark scheme content: {json.dumps(answer_key_dict, indent=2)}")
                        expected_questions = st.session_state.get("expected_question_count", len(answer_key_dict))
                        if len(answer_key_dict) != expected_questions:
                            st.warning(f"Mismatch detected: Extracted {len(answer_key_dict)} questions, expected {expected_questions}.")
                        st.session_state["answer_keys"] = {uploaded_file.name: answer_key_dict}
                        st.session_state["step"] = "review_full"
                        st.session_state["uploaded_file_name"] = uploaded_file.name
                        st.session_state["uploaded_file_processed"] = True
                        marks_table, question_marks_dict = process_generate_mark_scheme_pdf(text)
                        st.session_state["question_marks_dict"] = question_marks_dict
                        st.session_state["marks_table"] = marks_table
                        st.success(f"Processed Mark Scheme '{uploaded_file.name}': {len(answer_key_dict)} questions extracted.")
                        st.rerun()
                    else:
                        st.error("Failed to extract mark scheme. Please ensure the PDF contains questions, answers, and marking schemes in the correct format.")
                        logger.error("Failed to extract mark scheme from uploaded file")
                else:
                    question_marks_dict = parse_questions_and_marks(text)
                    if question_marks_dict["question_details"]:
                        logger.info(f"Extracted {len(question_marks_dict['question_details'])} questions for mark scheme generation")
                        st.session_state["question_marks_dict"] = question_marks_dict
                        st.session_state["step"] = "review_edit"
                        st.session_state["uploaded_file_name"] = uploaded_file.name
                        st.session_state["uploaded_file_processed"] = True
                        marks_table, question_marks_dict = process_generate_mark_scheme_pdf(text)
                        st.session_state["question_marks_dict"] = question_marks_dict
                        st.session_state["marks_table"] = marks_table
                        st.success(f"Extracted {len(question_marks_dict['question_details'])} questions from '{uploaded_file.name}' for mark scheme generation.")
                        st.rerun()
                    else:
                        st.error("Failed to extract questions. Please ensure the PDF contains questions in the correct format (e.g., '1.', 'Question 1:').")
                        logger.error("Failed to extract questions from uploaded file")
            else:
                st.error("Failed to extract text from the uploaded PDF. Please check the file.")
                logger.error(f"No text extracted from {uploaded_file.name}")

def generate_mark_scheme(question_details: Dict, client, max_retries: int = 3) -> str:
    try:
        if not question_details:
            raise ValueError("No question details provided for mark scheme generation")
        
        with open("prompt.json", "r") as file:
            prompt_data = json.load(file)
            MARK_SCHEME_PROMPT_TEMPLATE = prompt_data.get("MARK_SCHEME_PROMPT", "")

        if not MARK_SCHEME_PROMPT_TEMPLATE:
            raise ValueError("MARK_SCHEME_PROMPT not found in prompt.json")

        questions_text = ""
        for q_num, q_data in sorted(question_details.items(), key=lambda x: int(x[0])):
            questions_text += f"Question {q_num}: {q_data.get('question', '')} (Marks: {q_data.get('marks', 0)})\n"
            if 'sub_questions' in q_data and q_data['sub_questions']:
                for sub_q in q_data['sub_questions']:
                    questions_text += f"  {q_num}.{sub_q.get('id')} {sub_q.get('text', '')} (Marks: {sub_q.get('marks', 0)})\n"
        
        MARK_SCHEME_PROMPT = MARK_SCHEME_PROMPT_TEMPLATE.format(questions_text=questions_text)
        
        attempt = 0
        while attempt < max_retries:
            try:
                logger.info(f"Attempting to generate mark scheme (Attempt {attempt + 1}/{max_retries})")
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role": "system", "content": "You are an expert in creating structured mark schemes for educational assessments."},
                        {"role": "user", "content": MARK_SCHEME_PROMPT}
                    ],
                    temperature=1,
                    max_tokens=8000
                )
                
                response_text = response.choices[0].message.content.strip()
                if not response_text:
                    raise ValueError("Empty response from Groq API")
                
                print("Raw Model Response:")
                print(response_text)
                print("--- End of Raw Model Response ---")
                
                logger.info("Successfully generated raw mark scheme response")
                return response_text
                
            except Exception as e:
                attempt += 1
                logger.error(f"Error generating mark scheme on attempt {attempt}: {str(e)}")
                if attempt == max_retries:
                    logger.error("Max retries reached. Failed to generate mark scheme.")
                    default_response = "\n".join(
                        f"**Question {q_num}**\n**Answer**: Not generated\n**Marking Scheme**: Not generated\n"
                        for q_num in sorted(question_details.keys())
                    )
                    return default_response
                time.sleep(1)
        
        return ""
    
    except Exception as e:
        logger.error(f"Error in generate_mark_scheme: {str(e)}")
        raise ValueError(f"Failed to generate mark scheme: {str(e)}")

def parse_mark_scheme() -> dict:
    """
    Parse marking scheme from the provided text format.
    Extracts: question, answer, marking_scheme (with notes included) for each question.
    """
    import re
    import json

    # Read the input file
    try:
        with open('final_mark_scheme.txt', 'r', encoding='utf-8') as f:
            input_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file 'final_mark_scheme.txt' not found.")

    # Initialize the result dictionary
    mark_scheme = {"questions": []}
    
    # Split input into individual question blocks using **Question X:** pattern
    question_pattern = r'\*\*Question (\d+):\*\*(.*?)(?=\*\*Question \d+:|\Z)'
    question_blocks = re.findall(question_pattern, input_text, re.DOTALL)
    
    for question_num, block_content in question_blocks:
        # Initialize components
        question_text = None
        answer_text = None
        marking_text = None
        
        # Clean up the block content
        block_content = block_content.strip()
        
        # Extract question text (everything before "Answer:")
        question_match = re.search(r'^(.*?)(?=Answer:)', block_content, re.DOTALL)
        if question_match:
            question_text = question_match.group(1).strip()
        
        # Extract answer text (between "Answer:" and "Marking Scheme:")
        answer_match = re.search(r'Answer:\s*(.*?)(?=Marking Scheme:)', block_content, re.DOTALL)
        if answer_match:
            answer_text = answer_match.group(1).strip()
        
        # Extract marking scheme text (between "Marking Scheme:" and "Notes:")
        marking_match = re.search(r'Marking Scheme:\s*(.*?)(?=Notes:|\Z)', block_content, re.DOTALL)
        if marking_match:
            marking_text = marking_match.group(1).strip()
        
        # Extract notes text (after "Notes:") if present
        notes_match = re.search(r'Notes:\s*(.*?)$', block_content, re.DOTALL)
        notes_text = notes_match.group(1).strip() if notes_match else ""
        
        # Combine marking scheme and notes
        combined_marking = marking_text if marking_text else ""
        if notes_text:
            combined_marking = f"{combined_marking}\nNotes: {notes_text}" if marking_text else f"Notes: {notes_text}"
        
        # Only append if question text is found (minimum requirement)
        if question_text:
            question_data = {
                "question_number": int(question_num),
                "question": question_text,
                "answer": answer_text if answer_text else "",
                "marking_scheme": combined_marking
            }
            mark_scheme["questions"].append(question_data)
    
    # Sort questions by question_number to ensure correct order
    mark_scheme["questions"].sort(key=lambda x: x["question_number"])
    
    # Save to JSON file
    output_filename = "final_mark_scheme.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(mark_scheme, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully parsed {len(mark_scheme['questions'])} questions")
    print(f"Output saved to: {output_filename}")
    
    return mark_scheme

def extract_json(raw_content: str) -> str:
    logger.debug(f"Raw LLM response: {raw_content[:1000]}...")
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL | re.IGNORECASE)
    if json_match:
        logger.info("Found JSON within markdown code blocks")
        json_str = json_match.group(1).strip()
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in markdown code block: {str(e)}")
            pass

    json_match = re.search(r'(\{.*?\})', raw_content, re.DOTALL)
    if json_match:
        logger.info("Found standalone JSON object")
        json_str = json_match.group(1).strip()
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Invalid standalone JSON: {str(e)}")
            pass

    cleaned_content = raw_content.strip()
    if cleaned_content.startswith('{') and cleaned_content.endswith('}'):
        logger.info("Raw content resembles a JSON object")
        try:
            json.loads(cleaned_content)
            return cleaned_content
        except json.JSONDecodeError as e:
            logger.error(f"Invalid raw JSON content: {str(e)}")
            pass

    logger.warning(f"Could not extract valid JSON from response: {raw_content[:500]}...")
    return "{}"

def analyze_question_topics(questions: Dict) -> Dict:
    logger = logging.getLogger(__name__)
    default_response = {
        "topics": ["Unknown Topic"],
        "question_mapping": {str(q_num): "Unknown Topic" for q_num in questions.keys()}
    }
    try:
        # Load prompt from prompt.json
        try:
            with open("prompt.json", "r", encoding="utf-8") as f:
                prompt_data = json.load(f)
                prompt_template = prompt_data["TOPIC_ANALYSIS_PROMPT"]
        except Exception as e:
            logger.error(f"Failed to load prompt.json: {str(e)}")
            raise ValueError("Could not load prompt from prompt.json")

        # Serialize questions to JSON string
        questions_json = json.dumps(questions, indent=2)
        # Format prompt with serialized questions
        prompt = prompt_template.format(questions=questions_json)
        
        client = init_groq_client_topic()
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048
        )
        raw_content = response.choices[0].message.content.strip()
        logger.info(f"Raw LLM Response length: {len(raw_content)}")

        json_content = extract_json(raw_content)
        parsed_response = json.loads(json_content)
        logger.info("Parsed JSON successfully")

        if not isinstance(parsed_response, dict) or "topics" not in parsed_response or "question_mapping" not in parsed_response:
            logger.error("Validation Error: Invalid JSON structure")
            raise ValueError("LLM response does not match expected JSON format")

        parsed_response["question_mapping"] = {str(k): v for k, v in parsed_response["question_mapping"].items()}
        
        logger.info("Successfully analyzed question topics with LLM")
        
        print(json.dumps(parsed_response, indent=2))
        
        try:
            with open("topic_mapping.json", "w", encoding="utf-8") as f:
                json.dump(parsed_response, f, indent=2)
            logger.info("Saved topic_mapping to topic_mapping.json")
        except Exception as e:
            logger.error(f"Failed to save topic_mapping.json: {str(e)}")
        
        return parsed_response

    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        st.error(f"LLM topic analysis failed: {str(e)}. Returning default response.")
        print(json.dumps(default_response, indent=2))
        return default_response

def save_and_download() -> Optional[dict]:
    try:
        # Load parsed mark scheme directly from final_mark_scheme.json
        try:
            with open("final_mark_scheme.json", "r", encoding="utf-8") as f:
                parsed_mark_scheme = json.load(f)
            logger.info("Loaded parsed mark scheme from final_mark_scheme.json")
        except OSError as e:
            logger.error(f"Failed to load final_mark_scheme.json: {str(e)}")
            st.error(f"Failed to load final_mark_scheme.json: {str(e)}")
            return None

        if not parsed_mark_scheme.get("questions"):
            raise ValueError("No valid questions found in parsed mark scheme")
        
        st.session_state["mark_sheet"] = parsed_mark_scheme
        
        question_marks_dict = st.session_state["question_marks_dict"]
        for q in parsed_mark_scheme["questions"]:
            q_num = str(q["question_number"])
            if q_num in question_marks_dict["question_details"]:
                question_marks_dict["question_details"][q_num]["correct_answer"] = q["correct_answer"]
                question_marks_dict["question_details"][q_num]["marking_scheme"] = q["marking_scheme"]
        st.session_state["mark_scheme_questions"] = question_marks_dict["question_details"]
        
        try:
            with open("question_marks_dict.json", "w", encoding="utf-8") as f:
                json.dump(question_marks_dict, f, indent=2)
            logger.info("Saved updated question_marks_dict to question_marks_dict.json")
        except OSError as e:
            logger.error(f"Failed to save question_marks_dict.json: {str(e)}")
            st.error(f"Failed to save question_marks_dict.json: {str(e)}")
        
        try:
            with open("mark_sheet.json", "w", encoding="utf-8") as f:
                json.dump(parsed_mark_scheme, f, indent=2)
            logger.info("Saved mark_sheet to mark_sheet.json")
        except OSError as e:
            logger.error(f"Failed to save mark_sheet.json: {str(e)}")
            st.error(f"Failed to save mark_sheet.json: {str(e)}")
        
        topic_mapping = analyze_question_topics(st.session_state["mark_scheme_questions"])
        st.session_state["topic_mapping"] = topic_mapping
        st.session_state["all_topics"] = topic_mapping.get("topics", [])
        logger.info(f"Topic analysis completed: {topic_mapping}")
        
        try:
            with open("topic_mapping.json", "w", encoding="utf-8") as f:
                json.dump(topic_mapping, f, indent=2)
            logger.info("Saved topic_mapping to topic_mapping.json")
        except OSError as e:
            logger.error(f"Failed to save topic_mapping.json: {str(e)}")
            st.error(f"Failed to save topic_mapping.json: {str(e)}")
        
        file_name = st.session_state["uploaded_file_name"]
        answer_keys = {
            str(q["question_number"]): {
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "marking_scheme": q["marking_scheme"]
            } for q in parsed_mark_scheme["questions"]
        }
        st.session_state["answer_keys"] = {file_name: answer_keys}
        
        st.session_state["step"] = "proceed"
        st.session_state["uploaded_file_processed"] = True
        
        return parsed_mark_scheme
    
    except ValueError as e:
        st.error(str(e))
        logger.error(f"Validation error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing mark scheme: {str(e)}")
        logger.error(f"Error processing mark scheme: {str(e)}")
        return None

def parse_student_answers(text: str, pdf_bytes: Optional[bytes] = None, filename: str = "unknown") -> Dict[int, Dict]:
    """
    Parse student answers from text and PDF, map images to questions, and save to JSON.
    
    Args:
        text (str): Extracted text from the PDF.
        pdf_bytes (Optional[bytes]): Raw PDF bytes for image extraction.
        filename (str): Name of the student file for JSON naming.
    
    Returns:
        Dict[int, Dict]: Parsed student answers with question details and images.
    """
    student_answers = {}
    unmapped_images = []
    
    # Clean up the text
    text = re.sub(r'\n\s*\n+', '\n', text.strip())
    
    # More robust question pattern - matches question numbers at start of line or after newline
    question_pattern = re.compile(r'(?:^|\n)\s*(\d+)\.?\s+(.+?)(?=(?:^|\n)\s*\d+\.?\s+|\Z)', re.MULTILINE | re.DOTALL)
    
    # Find all question matches
    question_matches = question_pattern.findall(text)
    
    if not question_matches:
        # Fallback: try splitting by numbered lines if the regex doesn't work
        lines = text.split('\n')
        current_question = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a number followed by period or colon
            match = re.match(r'^(\d+)[\.:]\s*(.*)$', line)
            if match:
                # Save previous question if exists
                if current_question is not None:
                    content = '\n'.join(current_content).strip()
                    if content:
                        question_matches.append((str(current_question), content))
                
                # Start new question
                current_question = int(match.group(1))
                current_content = [match.group(2)] if match.group(2) else []
            else:
                # Add to current question content
                if current_question is not None:
                    current_content.append(line)
        
        # Don't forget the last question
        if current_question is not None:
            content = '\n'.join(current_content).strip()
            if content:
                question_matches.append((str(current_question), content))
    
    # Process each question
    for q_num_str, content in question_matches:
        try:
            q_num = int(q_num_str)
        except ValueError:
            logger.warning(f"Skipping invalid question number in {filename}: '{q_num_str}'")
            print(f"  - Warning: Skipping invalid question number in {filename}: '{q_num_str}'")
            continue
        
        content = content.strip()
        
        # Look for student answer pattern - more flexible matching
        answer_patterns = [
            r'Student\'s Answer:\s*(.*?)(?=\n\d+\.|\Z)',
            r'Answer:\s*(.*?)(?=\n\d+\.|\Z)',
            r'Ans:\s*(.*?)(?=\n\d+\.|\Z)',
            r'Response:\s*(.*?)(?=\n\d+\.|\Z)'
        ]
        
        question_text = ""
        answer_text = ""
        
        # Try to find student answer section
        answer_found = False
        for pattern in answer_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                # Split content at the answer marker
                answer_start = match.start()
                question_text = content[:answer_start].strip()
                answer_text = match.group(1).strip()
                answer_found = True
                break
        
        if not answer_found:
            # If no explicit answer marker found, treat entire content as question
            # Look for common patterns that might indicate where question ends
            question_end_patterns = [
                r'(.+?)(?:\n\s*[A-Z][a-z].*?\n)',  # Question followed by answer starting with capital
                r'(.+?)(?:\n\s*-\s*)',  # Question followed by bullet points
                r'(.+?)(?:\n\s*\w+.*?:)',  # Question followed by any word with colon
            ]
            
            for pattern in question_end_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    question_text = match.group(1).strip()
                    answer_text = content[len(question_text):].strip()
                    break
            
            # If still no split found, check if content has multiple sentences
            if not question_text and not answer_text:
                sentences = re.split(r'[.!?]+\s*', content)
                if len(sentences) > 1:
                    # Assume first sentence(s) are question, rest is answer
                    question_text = sentences[0].strip() + ('.' if not sentences[0].endswith(('.', '!', '?')) else '')
                    answer_text = ' '.join(sentences[1:]).strip()
                else:
                    # Single sentence - treat as question with no answer
                    question_text = content
                    answer_text = "No answer provided"
        
        # Clean up question text
        if not question_text.strip():
            question_text = f"Question {q_num} text missing"
            logger.warning(f"Empty question text for Q{q_num} in {filename}")
            print(f"  - Warning: Empty question text for Q{q_num} in {filename}")
        
        # Clean up answer text
        if not answer_text.strip():
            answer_text = "No answer provided"
            logger.warning(f"Empty answer for Q{q_num} in {filename}")
            print(f"  - Warning: Empty answer for Q{q_num} in {filename}")
        
        # Count potential image references
        image_count = len(re.findall(r'\b(Image|Diagram|Table|Figure|Chart|Graph)\b', answer_text, re.IGNORECASE))
        
        student_answers[q_num] = {
            "question": question_text,
            "student_answer": answer_text,
            "image_count": image_count,
            "images": []
        }
    
    # Handle image extraction if PDF bytes provided and images available
    if pdf_bytes and student_answers:
        try:
            # Import fitz only when needed for image processing
            import fitz
            
            # Extract text blocks for positioning (if extract_images_from_page function exists)
            text_blocks = []
            question_positions = {}
            
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                # Extract text blocks for positioning
                for page_num, page in enumerate(doc):
                    blocks = page.get_text("dict")["blocks"]
                    for block in blocks:
                        if block["type"] == 0:  # Text block
                            block_text = ""
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    block_text += span["text"]
                            bbox = block["bbox"]
                            text_blocks.append({
                                "text": block_text,
                                "page": page_num,
                                "y0": bbox[1],
                                "y1": bbox[3],
                                "x0": bbox[0],
                                "x1": bbox[2]
                            })
                
                # Map questions to positions
                for q_num in sorted(student_answers.keys()):
                    q_text = f"{q_num}."
                    q_blocks = []
                    
                    # Find blocks containing question number
                    for block in text_blocks:
                        if q_text in block["text"]:
                            q_blocks.append(block)
                    
                    # Also look for answer text chunks
                    answer_text = student_answers[q_num]["student_answer"]
                    if answer_text and answer_text != "No answer provided":
                        # Take first 30 characters of answer for matching
                        answer_chunk = answer_text[:min(30, len(answer_text))]
                        if len(answer_chunk) > 10:
                            for block in text_blocks:
                                if answer_chunk in block["text"]:
                                    q_blocks.append(block)
                    
                    if q_blocks:
                        question_positions[q_num] = {
                            "page_min": min(b["page"] for b in q_blocks),
                            "page_max": max(b["page"] for b in q_blocks),
                            "y0": min(b["y0"] for b in q_blocks),
                            "y1": max(b["y1"] for b in q_blocks)
                        }
                
                # Extract and map images (if extract_images_from_page function is available)
                try:
                    all_images = []
                    for page_num, page in enumerate(doc):
                        # This assumes extract_images_from_page function exists
                        page_images = extract_images_from_page(page, page_num)
                        all_images.extend(page_images)
                    
                    # Map images to questions
                    sorted_questions = sorted(
                        [(q, pos) for q, pos in question_positions.items()],
                        key=lambda x: (x[1]["page_min"], x[1]["y0"])
                    )
                    
                    for img in all_images:
                        img_page = img["page_num"]
                        img_y0 = img["y_position"] or 0
                        assigned_q = None
                        
                        # Try to assign image to question
                        for q_num, q_pos in sorted_questions:
                            if q_pos["page_max"] == img_page and q_pos["y1"] <= img_y0:
                                assigned_q = q_num
                        
                        # Fallback assignment strategies
                        if assigned_q is None and img_page > 0:
                            # Look for last question on previous page
                            last_q_prev_page = None
                            for q_num, q_pos in sorted_questions:
                                if q_pos["page_max"] == img_page - 1:
                                    last_q_prev_page = q_num
                            if last_q_prev_page is not None:
                                assigned_q = last_q_prev_page
                        
                        if assigned_q is None:
                            # Assign to first question on same page
                            same_page_questions = [
                                q_num for q_num, pos in question_positions.items()
                                if pos["page_min"] <= img_page <= pos["page_max"]
                            ]
                            if same_page_questions:
                                assigned_q = min(same_page_questions)
                        
                        # Add image to question if assigned and valid
                        if assigned_q is not None and validate_image_bytes(img["bytes"]):
                            student_answers[assigned_q]["images"].append({
                                "bytes": base64.b64encode(img["bytes"]).decode('utf-8'),
                                "format": img["format"]
                            })
                            student_answers[assigned_q]["image_count"] = len(student_answers[assigned_q]["images"])
                            logger.info(f"Mapped image at y={img_y0} on page {img_page} to Question {assigned_q} in {filename}")
                            print(f"  - Mapped image at y={img_y0} on page {img_page} to Question {assigned_q} in {filename}")
                        else:
                            unmapped_images.append({
                                "bytes": base64.b64encode(img["bytes"]).decode('utf-8') if img.get("bytes") else "",
                                "page": img_page,
                                "y0": img_y0
                            })
                            logger.warning(f"Unmapped image at y={img_y0} on page {img_page} in {filename}")
                            print(f"  - Warning: Unmapped image at y={img_y0} on page {img_page} in {filename}")
                
                except NameError:
                    # extract_images_from_page or validate_image_bytes functions not available
                    logger.info(f"Image extraction functions not available for {filename}")
                    print(f"  - Image extraction functions not available for {filename}")
                except Exception as e:
                    logger.error(f"Error in image extraction for {filename}: {str(e)}")
                    print(f"  - Error in image extraction for {filename}: {str(e)}")
        
        except ImportError:
            logger.warning(f"PyMuPDF not available for image processing in {filename}")
            print(f"  - PyMuPDF not available for image processing in {filename}")
        except Exception as e:
            logger.error(f"Error in image mapping for {filename}: {str(e)}")
            print(f"  - Error in image mapping for {filename}: {str(e)}")
    
    # Log unmapped images
    if unmapped_images:
        logger.info(f"{len(unmapped_images)} unmapped images stored for review in {filename}")
        print(f"  - {len(unmapped_images)} unmapped images stored for review in {filename}")
    
    # Warn if no questions found
    if not student_answers:
        logger.warning(f"No valid question-answer pairs extracted from the text in {filename}")
        print(f"  - Warning: No valid question-answer pairs extracted from the text in {filename}")
    
    # Save student answers to JSON file
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_')).rstrip()
    json_filename = f"student_answers_{safe_filename}.json"
    
    try:
        serializable_answers = {}
        for q_num, data in student_answers.items():
            serializable_answers[q_num] = {
                "question": data["question"],
                "student_answer": data["student_answer"],
                "image_count": data["image_count"],
                "images": [
                    {"bytes": img["bytes"], "format": img["format"]}
                    for img in data["images"]
                ]
            }
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(serializable_answers, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved student answers to {json_filename}")
        print(f"  - Successfully saved student answers to {json_filename}")
        
    except Exception as e:
        logger.error(f"Failed to save student answers to {json_filename}: {str(e)}")
        print(f"  - Error: Failed to save student answers to {json_filename}: {str(e)}")
    
    return student_answers

def extract_images_from_page(page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
    images = []
    try:
        img_list = page.get_images(full=True)
        for img_index, img in enumerate(img_list):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            if not base_image:
                continue
            image_bytes = base_image["image"]
            image_ext = base_image.get("ext", "png").lower()
            image_rects = page.get_image_rects(xref)
            image_rect = image_rects[0] if image_rects else None
            if not image_bytes:
                continue
            try:
                with Image.open(BytesIO(image_bytes)) as img:
                    image_format = img.format.lower() if img.format else image_ext
            except Exception:
                image_format = image_ext
            image_info = {
                "xref": xref,
                "bytes": image_bytes,
                "format": image_format,
                "width": base_image.get("width", 0),
                "height": base_image.get("height", 0),
                "y_position": image_rect.y0 if image_rect else None,
                "page_num": page_num,
                "img_index": img_index,
                "bbox": {
                    "x0": image_rect.x0 if image_rect else None,
                    "y0": image_rect.y0 if image_rect else None,
                    "x1": image_rect.x1 if image_rect else None,
                    "y1": image_rect.y1 if image_rect else None,
                }
            }
            images.append(image_info)
        images.sort(key=lambda x: (x["y_position"] if x["y_position"] is not None else float("inf"), x["img_index"]))
    except Exception as e:
        logger.error(f"Error processing images on page {page_num}: {str(e)}")
    return images

def validate_image_bytes(image_bytes: bytes) -> bool:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image bytes: {str(e)}")
        return False

def merge_json_files(mark_scheme_file: str, student_answers_file: str, question_marks_file: str, output_file: str) -> Dict:
    """
    Merges mark scheme, student answers, and question marks into a single JSON file.
    
    Args:
        mark_scheme_file (str): Path to the mark scheme JSON file.
        student_answers_file (str): Path to the student answers JSON file.
        question_marks_file (str): Path to the question marks JSON file.
        output_file (str): Path to save the merged JSON file.
    
    Returns:
        Dict: Merged JSON with paired questions, answers, and max marks.
    """
    try:
        if not os.path.exists(mark_scheme_file):
            logger.error(f"Mark scheme file not found: {mark_scheme_file}")
            raise FileNotFoundError(f"Mark scheme file not found: {mark_scheme_file}")
        if not os.path.exists(student_answers_file):
            logger.error(f"Student answers file not found: {student_answers_file}")
            raise FileNotFoundError(f"Student answers file not found: {student_answers_file}")
        if not os.path.exists(question_marks_file):
            logger.error(f"Question marks file not found: {question_marks_file}")
            raise FileNotFoundError(f"Question marks file not found: {question_marks_file}")
        
        with open(mark_scheme_file, "r", encoding="utf-8") as f:
            mark_scheme_json = json.load(f)
        with open(student_answers_file, "r", encoding="utf-8") as f:
            student_answers_json = json.load(f)
        with open(question_marks_file, "r", encoding="utf-8") as f:
            question_marks_json = json.load(f)
        
        logger.info(f"Successfully loaded {mark_scheme_file}, {student_answers_file}, and {question_marks_file}")
    except Exception as e:
        logger.error(f"Error reading input files: {str(e)}")
        raise
    
    if not isinstance(mark_scheme_json, dict) or "questions" not in mark_scheme_json:
        logger.error("Invalid mark_scheme_json: Must be a dictionary with 'questions' key")
        raise ValueError("Mark scheme JSON is invalid or missing 'questions' key")
    
    if not isinstance(student_answers_json, dict):
        logger.error("Invalid student_answers_json: Must be a dictionary")
        raise ValueError("Student answers JSON is invalid or not a dictionary")
    
    if not isinstance(question_marks_json, dict) or "marks_per_question" not in question_marks_json:
        logger.error("Invalid question_marks_json: Must be a dictionary with 'marks_per_question' key")
        raise ValueError("Question marks JSON is invalid or missing 'marks_per_question' key")
    
    merged_data = {"questions": []}
    questions = mark_scheme_json.get("questions", [])
    marks_per_question = question_marks_json.get("marks_per_question", [])
    
    if not questions:
        logger.warning("No questions found in mark_scheme_json")
        return merged_data
    
    if not marks_per_question:
        logger.warning("No marks found in question_marks_json")
        return merged_data
    
    logger.info(f"Found {len(questions)} questions in mark_scheme_json")
    
    for idx, mark_scheme_entry in enumerate(questions):
        if not isinstance(mark_scheme_entry, dict) or "question_number" not in mark_scheme_entry:
            logger.warning(f"Skipping invalid mark scheme entry: {mark_scheme_entry}")
            continue
        
        question_number = str(mark_scheme_entry.get("question_number"))
        merged_entry = {
            "question_number": question_number,
            "question": mark_scheme_entry.get("question", ""),
            "correct_answer": mark_scheme_entry.get("answer", ""),
            "marking_scheme": mark_scheme_entry.get("marking_scheme", "")
        }
        
        try:
            max_marks = marks_per_question[int(question_number) - 1] if int(question_number) - 1 < len(marks_per_question) else 0
            merged_entry["max_marks"] = max_marks
        except (IndexError, ValueError):
            logger.warning(f"No max_marks found for question {question_number}, setting to 0")
            merged_entry["max_marks"] = 0
        
        student_answer_entry = student_answers_json.get(question_number, {})
        if student_answer_entry:
            logger.info(f"Found student answer for question {question_number}")
            merged_entry["student_answer"] = student_answer_entry.get("student_answer", "")
            merged_entry["image_count"] = student_answer_entry.get("image_count", 0)
            merged_entry["images"] = student_answer_entry.get("images", [])
        else:
            logger.info(f"No student answer found for question {question_number}")
            merged_entry["student_answer"] = ""
            merged_entry["image_count"] = 0
            merged_entry["images"] = []
        
        merged_data["questions"].append(merged_entry)
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=4)
        logger.info(f"Merged JSON saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving merged JSON to {output_file}: {str(e)}")
        raise
    
    logger.info(f"Merged {len(merged_data['questions'])} questions")
    return merged_data

def merge_all_student_files(student_answer_files: List[str], mark_scheme_file: str, question_marks_file: str) -> Dict[str, Dict]:
    """
    Merges each student answer file with the mark scheme and question marks, producing separate merged outputs
    in the merged_outputs directory.
    
    Args:
        student_answer_files (List[str]): List of paths to student answer JSON files.
        mark_scheme_file (str): Path to the mark scheme JSON file.
        question_marks_file (str): Path to the question marks JSON file.
    
    Returns:
        Dict[str, Dict]: Dictionary mapping student filenames to their merged JSON data.
    """
    merged_results = {}
    
    for student_file in student_answer_files:
        try:
            # Extract the original student filename from the student answer JSON file
            base_name = os.path.basename(student_file)
            # Remove the 'student_answers_' prefix and '.json' extension to get the original filename
            if base_name.startswith("student_answers_"):
                original_fname = base_name[len("student_answers_"):-5]  # Remove '.json'
            else:
                original_fname = base_name[:-5]  # Remove '.json'
            
            # Sanitize the original filename for the merged output
            safe_filename = "".join(c for c in original_fname if c.isalnum() or c in ('.', '_')).rstrip()
            output_file = os.path.join(MERGED_OUTPUT_DIR, f"merged_output_{safe_filename}.json")
            logger.info(f"Merging {student_file} into {output_file}")
            
            merged_data = merge_json_files(
                mark_scheme_file=mark_scheme_file,
                student_answers_file=student_file,
                question_marks_file=question_marks_file,
                output_file=output_file
            )
            
            merged_results[original_fname] = merged_data
            logger.info(f"Successfully merged {student_file}")
        
        except Exception as e:
            logger.error(f"Error merging {student_file}: {str(e)}")
            print(f"  - Error merging {student_file}: {str(e)}")
            continue
    
    return merged_results

def init_groq_client_evaluation() -> Groq:
    """
    Initialize a Groq client for evaluation tasks.
    
    Returns:
        Groq: Initialized Groq client.
    
    Raises:
        ValueError: If no API key is found.
        ImportError: If Groq client is not installed.
        Exception: For other initialization errors.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY", "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")
        if not api_key:
            raise ValueError("No Groq API key found.")
        client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully for evaluation.")
        return client
    except ImportError:
        logger.error("Groq client not installed.")
        raise ImportError("Groq client not installed. Install with 'pip install groq'")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        raise

def extract_json_from_response(raw_content: str) -> Dict:
    """
    Extract JSON from LLM response, handling markdown code blocks or standalone JSON.
    
    Args:
        raw_content (str): Raw response from LLM.
    
    Returns:
        Dict: Parsed JSON object, or empty dict if extraction fails.
    """
    logger.debug(f"Raw LLM response: {raw_content[:500]}...")
    
    # Try to find JSON within markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL | re.IGNORECASE)
    if json_match:
        logger.info("Found JSON within markdown code blocks")
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in markdown code block: {str(e)}")

    # Try to find standalone JSON object
    json_match = re.search(r'(\{.*?\})', raw_content, re.DOTALL)
    if json_match:
        logger.info("Found standalone JSON object")
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid standalone JSON: {str(e)}")

    # Try treating the entire content as JSON
    cleaned_content = raw_content.strip()
    if cleaned_content.startswith('{') and cleaned_content.endswith('}'):
        logger.info("Raw content resembles a JSON object")
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid raw JSON content: {str(e)}")

    logger.warning(f"Could not extract valid JSON from response: {raw_content[:500]}...")
    return {}

def evaluate_student_answers(input_data: Dict, max_retries: int = 3, client: Optional[Groq] = None, client_index: int = 0) -> Optional[Dict]:
    """
    Evaluate student answers using AI based on the provided mark scheme.

    Args:
        input_data (Dict): Dictionary containing questions and student answers
        max_retries (int): Maximum number of retries for API calls
        client (Optional[Groq]): Groq client to use for API calls
        client_index (int): Index of the client for logging purposes

    Returns:
        Optional[Dict]: Raw API responses for evaluated questions
    """
    logger = logging.getLogger(__name__)
    print(f" Starting student answer evaluation with client {client_index + 1}...")
    print("=" * 80)
    
    try:
        # Load prompt from evaluation_prompt.json
        try:
            with open("prompt.json", "r", encoding="utf-8") as f:
                prompt_data = json.load(f)
                EVALUATION_PROMPT = prompt_data["EVALUATION_PROMPT"]
        except Exception as e:
            logger.error(f"Failed to load prompt.json: {str(e)}")
            raise ValueError("Could not load prompt from evaluation_prompt.json")

        # Validate input data structure
        print(" Validating input data structure...")
        if not isinstance(input_data, dict) or "questions" not in input_data:
            logger.error("Invalid input data: Must be a dictionary with 'questions' key")
            raise ValueError("Input data is invalid or missing 'questions' key")

        questions = input_data.get("questions", [])
        if not questions:
            logger.warning("No questions found in input data")
            return {"questions": []}

        print(f" Found {len(questions)} questions to evaluate")

        if client is None:
            raise ValueError("No Groq client provided")

        evaluated_questions = []
        print("\n" + "="*80)
        print(f" STARTING QUESTION-BY-QUESTION EVALUATION (Client {client_index + 1})")
        print("="*80)

        for i, question in enumerate(questions, 1):
            print(f"\n Processing Question {i}/{len(questions)}")
            print("-" * 60)
            
            try:
                q_num = question.get("question_number", f"Q{i}")
                question_text = question.get("question", "")
                correct_answer = question.get("correct_answer", "")
                marking_scheme = question.get("marking_scheme", "")
                student_answer = question.get("student_answer", "")
                image_count = question.get("image_count", 0)
                images = question.get("images", [])

                print(f" Question Number: {q_num}")
                print(f" Question Text: {question_text[:100]}...")
                print(f" Student Answer: {student_answer[:100] if student_answer else 'No answer provided'}...")
                print(f" Image Count: {image_count}")

                # Extract marks from marking scheme or use max_marks field
                marks = question.get("max_marks")
                if marks is None:
                    marks_match = re.search(r'\((\d+)\s*marks?\)', marking_scheme, re.IGNORECASE)
                    marks = int(marks_match.group(1)) if marks_match else 3
                    print(f" Extracted marks from scheme: {marks}")
                else:
                    print(f" Using provided max_marks: {marks}")

                # Format the prompt
                prompt = EVALUATION_PROMPT.format(
                    q_num=q_num,
                    marks=marks,
                    question_text=question_text.strip(),
                    correct_answer=correct_answer.strip(),
                    marking_scheme=marking_scheme.strip(),
                    student_text=student_answer.strip() if student_answer else "No answer provided",
                    image_count=image_count
                )

                # Prepare message content with text and image(s)
                message_content = [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]

                # Add image(s) if available
                if image_count > 0 and images:
                    for img in images[:1]:  # Limit to one image for now
                        if isinstance(img, dict) and "bytes" in img and "format" in img:
                            image_format = img["format"].lower()
                            if image_format not in ["png", "jpeg", "jpg"]:
                                image_format = "png"
                            try:
                                base64.b64decode(img["bytes"])
                                message_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{img['bytes']}"
                                    }
                                })
                                print(f" Added image (format: {image_format}) for question {q_num}")
                                logger.info(f"Added image (format: {image_format}) for question {q_num}")
                            except Exception as e:
                                print(f" Invalid base64 image for question {q_num}: {str(e)}")
                                logger.warning(f"Invalid base64 image for question {q_num}: {str(e)}")
                                message_content.append({
                                    "type": "text",
                                    "text": "Note: Image data provided but invalid or could not be decoded."
                                })
                elif image_count > 0:
                    message_content.append({
                        "type": "text",
                        "text": "Note: Diagrams indicated but no valid image data provided."
                    })
                    print(f" No valid images provided for question {q_num} despite image_count={image_count}")
                    logger.info(f"No valid images provided for question {q_num} despite image_count={image_count}")

                print("\n" + "="*60)
                print(f" SENDING PROMPT TO API (Client {client_index + 1})")
                print("="*60)
                print(prompt)
                if len(message_content) > 1:
                    print(f" Including {len(message_content)-1} image(s) in API call")
                print("="*60)

                # Try to get evaluation from API with retries
                attempt = 0
                response_text = None

                while attempt < max_retries:
                    try:
                        print(f" API Call Attempt {attempt + 1}/{max_retries} for question {q_num}")
                        logger.info(f"Evaluating question {q_num} (Attempt {attempt + 1}/{max_retries}, Client {client_index + 1})")
                        
                        response = client.chat.completions.create(
                            model="meta-llama/llama-4-maverick-17b-128e-instruct",
                            messages=[
                                {"role": "system", "content": "You are an expert in evaluating student answers based on provided mark schemes. Always respond with valid JSON."},
                                {
                                    "role": "user",
                                    "content": message_content
                                }
                            ],
                            temperature=0.3,
                            max_tokens=2048
                        )
                        response_text = response.choices[0].message.content.strip()
                        
                        print(f" API Response received for question {q_num}")
                        print(f" Raw API Response:\n{response_text}")
                        print("-" * 40)
                        
                        if not response_text:
                            raise ValueError("Empty response from API")
                        break
                    except Exception as e:
                        attempt += 1
                        print(f" Error on attempt {attempt}: {str(e)}")
                        logger.error(f"Error evaluating question {q_num} on attempt {attempt}: {str(e)}")
                        if attempt == max_retries:
                            logger.error(f"Max retries reached for question {q_num}")
                            response_text = "[]"
                            break
                        time.sleep(1)

                # Store raw response in evaluated_questions
                evaluated_questions.append({
                    "question_number": q_num,
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "marking_scheme": marking_scheme,
                    "student_answer": student_answer,
                    "image_count": image_count,
                    "images": images,
                    "max_marks": marks,
                    "raw_response": response_text
                })

                print(f" Successfully stored raw response for question {q_num}")
                logger.info(f"Successfully stored raw response for question {q_num}")

            except Exception as e:
                print(f"Error processing question {q_num}: {str(e)}")
                logger.error(f"Error processing question {q_num}: {str(e)}")
                evaluated_questions.append({
                    "question_number": q_num,
                    "question": question.get("question", ""),
                    "correct_answer": question.get("correct_answer", ""),
                    "marking_scheme": question.get("marking_scheme", ""),
                    "student_answer": question.get("student_answer", ""),
                    "image_count": question.get("image_count", 0),
                    "images": question.get("images", []),
                    "max_marks": question.get("max_marks", 3),
                    "raw_response": "[]"
                })

        # Prepare output data
        print("\n" + "="*80)
        print(f"PREPARING FINAL RESULTS (Client {client_index + 1})")
        print("="*80)
        
        output_data = {"questions": evaluated_questions}

        # Print results
        print("\n" + "=" * 60)
        print(f" STUDENT ANSWER EVALUATION RESULTS (RAW, Client {client_index + 1})")
        print("=" * 60)
        print(json.dumps(output_data, indent=2))
        print("=" * 60)

        return output_data

    except Exception as e:
        print(f" Critical Error in evaluate_student_answers (Client {client_index + 1}): {str(e)}")
        logger.error(f"Error in evaluate_student_answers (Client {client_index + 1}): {str(e)}")
        return None

def parse_evaluation_response(evaluation_data: Dict) -> Optional[Dict]:
    """
    Parse raw API responses from evaluate_student_answers into structured evaluation data,
    extracting total_score and total_feedback, and save to a JSON file.

    Args:
        evaluation_data (Dict): Dictionary containing questions with raw API responses

    Returns:
        Optional[Dict]: Parsed evaluations with scores, feedback, and summary statistics
    """
    print("🚀 Starting parsing of evaluation responses...")
    print("=" * 80)

    try:
        # Validate input data structure
        print("🔍 Validating evaluation data structure...")
        if not isinstance(evaluation_data, dict) or "questions" not in evaluation_data:
            logger.error("Invalid evaluation data: Must be a dictionary with 'questions' key")
            raise ValueError("Evaluation data is invalid or missing 'questions' key")

        questions = evaluation_data.get("questions", [])
        if not questions:
            logger.warning("No questions found in evaluation data")
            output_data = {
                "questions": [],
                "summary": {
                    "total_questions": 0,
                    "total_marks": 0,
                    "obtained_marks": 0,
                    "percentage": 0.0
                }
            }
            output_file = f"evaluation_output_{uuid.uuid4()}.json"
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"📝 Saved output to {output_file}")
            return output_data

        print(f"✅ Found {len(questions)} questions to parse")

        parsed_questions = []
        print("\n" + "="*80)
        print("📋 STARTING QUESTION-BY-QUESTION PARSING")
        print("="*80)

        for i, question in enumerate(questions, 1):
            print(f"\n🔄 Parsing Question {i}/{len(questions)}")
            print("-" * 60)
            
            try:
                q_num = question.get("question_number", f"Q{i}")
                question_text = question.get("question", "")
                correct_answer = question.get("correct_answer", "")
                marking_scheme = question.get("marking_scheme", "")
                student_answer = question.get("student_answer", "")
                image_count = question.get("image_count", 0)
                images = question.get("images", [])
                marks = question.get("max_marks", 3)
                response_text = question.get("raw_response", "[]")

                print(f"📝 Question Number: {q_num}")
                print(f"📝 Raw Response: {response_text[:100] if response_text else 'No response'}...")

                # Parse the raw response
                print(f"🔍 Parsing response for question {q_num}...")
                try:
                    evaluation = json.loads(response_text) if response_text else []
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON for question {q_num}: {str(e)}")
                    logger.warning(f"Failed to parse JSON for question {q_num}: {str(e)}")
                    evaluation = [{
                        "question_number": q_num,
                        "total_score": f"0/{marks}",
                        "total_feedback": "Invalid or missing JSON response"
                    }]

                # Ensure evaluation is a list with at least one object
                if not evaluation or not isinstance(evaluation, list) or not evaluation[0]:
                    print(f"⚠️ Empty or invalid evaluation for question {q_num}, using default evaluation")
                    logger.warning(f"Empty or invalid evaluation for question {q_num}")
                    evaluation = [{
                        "question_number": q_num,
                        "total_score": f"0/{marks}",
                        "total_feedback": "No answer provided or evaluation failed."
                    }]

                # Extract evaluation details
                eval_question = evaluation[0]
                print(f"📊 Parsed evaluation: {json.dumps(eval_question, indent=2)}")

                # Validate question number
                if eval_question.get("question_number") != q_num:
                    print(f"⚠️ Question number mismatch for {q_num}")
                    logger.warning(f"Question number mismatch for {q_num}")
                    eval_question["question_number"] = q_num

                # Extract total_score and total_feedback
                total_score = eval_question.get("total_score", f"0/{marks}")
                total_feedback = eval_question.get("total_feedback", 
                    "No answer provided" if not student_answer and image_count == 0
                    else "Evaluation failed or incomplete answer provided"
                )

                # Validate total_score format
                score_match = re.match(r"(\d+)/(\d+)", str(total_score))
                if not score_match or int(score_match.group(2)) != marks:
                    print(f"⚠️ Invalid total_score format for question {q_num}: {total_score}")
                    logger.warning(f"Invalid total_score format for question {q_num}: {total_score}")
                    total_score = f"0/{marks}"

                # Add parsed question to results
                parsed_questions.append({
                    "question_number": q_num,
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "marking_scheme": marking_scheme,
                    "student_answer": student_answer,
                    "image_count": image_count,
                    "images": images,
                    "max_marks": marks,
                    "score": total_score,
                    "feedback": {
                        "total_feedback": total_feedback
                    }
                })

                print(f"✅ Successfully parsed question {q_num} with score {total_score}")
                logger.info(f"Successfully parsed question {q_num} with score {total_score}")

            except Exception as e:
                print(f"❌ Error parsing question {q_num}: {str(e)}")
                logger.error(f"Error parsing question {q_num}: {str(e)}")
                parsed_questions.append({
                    "question_number": q_num,
                    "question": question.get("question", ""),
                    "correct_answer": question.get("correct_answer", ""),
                    "marking_scheme": question.get("marking_scheme", ""),
                    "student_answer": question.get("student_answer", ""),
                    "image_count": question.get("image_count", 0),
                    "images": question.get("images", []),
                    "max_marks": question.get("max_marks", 3),
                    "score": f"0/{question.get('max_marks', 3)}",
                    "feedback": {
                        "total_feedback": f"Parsing failed: {str(e)}"
                    }
                })

        # Prepare output data
        print("\n" + "="*80)
        print("📊 PREPARING FINAL PARSED RESULTS")
        print("="*80)
        
        output_data = {"questions": parsed_questions}

        # Calculate summary statistics
        total_marks = sum(q.get("max_marks", 0) for q in parsed_questions)
        obtained_marks = sum(int(q.get("score", "0/0").split("/")[0]) for q in parsed_questions)

        output_data["summary"] = {
            "total_questions": len(parsed_questions),
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": round((obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2)
        }

        print(f"📈 Summary Statistics:")
        print(f"   - Total Questions: {output_data['summary']['total_questions']}")
        print(f"   - Total Marks: {output_data['summary']['total_marks']}")
        print(f"   - Obtained Marks: {output_data['summary']['obtained_marks']}")
        print(f"   - Percentage: {output_data['summary']['percentage']}%")

        # Save to JSON file
        output_file = f"evaluation_output_{uuid.uuid4()}.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"📝 Saved output to {output_file}")

        # Print results
        print("\n" + "=" * 60)
        print("🎉 PARSED EVALUATION RESULTS")
        print("=" * 60)
        print(json.dumps(output_data, indent=2))
        print("=" * 60)

        return output_data

    except Exception as e:
        print(f"💥 Critical Error in parse_evaluation_response: {str(e)}")
        logger.error(f"Error in parse_evaluation_response: {str(e)}")
        return None
    
def evaluate_all_student_files(merged_files: List[str], student_filenames: List[str]) -> Dict[str, Dict]:
    """
    Evaluates all merged student answer files from the merged_outputs directory in parallel.

    Args:
        merged_files (List[str]): List of paths to merged JSON files (relative to merged_outputs directory).
        student_filenames (List[str]): List of original student filenames for tracking.

    Returns:
        Dict[str, Dict]: Dictionary mapping student filenames to their evaluation results.
    """
    MERGED_OUTPUT_DIR = "merged_outputs"  # Define or import MERGED_OUTPUT_DIR
    evaluation_results = {}
    
    # Initialize Groq clients
    clients = init_groq_clients()
    num_clients = len(clients)
    if num_clients == 0:
        logger.error("No Groq clients available for evaluation")
        print("❌ No Groq clients available for evaluation")
        return {filename: {"questions": []} for filename in student_filenames}

    def process_file(merged_file: str, student_filename: str, client: Groq, client_index: int) -> tuple:
        try:
            # Ensure the merged file path is within the merged_outputs directory
            merged_file_path = os.path.join(MERGED_OUTPUT_DIR, os.path.basename(merged_file))
            logger.info(f"Evaluating merged file {merged_file_path} for {student_filename} with client {client_index + 1}")
            
            # Load the merged JSON file
            if not os.path.exists(merged_file_path):
                logger.error(f"Merged file not found: {merged_file_path}")
                raise FileNotFoundError(f"Merged file not found: {merged_file_path}")
            
            with open(merged_file_path, "r", encoding="utf-8") as f:
                input_data = json.load(f)
            
            # Evaluate the student answers
            result = evaluate_student_answers(
                input_data=input_data,
                max_retries=3,
                client=client,
                client_index=client_index
            )

            if result:
                logger.info(f"Successfully evaluated {student_filename} with client {client_index + 1}")
                
                # Save evaluation results to a file
                output_file = f"evaluation_{''.join(c for c in student_filename if c.isalnum() or c in ('.', '_')).rstrip()}.json"
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    logger.info(f"Saved evaluation results to {output_file}")
                except Exception as e:
                    logger.error(f"Failed to save evaluation results to {output_file}: {str(e)}")
                return student_filename, result
            else:
                logger.warning(f"Evaluation failed for {student_filename}")
                return student_filename, {"questions": []}

        except Exception as e:
            logger.error(f"Error evaluating {merged_file_path} for {student_filename}: {str(e)}")
            print(f"  - Error evaluating {student_filename}: {str(e)}")
            return student_filename, {"questions": []}

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        # Map each file to a client using modulo to cycle through clients
        future_to_file = {
            executor.submit(
                process_file,
                merged_file,
                student_filename,
                clients[i % num_clients],
                i % num_clients
            ): (merged_file, student_filename)
            for i, (merged_file, student_filename) in enumerate(zip(merged_files, student_filenames))
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            merged_file, student_filename = future_to_file[future]
            try:
                student_filename, result = future.result()
                evaluation_results[student_filename] = result
            except Exception as e:
                logger.error(f"Error processing {student_filename}: {str(e)}")
                print(f"  - Error processing {student_filename}: {str(e)}")
                evaluation_results[student_filename] = {"questions": []}

    return evaluation_results


def load_evaluations():
    """Load evaluations from parsed_grading_results.json if available."""
    evaluations = {}
    file_path = Path("parsed_grading_results.json")
    if file_path.exists():
        with open(file_path, 'r') as f:
            try:
                evaluations = json.load(f)
                update_student_id_map(evaluations.keys())
            except json.JSONDecodeError:
                st.warning("Failed to load parsed_grading_results.json. File may be corrupted.")
    return evaluations

def update_student_id_map(filenames):
    """Update student_id_map with filenames, ensuring unique and stable IDs."""
    if "student_id_map" not in st.session_state:
        st.session_state["student_id_map"] = {}
    
    existing_ids = {info["id"] for info in st.session_state["student_id_map"].values()}
    next_index = len(st.session_state["student_id_map"])
    
    for fname in filenames:
        normalized_fname = re.sub(r'[^\w\-_\.]', '_', fname)
        if normalized_fname not in st.session_state["student_id_map"]:
            while f"ID_{next_index:03d}" in existing_ids:
                next_index += 1
            base_name = os.path.basename(fname).replace('.pdf', '')
            st.session_state["student_id_map"][normalized_fname] = {
                "id": f"ID_{next_index:03d}",
                "name": base_name
            }
            existing_ids.add(f"ID_{next_index:03d}")
            next_index += 1

def save_to_json(data, filename):
    """Helper function to save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_confirmed_evaluation(json_input, filename=None):
    """
    Save confirmed evaluation for a question or answer sheet to parsed_grading_results.json or a new file.
    """
    if "evaluations" not in st.session_state:
        st.session_state["evaluations"] = {}
    if "confirmed_evaluations" not in st.session_state:
        st.session_state["confirmed_evaluations"] = {}

    output_data = {}
    answer_sheets_dir = Path("answer_sheets")
    answer_sheets_dir.mkdir(exist_ok=True)

    if filename:
        normalized_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        update_student_id_map([filename])
        
        if filename not in json_input and normalized_filename not in json_input:
            json_input[filename] = {
                "questions": json_input.get(filename, {}).get("questions", []),
                "summary": {}
            }
            new_file_path = answer_sheets_dir / f"{normalized_filename}.json"
            save_to_json(json_input[filename], new_file_path)
            st.info(f"Created new file for {filename} at {new_file_path}")

        working_filename = normalized_filename if normalized_filename in json_input else filename
        if working_filename not in st.session_state["evaluations"]:
            st.session_state["evaluations"][working_filename] = {"questions": [], "summary": {}}

        question_data = json_input[working_filename]["questions"]
        for q_data in question_data:
            question_number = str(q_data.get("question_number"))
            max_marks = q_data.get("max_marks", 1)
            score = q_data.get("score", f"0/{max_marks}")
            try:
                obtained_marks = float(score.split('/')[0])
            except (ValueError, IndexError):
                obtained_marks = 0.0

            question_entry = {
                "question_number": question_number,
                "question": q_data.get("question", ""),
                "correct_answer": q_data.get("correct_answer", ""),
                "marking_scheme": q_data.get("marking_scheme", ""),
                "student_answer": q_data.get("student_answer", ""),
                "image_count": q_data.get("image_count", 0),
                "images": q_data.get("images", []),
                "max_marks": max_marks,
                "score": score,
                "feedback": {"total_feedback": q_data.get("feedback", {}).get("total_feedback", "")}
            }

            existing_questions = [q for q in st.session_state["evaluations"][working_filename]["questions"]
                                  if q["question_number"] != question_number]
            existing_questions.append(question_entry)
            st.session_state["evaluations"][working_filename]["questions"] = sorted(
                existing_questions, key=lambda x: int(x["question_number"])
            )

        total_questions = len(st.session_state["evaluations"][working_filename]["questions"])
        total_marks = sum(q["max_marks"] for q in st.session_state["evaluations"][working_filename]["questions"])
        obtained_marks = sum(float(q["score"].split('/')[0])
                             for q in st.session_state["evaluations"][working_filename]["questions"]
                             if '/' in q["score"])
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0.0

        st.session_state["evaluations"][working_filename]["summary"] = {
            "total_questions": total_questions,
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": percentage
        }

        output_data[working_filename] = st.session_state["evaluations"][working_filename]
        save_to_json(output_data[working_filename], answer_sheets_dir / f"{normalized_filename}.json")

    else:
        question_map = {}
        for answer_sheet, data in json_input.items():
            normalized_answer_sheet = re.sub(r'[^\w\-_\.]', '_', answer_sheet)
            update_student_id_map([answer_sheet])
            for q_data in data["questions"]:
                question_number = str(q_data.get("question_number"))
                if question_number not in question_map:
                    question_map[question_number] = {
                        "question": q_data.get("question", ""),
                        "correct_answer": q_data.get("correct_answer", ""),
                        "marking_scheme": q_data.get("marking_scheme", ""),
                        "student_answers": {}
                    }
                question_map[question_number]["student_answers"][normalized_answer_sheet] = {
                    "id": st.session_state["student_id_map"][normalized_answer_sheet]["id"],
                    "name": st.session_state["student_id_map"][normalized_answer_sheet]["name"],
                    "answer": q_data.get("student_answer", ""),
                    "score": q_data.get("score", f"0/{q_data.get('max_marks', 1)}"),
                    "feedback": q_data.get("feedback", {}).get("total_feedback", "")
                }

        for question_number, question_data in question_map.items():
            if question_number not in st.session_state["confirmed_evaluations"]:
                st.session_state["confirmed_evaluations"][question_number] = {
                    "content": question_data.get("question", ""),
                    "correct_answer": question_data.get("correct_answer", ""),
                    "marking_scheme": question_data.get("marking_scheme", ""),
                    "student_answers": {},
                    "topic": ""
                }

            st.session_state["confirmed_evaluations"][question_number]["student_answers"] = question_data["student_answers"]

            for student_file, student_data in question_data["student_answers"].items():
                normalized_student_file = re.sub(r'[^\w\-_\.]', '_', student_file)
                if normalized_student_file not in st.session_state["evaluations"]:
                    st.session_state["evaluations"][normalized_student_file] = {"questions": [], "summary": {}}

                max_marks = json_input[student_file]["questions"][int(question_number) - 1].get("max_marks", 1)
                question_entry = {
                    "question_number": question_number,
                    "question": question_data.get("question", ""),
                    "correct_answer": question_data.get("correct_answer", ""),
                    "marking_scheme": q_data.get("marking_scheme", ""),
                    "student_answer": student_data.get("answer", ""),
                    "image_count": json_input[student_file]["questions"][int(question_number) - 1].get("image_count", 0),
                    "images": json_input[student_file]["questions"][int(question_number) - 1].get("images", []),
                    "max_marks": max_marks,
                    "score": student_data.get("score", f"0/{max_marks}"),
                    "feedback": {"total_feedback": student_data.get("feedback", "")}
                }

                existing_questions = [q for q in st.session_state["evaluations"][normalized_student_file]["questions"]
                                      if q["question_number"] != question_number]
                existing_questions.append(question_entry)
                st.session_state["evaluations"][normalized_student_file]["questions"] = sorted(
                    existing_questions, key=lambda x: int(x["question_number"])
                )

                total_questions = len(st.session_state["evaluations"][normalized_student_file]["questions"])
                total_marks = sum(q["max_marks"] for q in st.session_state["evaluations"][normalized_student_file]["questions"])
                obtained_marks = sum(float(q["score"].split('/')[0])
                                     for q in st.session_state["evaluations"][normalized_student_file]["questions"]
                                     if '/' in q["score"])
                percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0.0

                st.session_state["evaluations"][normalized_student_file]["summary"] = {
                    "total_questions": total_questions,
                    "total_marks": total_marks,
                    "obtained_marks": obtained_marks,
                    "percentage": percentage
                }

                output_data[normalized_student_file] = st.session_state["evaluations"][normalized_student_file]
                save_to_json(output_data[normalized_student_file], answer_sheets_dir / f"{normalized_student_file}.json")

            question_eval_dir = Path("evaluations_confirmed")
            question_eval_dir.mkdir(exist_ok=True)
            with open(question_eval_dir / f"question_{question_number}_eval.json", 'w') as f:
                json.dump(st.session_state["confirmed_evaluations"][question_number], f, indent=4)

    save_to_json(output_data, "parsed_grading_results.json")

def load_confirmed_evaluations():
    """Load confirmed evaluations from evaluations_confirmed directory."""
    confirmed_evals = {}
    eval_dir = Path("evaluations_confirmed")
    if eval_dir.exists():
        for file in eval_dir.glob("question_*.json"):
            with open(file, 'r') as f:
                try:
                    data = json.load(f)
                    question_num = file.stem.split('_')[1]
                    confirmed_evals[question_num] = data
                    student_files = data.get("student_answers", {}).keys()
                    update_student_id_map(student_files)
                except json.JSONDecodeError:
                    continue
    return confirmed_evals

def build_question_bank():
    """Build or update the question bank with synced scores and feedback."""
    if not st.session_state["evaluations"] and not st.session_state["confirmed_evaluations"]:
        return {}

    question_bank = {}
    for q_num_str, q_data in st.session_state["confirmed_evaluations"].items():
        try:
            q_num = int(q_num_str)
            question_bank[q_num] = {
                "content": q_data.get("content", "Question content not provided"),
                "correct_answer": q_data.get("correct_answer", "N/A"),
                "marking_scheme": q_data.get("marking_scheme", "N/A"),
                "student_answers": q_data.get("student_answers", {}),
                "topic": st.session_state["topic_mapping"].get(q_num_str, "Uncategorized"),
                "max_marks": q_data.get("max_marks", 1)
            }
        except ValueError:
            continue

    for student_file, student_data in st.session_state["evaluations"].items():
        normalized_student_file = re.sub(r'[^\w\-_\.]', '_', student_file)
        update_student_id_map([student_file])
        for q_data in student_data.get("questions", []):
            q_num = int(q_data["question_number"])
            if q_num not in question_bank:
                question_bank[q_num] = {
                    "content": q_data.get("question", "Question content not provided"),
                    "correct_answer": q_data.get("correct_answer", "N/A"),
                    "marking_scheme": q_data.get("marking_scheme", "N/A"),
                    "student_answers": {},
                    "topic": st.session_state["topic_mapping"].get(str(q_num), "Uncategorized"),
                    "max_marks": q_data.get("max_marks", 1)
                }
            base_name = os.path.basename(student_file).replace('.pdf', '')
            sanitized_id = st.session_state["student_id_map"][normalized_student_file]["id"]
            student_id = st.session_state["student_id_map"][normalized_student_file]
            question_bank[q_num]["student_answers"][normalized_student_file] = {
                "id": student_id.get("id", sanitized_id),
                "name": student_id.get("name", base_name),
                "answer": q_data.get("student_answer", "No answer provided"),
                "score": q_data.get("score", f"0/{q_data.get('max_marks', 1)}"),
                "feedback": q_data.get("feedback", {}).get("total_feedback", ""),
                "image_count": q_data.get("image_count", 0),
                "images": q_data.get("images", [])
            }
    
    return question_bank

def get_student_display_name(file_name):
    """Get display name for student, masking only if enabled and on Cross-check & Edit page."""
    normalized_file_name = re.sub(r'[^\w\-_\.]', '_', file_name)
    if normalized_file_name not in st.session_state["student_id_map"]:
        update_student_id_map([file_name])
    if st.session_state["current_page"] == "Cross-check & Edit" and st.session_state["mask_student_names"]:
        return f"Student ID: {st.session_state['student_id_map'][normalized_file_name]['id']}"
    return st.session_state["student_id_map"][normalized_file_name]["name"]

def get_masked_options(options):
    """Mask filenames in dropdown options, only if enabled and on Cross-check & Edit page."""
    if st.session_state["current_page"] != "Cross-check & Edit" or not st.session_state["mask_student_names"]:
        return options
    update_student_id_map([opt for opt in options if opt != "-- Select PDF --"])
    masked_options = ["-- Select PDF --"]
    for opt in options[1:]:
        normalized_opt = re.sub(r'[^\w\-_\.]', '_', opt)
        if normalized_opt in st.session_state["student_id_map"]:
            masked_options.append(f"Student ID: {st.session_state['student_id_map'][normalized_opt]['id']}")
        else:
            st.warning(f"Filename {opt} not found in student_id_map. Skipping in dropdown.")
    return masked_options

def get_original_filename(masked_option):
    """Convert masked option back to original filename."""
    if masked_option == "-- Select PDF --" or st.session_state["current_page"] != "Cross-check & Edit" or not st.session_state["mask_student_names"]:
        return masked_option
    id_match = re.search(r"Student ID: (.+)$", masked_option)
    if id_match:
        student_id = id_match.group(1)
        for filename, info in st.session_state["student_id_map"].items():
            if info.get("id") == student_id:
                return filename
        st.error(f"Could not find filename for {masked_option}. Available IDs: {[info['id'] for info in st.session_state['student_id_map'].values()]}")
    else:
        st.error(f"Invalid masked option format: {masked_option}")
    return None

def clean_text_for_pdf(text):
    """Clean text for PDF generation to handle special characters."""
    return ''.join(c if ord(c) < 128 else ' ' for c in str(text))

def calculate_topic_scores(evaluations, topic_mapping):
    """Calculate topic scores for each student based on evaluations."""
    topic_scores = defaultdict(dict)
    for student, data in evaluations.items():
        topic_totals = defaultdict(float)
        topic_maxes = defaultdict(float)
        for q_data in data.get("questions", []):  # Iterate over the list of questions
            q_num = str(q_data.get("question_number"))  # Get question number as string
            topic = topic_mapping.get("question_mapping", {}).get(q_num, "")
            score_str = q_data.get("score", "0/1")
            try:
                score = float(score_str.split('/')[0])
                max_marks = float(score_str.split('/')[1])
            except (ValueError, IndexError):
                score = 0.0
                max_marks = 1.0
            topic_totals[topic] += score
            topic_maxes[topic] += max_marks
        for topic in topic_totals:
            topic_scores[student][topic] = (
                (topic_totals[topic] / topic_maxes[topic] * 100)
                if topic_maxes[topic] > 0 else 0.0
            )
    return topic_scores

def generate_combined_report(questions, total_score, percentage, topic_summary, images, topic_mapping):
    """Generate a PDF report for a student's evaluation."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    try:
        pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
        pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
    except:
        pdfmetrics.registerFont(TTFont('Vera', 'arial.ttf'))
    c.setFont("VeraBd", 16)
    c.drawCentredString(width / 2, height - 50, "Student Evaluation Report")
    c.setFont("Vera", 12)
    text_obj = c.beginText(50, height - 100)
    text_obj.setFont("Vera", 12)
    report_lines = [
        f"Total Score: {total_score:.1f}",
        f"Percentage: {percentage:.1f}%",
        "",
        "Topic Performance:",
        clean_text_for_pdf(topic_summary),
        "",
        "Question-wise Breakdown:"
    ]
    for q_num, details in sorted(questions.items(), key=lambda x: int(x[0])):
        score = details.get("score", "0/1")
        max_marks = float(score.split('/')[1]) if '/' in score else 1.0
        topic = topic_mapping.get("question_mapping", {}).get(str(q_num), "")
        report_lines.extend([
            f"Question {q_num}: {clean_text_for_pdf(details.get('question', 'N/A'))}",
            f"Score: {score}",
            f"Student Answer: {clean_text_for_pdf(details.get('student_answer', 'N/A'))}",
            f"Correct Answer: {clean_text_for_pdf(details.get('correct_answer', 'N/A'))}",
            f"Feedback: {clean_text_for_pdf(details.get('feedback', {}).get('total_feedback', 'N/A'))}",
            f"Topic: {clean_text_for_pdf(topic)}",
            "-------------------------"
        ])
    for line in report_lines:
        text_obj.textLine(line.encode('utf-8').decode('latin-1', errors='replace'))
    c.drawText(text_obj)
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
