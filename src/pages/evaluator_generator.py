from functions import *
# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Streamlit page configuration
st.set_page_config(layout="wide")

# Constants
MERGED_OUTPUT_DIR = "merged_outputs"

def initialize_session_state():
    """Initialize Streamlit session state with default values."""
    defaults = {
        "current_page": "Upload PDFs",
        "current_option": None,
        "file_id": None,
        "answer_keys": {},
        "question_marks_dict": {},
        "step": "upload",
        "show_details": False,
        "needs_regeneration": False,
        "topic_mapping": {"topics": [], "question_mapping": {}},
        "all_topics": [],
        "student_answers": {},
        "grading_results": {},
        "generated_text": "",
        # "final_max_paper_marks": "",
        "final_max_questions_to_attempt": None,
        "uploaded_file_processed": False,
        "marks_table": None,
        "show_marks_table": False,
        "evaluation_started": False,
        "evaluations": {},
        "final_evals": {},
        "question_bank": {},
        "confirmed_evaluations": {},
        "confirmed_questions": set(),
        "temp_confirmed_questions": set(),
        "current_question": "Select a question to confirm",
        "student_id_map": {},
        "edit_mode": "By Answer Sheet",
        "mask_student_names": False,
        "pending_evaluations": set(),
        "mark_scheme_questions": {},
        "uploaded_file_name": None,
        "merged_results": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    logger.info("Session state initialized")

def main():
    """Main Streamlit application for processing and evaluating student submissions."""
    initialize_session_state()
    logger.info("Starting main application")

    # Consolidated CSS styles
    st.markdown("""
        <style>
            .full-width-button button { width: 100%; padding: 10px; font-size: 16px; }
            .custom-tooltip { position: relative; display: inline-block; cursor: pointer; }
            .custom-tooltip .custom-tooltiptext {
                visibility: hidden;
                width: 700px;
                background-color: #555;
                color: #fff;
                text-align: left;
                border-radius: 4px;
                padding: 6px;
                position: absolute;
                z-index: 1;
                left: 105%;
                top: 50%;
                transform: translateY(-50%);
                opacity: 0;
                transition: opacity 0.3s;
            }
            .custom-tooltip:hover .custom-tooltiptext {
                visibility: visible;
                opacity: 1;
            }
            .section-header { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
            .question-content {
                background-color: #e8f0fe;
                border-left: 4px solid #4285f4;
                padding: 15px;
                margin: 10px 0;
                text-align: left;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            .correct-answer {
                background-color: #e6f4ea;
                border-left: 4px solid #34a853;
                padding: 15px;
                margin: 10px 0;
                text-align: left;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            .marking-scheme {
                background-color: #fef6e0;
                border-left: 4px solid #fbbc04;
                padding: 15px;
                margin: 10px 0;
                text-align: left;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            .student-response-box {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                text-align: left;
                background-color: #f8f9fa;
            }
            .mask-toggle {
                padding: 10px;
                background-color: #f1f3f4;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            .validation-warning {
                background-color: #fce8e6;
                border-left: 4px solid #ea4335;
                padding: 15px;
                margin: 10px 0;
                text-align: left;
            }
            .student-image {
                max-width: 500px;
                margin-top: 10px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            .student-report {
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                background: #f8f9fa;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .metric-box {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e1e4e8;
            }
            .topic-pill {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                margin: 4px;
                font-size: 0.9em;
            }
            .strong-topic {
                background: #e6f4ea;
                color: #137333;
                border: 1px solid #13733320;
            }
            .weak-topic {
                background: #fce8e6;
                color: #a50e0e;
                border: 1px solid #a50e0e20;
            }
            .question-card {
                border-left: 4px solid #1a73e8;
                background: #f8fbff;
                padding: 16px;
                margin: 12px 0;
                border-radius: 4px;
            }
            .analytics-section {
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                background: #f8f9fa;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
        </style>
    """, unsafe_allow_html=True)

    # Page: Upload PDFs
    if st.session_state["current_page"] == "Upload PDFs":
        st.title("Mark Scheme and Student Answer Processing")

        # Step 1: Upload Questions to Generate Mark Scheme
        with st.expander("Step 1: Upload Questions to Generate Mark Scheme", expanded=True):
            st.markdown(
                '''
                <div style="display: flex; align-items: center; margin-bottom: -50px;">
                    <span class="section-header">Upload Questions Paper</span>
                    <div class="custom-tooltip" style="margin-left: 6px;">
                        <span style="font-size: 17px; vertical-align: top; position: relative; top: -3px;">ⓘ</span>
                        <span class="custom-tooltiptext">
                            <b>Instructions:</b><br>
                            Upload a PDF with the questions and marks for each question.<br>
                            <b>Format requirements:</b><br>
                            • The uploaded question paper should be in this format: <br>
                                1. question text (N marks) <br>
                                2. question text (N marks)
                        </span>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )

            uploaded_file = st.file_uploader(
                "",
                type=["pdf"],
                key="answer_key_uploader_generate",
                label_visibility="visible"
            )

            process_uploaded_file(uploaded_file, "Generate and edit mark scheme")

        # Step 2: Review and Edit Marks Allocation
        if st.session_state.get("step") == "review_edit":
            st.subheader("Step 2: Review and Edit Marks Allocation")
            file_name = st.session_state["uploaded_file_name"]
            question_marks_dict = st.session_state["question_marks_dict"]
            questions_count = len(question_marks_dict["question_details"])
            st.markdown(f"**File:** {file_name}")
            st.markdown(f"**Questions Extracted:** {questions_count}")

            st.markdown("**Set Paper Parameters**")
            colA, colB = st.columns(2)
            with colA:
                max_marks = st.number_input(
                    "Maximum Marks for the Paper",
                    min_value=1,
                    value=st.session_state.get("final_max_paper_marks"),
                    step=1,
                    key=f"max_paper_marks_{st.session_state['step']}"
                )
            with colB:
                max_questions = st.number_input(
                    "Maximum Number of Questions to Attempt (if optional)",
                    min_value=1,
                    value=st.session_state.get("final_max_questions_to_attempt", questions_count),
                    step=1,
                    key=f"max_questions_to_attempt_{st.session_state['step']}"
                )
            st.session_state["final_max_paper_marks"] = max_marks
            st.session_state["final_max_questions_to_attempt"] = max_questions
            logger.info(f"Set max paper marks: {max_marks}, max questions to attempt: {max_questions}")

            if st.button("Show Marks Allocation Table", key=f"show_marks_table_{st.session_state['step']}", use_container_width=True):
                st.session_state["show_marks_table"] = True

            if st.session_state.get("show_marks_table", False):
                if question_marks_dict["questions_without_marks"] == len(question_marks_dict["question_details"]):
                    questions_text = ""
                    for q_num, q_data in sorted(question_marks_dict["question_details"].items()):
                        questions_text += f"{q_num}. {q_data.get('question', '')}\n"
                        for sub_q in q_data.get("sub_questions", []):
                            questions_text += f"{sub_q.get('id')} {sub_q.get('text', '')}\n"
                    marks_table, updated_question_marks_dict = process_generate_mark_scheme_pdf(questions_text)
                    st.session_state["question_marks_dict"] = updated_question_marks_dict
                    st.session_state["marks_table"] = marks_table
                    logger.info("Redistributed marks due to no marks detected")
                else:
                    marks_table = st.session_state["marks_table"]

                if question_marks_dict["questions_without_marks"] > 0:
                    st.warning(f"{question_marks_dict['questions_without_marks']} questions have no detected marks. Please review and edit.")
                    logger.warning(f"Found {question_marks_dict['questions_without_marks']} questions without marks")

                marks_table["Marks"] = pd.to_numeric(marks_table["Marks"], errors="coerce").fillna(0).astype(int)
                edited_df = st.data_editor(
                    marks_table,
                    column_config={
                        "Question Number": st.column_config.TextColumn("Question ID", disabled=True),
                        "Question Text": st.column_config.TextColumn("Question Text", disabled=True),
                        "Marks": st.column_config.NumberColumn(
                            "Marks",
                            min_value=0,
                            step=1,
                            format="%d",
                            help="Enter the marks for each question"
                        )
                    },
                    use_container_width=True,
                    hide_index=True,
                    key=f"marks_editor_{st.session_state['step']}"
                )

                if st.button("Confirm and Proceed", key=f"confirm_marks_{st.session_state['step']}", use_container_width=True):
                    with st.spinner("Processing marks and generating mark scheme..."):
                        try:
                            updated_result = apply_marks_updates(edited_df, st.session_state["question_marks_dict"])
                            st.session_state["question_marks_dict"] = updated_result

                            mark_scheme_text = generate_mark_scheme(
                                updated_result["question_details"],
                                client=init_groq_client_mark_scheme(),
                                max_retries=3
                            )
                            if not mark_scheme_text:
                                raise ValueError("Generated mark scheme is empty")
                            st.session_state["generated_text"] = mark_scheme_text
                            with open("marking_scheme.txt", "w", encoding="utf-8") as f:
                                f.write(mark_scheme_text)
                            logger.info("Saved generated mark scheme to marking_scheme.txt")
                            st.session_state["step"] = "edit_mark_scheme"

                            topic_mapping = analyze_question_topics(updated_result["question_details"])
                            st.session_state["topic_mapping"] = topic_mapping
                            st.session_state["all_topics"] = topic_mapping.get("topics", [])
                            with open("topic_mapping.json", "w", encoding="utf-8") as f:
                                json.dump(topic_mapping, f, indent=2)
                            logger.info("Saved topic_mapping to topic_mapping.json")

                            st.success("Marks updated and mark scheme processed. Proceed to review.")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"Error processing marks or mark scheme: {str(e)}")
                            logger.error(f"Error processing: {str(e)}")
                        except Exception as e:
                            st.error(f"Unexpected error: {str(e)}")
                            logger.error(f"Unexpected error: {str(e)}")

        # Step 3: Review and Edit Mark Scheme
        if st.session_state.get("step") == "edit_mark_scheme":
            st.subheader("Step 3: Review and Edit Mark Scheme")
            st.markdown(
                "Review the mark scheme below. Edit as needed, ensuring the format remains consistent "
                "(e.g., **Question X**, **Answer**, **Marking Scheme**)."
            )

            edited_mark_scheme = st.text_area(
                "Edit Mark Scheme",
                value=st.session_state["generated_text"],
                height=500,
                key="mark_scheme_editor"
            )

            if st.button("Save and Finalize Mark Scheme", key="save_final_mark_scheme", use_container_width=True):
                with st.spinner("Finalizing mark scheme..."):
                    try:
                        if not edited_mark_scheme.strip():
                            raise ValueError("Edited mark scheme is empty")
                        
                        with open("final_mark_scheme.txt", "w", encoding="utf-8") as f:
                            f.write(edited_mark_scheme)
                        logger.info("Saved edited mark scheme to final_mark_scheme.txt")

                        parsed_mark_scheme = parse_mark_scheme()
                        if not parsed_mark_scheme["questions"]:
                            raise ValueError("No valid questions parsed from edited mark scheme")

                        question_marks_dict = st.session_state["question_marks_dict"]
                        file_name = st.session_state["uploaded_file_name"]
                        answer_keys = {
                            str(q["question_number"]): {
                                "question": q["question"],
                                "correct_answer": q["answer"],
                                "marking_scheme": q["marking_scheme"]
                            } for q in parsed_mark_scheme["questions"]
                        }
                        st.session_state["answer_keys"] = {file_name: answer_keys}
                        for q in parsed_mark_scheme["questions"]:
                            q_num = str(q["question_number"])
                            if q_num in question_marks_dict["question_details"]:
                                question_marks_dict["question_details"][q_num]["correct_answer"] = q["answer"]
                                question_marks_dict["question_details"][q_num]["marking_scheme"] = q["marking_scheme"]
                        st.session_state["mark_scheme_questions"] = question_marks_dict["question_details"]
                        st.session_state["mark_sheet"] = parsed_mark_scheme

                        with open("question_marks_dict.json", "w", encoding="utf-8") as f:
                            json.dump(question_marks_dict, f, indent=2)
                        logger.info("Saved updated question_marks_dict to question_marks_dict.json")

                        st.session_state["step"] = "proceed"
                        st.success("Mark scheme finalized. Proceed to upload student answer sheets.")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"Error finalizing mark scheme: {str(e)}")
                        logger.error(f"Error finalizing mark scheme: {str(e)}")
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")
                        logger.error(f"Unexpected error: {str(e)}")

        # Step 4: Upload Student Answer Sheets
        if st.session_state.get("step") == "proceed":
            with st.expander("Step 4: Upload Student Answer Sheets", expanded=True):
                st.markdown(
                    '''
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span class="section-header">Upload Student Answer Sheets</span>
                        <div class="custom-tooltip" style="margin-left: 10px;">
                            <span style="font-size: 18px;">ⓘ</span>
                            <span class="custom-tooltiptext">
                                <b>Instructions:</b><br>
                                Upload one or more PDFs or a ZIP folder containing student answer sheets.<br>
                                Each PDF should include:<br>
                                • Question Number (e.g., '1.' or 'Question 1:')<br>
                                • Student's Answer<br>
                                Ensure question numbers match the mark scheme for accurate evaluation.
                            </span>
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

                student_files = st.file_uploader(
                    "Upload Student Answer Sheets (PDF or ZIP)",
                    type=["pdf", "zip"],
                    accept_multiple_files=True,
                    label_visibility="visible",
                    key="student_files_uploader"
                )

                if student_files:
                    student_data = []
                    logger.info(f"Processing {len(student_files)} student files")
                    for file in student_files:
                        try:
                            if file.name.endswith(".pdf"):
                                file_bytes = file.read()
                                text = extract_text_from_pdf(file_bytes)
                                if text:
                                    student_data.append((file.name, text, file_bytes))
                                    logger.debug(f"Extracted text from PDF: {file.name}")
                                else:
                                    st.warning(f"Failed to extract text from '{file.name}'. Please check the PDF.")
                                    logger.warning(f"No text extracted from {file.name}")
                            elif file.name.endswith(".zip"):
                                with zipfile.ZipFile(io.BytesIO(file.read()), "r") as zip_ref:
                                    for extracted_file in zip_ref.namelist():
                                        if extracted_file.endswith(".pdf"):
                                            try:
                                                with zip_ref.open(extracted_file) as pdf_file:
                                                    pdf_bytes = pdf_file.read()
                                                    text = extract_text_from_pdf(pdf_bytes)
                                                    if text:
                                                        base_name = os.path.basename(extracted_file)
                                                        student_data.append((base_name, text, pdf_bytes))
                                                        logger.debug(f"Extracted text from ZIP file: {extracted_file}")
                                                    else:
                                                        st.warning(f"Failed to extract text from '{extracted_file}' in ZIP.")
                                                        logger.warning(f"No text extracted from {extracted_file} in ZIP")
                                            except Exception as e:
                                                st.error(f"Error processing '{extracted_file}' in ZIP: {str(e)}")
                                                logger.error(f"Error processing {extracted_file} in ZIP: {str(e)}")
                                        else:
                                            st.warning(f"Skipping non-PDF file '{extracted_file}' in ZIP.")
                                            logger.warning(f"Non-PDF file {extracted_file} in ZIP")
                        except Exception as e:
                            st.error(f"Error processing file '{file.name}': {str(e)}")
                            logger.error(f"Error processing file {file.name}: {str(e)}")

                    if student_data:
                        ref_key = list(st.session_state["answer_keys"].keys())[0] if st.session_state.get("answer_keys") else None
                        ref_mark = st.session_state["answer_keys"][ref_key] if ref_key else {}
                        expected_count = len(ref_mark) if ref_mark else 0
                        st.session_state["student_answers"] = {}
                        for fname, txt, pdf_bytes in student_data:
                            with st.spinner(f"Processing student answers for '{fname}'..."):
                                try:
                                    stu_dict = parse_student_answers(txt, pdf_bytes, fname)
                                    count = len(stu_dict)
                                    logger.info(f"Parsed {count} answers for {fname}")
                                    if not stu_dict:
                                        st.warning(f"No answers extracted from '{fname}'. Please check the PDF format.")
                                        continue
                                    st.session_state["student_answers"][fname] = stu_dict
                                    if expected_count and count != expected_count:
                                        st.warning(f"Mismatch in '{fname}': Extracted {count} questions (expected {expected_count}).")
                                    else:
                                        st.success(f"Processed '{fname}': {count} questions extracted.")
                                except Exception as e:
                                    st.error(f"Error parsing answers from '{fname}': {str(e)}")
                                    logger.error(f"Error parsing {fname}: {str(e)}")

                if st.session_state["student_answers"]:
                    default_option = "--- Select an answer sheet to view ---"
                    options = [default_option] + list(st.session_state["student_answers"].keys())
                    selected_file = st.selectbox(
                        "Select a student answer sheet to view",
                        options=options,
                        key="student_file_selector",
                        label_visibility="visible"
                    )
                    if selected_file != default_option and selected_file in st.session_state["student_answers"]:
                        st.subheader(f"Extracted Answers from '{selected_file}'")
                        student_data = st.session_state["student_answers"][selected_file]
                        if not student_data:
                            st.warning(f"No answers found for '{selected_file}'. Please check the PDF content.")
                            logger.warning(f"No answers found for {selected_file}")
                        else:
                            display_data = {}
                            for q_num, ans_data in student_data.items():
                                display_data[q_num] = {
                                    "question": ans_data["question"],
                                    "student_answer": ans_data["student_answer"],
                                    "image_count": len(ans_data["images"]),
                                    "images": [
                                        img["bytes"][:50] + "..." 
                                        if isinstance(img, dict) and "bytes" in img 
                                        else "Invalid image data" 
                                        for img in ans_data["images"]
                                    ]
                                }
                            st.json(display_data)
                            for q_num, ans_data in student_data.items():
                                if ans_data.get("images"):
                                    st.markdown(f"**Question {q_num} Images**")
                                    for i, img in enumerate(ans_data["images"], 1):
                                        if isinstance(img, dict) and "bytes" in img:
                                            try:
                                                img_bytes = base64.b64decode(img["bytes"])
                                                st.image(img_bytes, caption=f"Image {i} for Question {q_num}", use_container_width=False)
                                                logger.debug(f"Displayed image {i} for question {q_num}")
                                            except Exception as e:
                                                st.warning(f"Failed to display image {i} for Question {q_num}: {str(e)}")
                                                logger.warning(f"Failed to display image {i} for Question {q_num}: {str(e)}")
                                        else:
                                            st.warning(f"Invalid image data for Question {q_num}, Image {i}")
                                            logger.warning(f"Invalid image data for Question {q_num}, Image {i}")

                if st.session_state.get("student_answers") and st.session_state.get("answer_keys") and st.session_state.get("question_marks_dict"):
                    evaluate_disabled = st.session_state.get("evaluation_started", False)
                    if st.button(
                        "Evaluate Submissions",
                        key="evaluate_button",
                        use_container_width=True,
                        disabled=evaluate_disabled,
                        help="Click to merge and evaluate all student submissions against the mark scheme."
                    ):
                        with st.spinner("Merging and evaluating all submissions..."):
                            try:
                                st.session_state["evaluation_started"] = True
                                logger.info("Starting merging of all student submissions")

                                mark_scheme_file = "final_mark_scheme.json"
                                question_marks_file = "question_marks_dict.json"
                                
                                if not os.path.exists(mark_scheme_file):
                                    st.error(f"Required file missing: {mark_scheme_file}")
                                    logger.error(f"File not found: {mark_scheme_file}")
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()
                                    return
                                if not os.path.exists(question_marks_file):
                                    st.error(f"Required file missing: {question_marks_file}")
                                    logger.error(f"File not found: {question_marks_file}")
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()
                                    return

                                student_answer_files = [
                                    f"student_answers_{''.join(c for c in fname if c.isalnum() or c in ('.', '_')).rstrip()}.json"
                                    for fname in st.session_state["student_answers"].keys()
                                ]
                                missing_files = [f for f in student_answer_files if not os.path.exists(f)]
                                if missing_files:
                                    st.error(f"Missing student answer files: {', '.join(missing_files)}")
                                    logger.error(f"Missing student answer files: {', '.join(missing_files)}")
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()
                                    return

                                merged_results = merge_all_student_files(
                                    student_answer_files=student_answer_files,
                                    mark_scheme_file=mark_scheme_file,
                                    question_marks_file=question_marks_file
                                )
                                
                                st.session_state["merged_results"] = merged_results

                                logger.info("Starting evaluation of all merged files")
                                merged_files = [
                                    os.path.join(MERGED_OUTPUT_DIR, f"merged_output_{''.join(c for c in fname if c.isalnum() or c in ('.', '_')).rstrip()}.json")
                                    for fname in st.session_state["student_answers"].keys()
                                ]
                                logger.info(f"Expected merged files: {merged_files}")
                                missing_merged_files = [f for f in merged_files if not os.path.exists(f)]
                                if missing_merged_files:
                                    st.error(f"Missing merged files: {', '.join(missing_merged_files)}")
                                    logger.error(f"Missing merged files: {', '.join(missing_merged_files)}")
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()
                                    return

                                evaluation_results = evaluate_all_student_files(
                                    merged_files=merged_files,
                                    student_filenames=list(st.session_state["student_answers"].keys())
                                )

                                if evaluation_results:
                                    parsed_evaluation_results = {}
                                    for student_filename, raw_result in evaluation_results.items():
                                        logger.info(f"Parsing evaluation results for {student_filename}")
                                        parsed_result = parse_evaluation_response(raw_result)
                                        if parsed_result:
                                            parsed_evaluation_results[student_filename] = parsed_result
                                            logger.info(f"Successfully parsed evaluation for {student_filename}")
                                        else:
                                            logger.warning(f"Parsing failed for {student_filename}")
                                            parsed_evaluation_results[student_filename] = {
                                                "questions": [],
                                                "summary": {"total_questions": 0, "total_marks": 0, "obtained_marks": 0, "percentage": 0.0}
                                            }

                                    st.session_state["grading_results"] = parsed_evaluation_results
                                    st.session_state["evaluations"] = parsed_evaluation_results
                                    st.success("Evaluation and parsing completed for all submissions! Check the results below.")
                                    logger.info("Evaluation and parsing completed successfully for all submissions")

                                    try:
                                        with open("parsed_grading_results.json", "w", encoding="utf-8") as f:
                                            json.dump(parsed_evaluation_results, f, indent=2)
                                        logger.info("Saved parsed grading results to parsed_grading_results.json")
                                    except Exception as e:
                                        st.error(f"Failed to save parsed grading results: {str(e)}")
                                        logger.error(f"Failed to save parsed_grading_results.json: {str(e)}")

                                    st.session_state["current_page"] = "Cross-check & Edit"
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()
                                else:
                                    st.error("Evaluation failed for all submissions. Check logs for details.")
                                    logger.error("Evaluation returned None for all submissions")
                                    st.session_state["evaluation_started"] = False
                                    st.rerun()

                            except Exception as e:
                                st.error(f"Error during merging, evaluation, or parsing: {str(e)}")
                                logger.error(f"Merge/evaluation/parsing error: {str(e)}")
                                st.session_state["evaluation_started"] = False
                                st.rerun()
                else:
                    logger.warning("Missing required session state variables for evaluation")

    # Page: Cross-check & Edit
    elif st.session_state["current_page"] == "Cross-check & Edit":
        st.header("Confirm / Edit Evaluations")

        if not st.session_state["evaluations"]:
            st.markdown('<div class="validation-warning">No evaluation data found. Please complete the evaluation step first.</div>', unsafe_allow_html=True)
            if st.button("Go to Evaluate Submissions"):
                st.session_state["current_page"] = "Upload PDFs"
                st.session_state["step"] = "proceed"
                st.rerun()
            return

        st.markdown('<div class="mask-toggle">', unsafe_allow_html=True)
        mask_changed = st.checkbox(
            "Mask student names while grading (use ID instead)",
            value=st.session_state["mask_student_names"],
            key="mask_toggle"
        )
        if mask_changed != st.session_state["mask_student_names"]:
            st.session_state["mask_student_names"] = mask_changed
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        edit_mode = st.selectbox(
            "Choose editing mode",
            ["By Answer Sheet", "By Question"],
            index=["By Answer Sheet", "By Question"].index(st.session_state["edit_mode"]),
            key="edit_mode_select"
        )
        if edit_mode != st.session_state["edit_mode"]:
            st.session_state["edit_mode"] = edit_mode
            st.session_state["current_question"] = "Select a question to confirm"
            st.session_state["temp_confirmed_questions"] = set()
            st.rerun()

        if edit_mode == "By Answer Sheet":
            pending_files = [
                fname for fname in st.session_state["evaluations"].keys()
                if fname not in st.session_state["final_evals"]
            ]
            if pending_files:
                left_col, right_col = st.columns([1, 3])
                with left_col:
                    pending_files = ["-- Select PDF --"] + sorted(pending_files)
                    display_options = get_masked_options(pending_files)
                    selected_display = st.selectbox(
                        "Choose Student to Review",
                        display_options,
                        index=0,
                        key="review_select"
                    )
                    selected_file = get_original_filename(selected_display)
                with right_col:
                    if selected_file and selected_file != "-- Select PDF --":
                        if selected_file not in st.session_state["evaluations"]:
                            st.error(f"No evaluation data found for {selected_file}. Please check parsed_grading_results.json.")
                        else:
                            display_name = get_student_display_name(selected_file)
                            st.markdown(f"**Reviewing:** {display_name}")
                            questions_data = st.session_state["evaluations"][selected_file].get("questions", [])
                            if not questions_data:
                                st.warning(f"No questions found for {display_name}. Please verify the evaluation data.")
                            else:
                                edited_questions = []
                                for q_data in sorted(questions_data, key=lambda x: int(x["question_number"])):
                                    q_num = q_data["question_number"]
                                    max_marks = q_data.get("max_marks", 1)
                                    score_str = q_data.get("score", f"0/{max_marks}")
                                    score_value = float(score_str.split('/')[0]) if '/' in score_str else 0.0
                                    feedback = q_data.get("feedback", {}).get("total_feedback", "")
                                    st.markdown(f"#### Question {q_num}")
                                    st.markdown(f'<div class="question-content">{q_data.get("question", "Question content not provided")}</div>', unsafe_allow_html=True)
                                    st.markdown("**Correct Answer:**")
                                    st.markdown(f'<div class="correct-answer">{q_data.get("correct_answer", "N/A")}</div>', unsafe_allow_html=True)
                                    st.markdown("**Student Answer:**")
                                    st.markdown(f'<div class="student-response-box">{q_data.get("student_answer", "No answer provided")}</div>', unsafe_allow_html=True)
                                    if q_data.get("image_count", 0) > 0 and q_data.get("images", []):
                                        st.markdown("**Attached Images:**")
                                        for i, img_data in enumerate(q_data["images"], 1):
                                            try:
                                                img_bytes = base64.b64decode(img_data.get("bytes", ""))
                                                st.image(
                                                    img_bytes,
                                                    caption=f"Image {i} for Question {q_num}",
                                                    
                                                    width=500,
                                                    clamp=True,
                                                    output_format=img_data.get("format", "PNG").upper()
                                                )
                                            except Exception as e:
                                                st.warning(f"Failed to display image {i} for Question {q_num}: {str(e)}")
                                    st.markdown("**Marking Scheme:**")
                                    st.markdown(f'<div class="marking-scheme">{q_data.get("marking_scheme", "N/A")}</div>', unsafe_allow_html=True)
                                    score_num = st.number_input(
                                        f"Score for Question {q_num} (max {max_marks})",
                                        min_value=0.0,
                                        max_value=float(max_marks),
                                        value=score_value,
                                        step=0.5,
                                        key=f"score_{selected_file}_{q_num}"
                                    )
                                    feedback_text = st.text_area(
                                        f"Feedback for Question {q_num}",
                                        value=feedback,
                                        key=f"feedback_{selected_file}_{q_num}"
                                    )
                                    edited_questions.append({
                                        "question_number": q_num,
                                        "question": q_data.get("question", ""),
                                        "correct_answer": q_data.get("correct_answer", ""),
                                        "marking_scheme": q_data.get("marking_scheme", ""),
                                        "student_answer": q_data.get("student_answer", ""),
                                        "image_count": q_data.get("image_count", 0),
                                        "images": q_data.get("images", []),
                                        "max_marks": max_marks,
                                        "score": f"{score_num}/{max_marks}",
                                        "feedback": {"total_feedback": feedback_text}
                                    })
                                st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                                if st.button("Confirm Evaluation", key=f"confirm_{selected_file}"):
                                    json_input = {
                                        selected_file: {
                                            "questions": edited_questions,
                                            "summary": st.session_state["evaluations"].get(selected_file, {}).get("summary", {})
                                        }
                                    }
                                    save_confirmed_evaluation(json_input, selected_file)
                                    st.session_state["final_evals"][selected_file] = True
                                    st.success(f"Evaluation for {display_name} confirmed and saved.")
                                    remaining_files = [
                                        fname for fname in st.session_state["evaluations"].keys()
                                        if fname not in st.session_state["final_evals"]
                                    ]
                                    if not remaining_files:
                                        st.session_state["mask_student_names"] = False
                                        report_dir = Path("Evaluation_Reports")
                                        report_dir.mkdir(exist_ok=True)
                                        original_filename = os.path.basename(selected_file).replace('.pdf', '')
                                        safe_filename = re.sub(r'[\\/*?:"<>|]', "_", original_filename)
                                        report_content = [
                                            f"Evaluation Report: {original_filename}",
                                            f"Student Name: {st.session_state['student_id_map'].get(selected_file, {}).get('name', original_filename)}",
                                            f"Original File: {selected_file}\n"
                                        ]
                                        total_score = 0
                                        max_score = 0
                                        for q in edited_questions:
                                            score_val = float(q["score"].split('/')[0]) if '/' in q["score"] else 0
                                            max_val = float(q["score"].split('/')[1]) if '/' in q["score"] else 1
                                            total_score += score_val
                                            max_score += max_val
                                            report_content.extend([
                                                f"\nQuestion {q['question_number']}: {q['question']}",
                                                f"Score: {q['score']}",
                                                f"Feedback: {q['feedback']['total_feedback']}",
                                                "-------------------------"
                                            ])
                                        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
                                        report_content.extend([
                                            f"\nSummary:",
                                            f"Total Questions: {len(edited_questions)}",
                                            f"Total Marks: {total_score}/{max_score}",
                                            f"Percentage: {percentage:.1f}%"
                                        ])
                                        try:
                                            with open(report_dir / f"{safe_filename}_report.txt", 'w', encoding="utf-8") as f:
                                                f.write("\n".join(report_content))
                                        except Exception as e:
                                            st.error(f"Error saving report for {original_filename}: {str(e)}")
                                        st.session_state["current_page"] = "Student Reports"
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            **Workflow Guide:**
                            1. Select a student from the left dropdown
                            2. Review auto-generated evaluations
                            3. Adjust scores and feedback as needed
                            4. Confirm to save and proceed
                        """)
            else:
                if st.session_state["evaluations"]:
                    st.session_state["mask_student_names"] = False
                    st.info("All answer sheets have been confirmed. Proceeding to Student Reports.")
                    st.session_state["current_page"] = "Student Reports"
                    st.rerun()
                else:
                    st.markdown('<div class="validation-warning">No evaluations found. Please ensure submissions have been evaluated.</div>', unsafe_allow_html=True)
                    if st.button("Go to Evaluate Submissions"):
                        st.session_state["current_page"] = "Upload PDFs"
                        st.session_state["step"] = "proceed"
                        st.rerun()

        elif edit_mode == "By Question":
            st.session_state["question_bank"] = build_question_bank()
            question_numbers = sorted(st.session_state["question_bank"].keys(), key=int)
            if question_numbers:
                options = ["Select a question to confirm"] + [str(q) for q in question_numbers
                                                             if str(q) not in st.session_state["confirmed_questions"]]
                default_index = (
                    options.index(st.session_state["current_question"])
                    if st.session_state["current_question"] in options else 0
                )
                selected_q_num = st.selectbox(
                    "Select Question",
                    options=options,
                    index=default_index,
                    format_func=lambda x: (
                        "Select a question to confirm" if x == "Select a question to confirm"
                        else f"Q{x}: {st.session_state['question_bank'][int(x)]['content'][:50]}..."
                    ),
                    key="question_selector"
                )
                if selected_q_num != st.session_state["current_question"]:
                    st.session_state["current_question"] = selected_q_num
                    st.session_state["temp_confirmed_questions"] = set()
                    st.rerun()
                if selected_q_num != "Select a question to confirm":
                    q_num = int(selected_q_num)
                    q_data = st.session_state["question_bank"].get(q_num, {})
                    topic = st.session_state["topic_mapping"].get(str(q_num), "")
                    max_marks = q_data.get("max_marks", 1)
                    st.markdown(f"### Question {q_num}")
                    st.markdown(f'<div class="question-content">{q_data.get("content", "Question content not provided")}</div>', unsafe_allow_html=True)
                    st.markdown("**Correct Answer:**")
                    st.markdown(f'<div class="correct-answer">{q_data.get("correct_answer", "N/A")}</div>', unsafe_allow_html=True)
                    st.markdown("**Marking Scheme:**")
                    st.markdown(f'<div class="marking-scheme">{q_data.get("marking_scheme", "N/A")}</div>', unsafe_allow_html=True)
                    st.markdown("---")
                    st.subheader("Student Responses")
                    edited_student_answers = {}
                    student_files = sorted(q_data.get("student_answers", {}).keys())
                    if not student_files:
                        st.warning("No student responses available for this question.")
                    for student_file in student_files:
                        s_data = q_data["student_answers"].get(student_file, {})
                        display_name = get_student_display_name(student_file)
                        score_str = s_data.get("score", f"0/{max_marks}")
                        score_value = float(score_str.split('/')[0]) if '/' in score_str else 0.0
                        feedback = s_data.get("feedback", "")
                        st.markdown(f'<div class="student-response-box">', unsafe_allow_html=True)
                        st.markdown(f"**{display_name}:**")
                        st.markdown(f"**Answer:** {s_data.get('answer', 'No answer provided')}")
                        if s_data.get("image_count", 0) > 0 and s_data.get("images", []):
                            st.markdown("**Attached Images:**")
                            for i, img_data in enumerate(s_data["images"], 1):
                                try:
                                    img_bytes = base64.b64decode(img_data.get("bytes", ""))
                                    st.image(
                                        img_bytes,
                                        caption=f"Image {i} for {display_name}, Question {q_num}",
                                        use_container_width=False,
                                        width=500,
                                        clamp=True,
                                        output_format=img_data.get("format", "PNG").upper()
                                    )
                                except Exception as e:
                                    st.warning(f"Failed to display image {i} for {display_name}, Question {q_num}: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        score_num = st.number_input(
                            f"Score for {display_name} (max {max_marks})",
                            min_value=0.0,
                            max_value=float(max_marks),
                            value=score_value,
                            step=0.5,
                            key=f"score_{q_num}_{student_file}"
                        )
                        feedback_text = st.text_area(
                            f"Feedback for {display_name}",
                            value=feedback,
                            key=f"feedback_{q_num}_{student_file}",
                            height=80
                        )
                        edited_student_answers[student_file] = {
                            "id": s_data.get("id", ""),
                            "name": s_data.get("name", ""),
                            "answer": s_data.get("answer", ""),
                            "score": f"{score_num}/{max_marks}",
                            "feedback": feedback_text,
                            "image_count": s_data.get("image_count", 0),
                            "images": s_data.get("images", [])
                        }
                    if student_files:
                        st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                        if st.button("Confirm Question Evaluation", key=f"confirm_q_{q_num}"):
                            question_data = {
                                "question_number": q_num,
                                "question": q_data.get("content", ""),
                                "correct_answer": q_data.get("correct_answer", ""),
                                "marking_scheme": q_data.get("marking_scheme", ""),
                                "student_answers": edited_student_answers,
                                "topic": topic,
                                "max_marks": max_marks
                            }
                            save_confirmed_evaluation(question_data)
                            st.session_state["confirmed_questions"].add(str(q_num))
                            st.success(f"Evaluation for Question {q_num} confirmed and saved.")
                            remaining_questions = [
                                str(q) for q in question_numbers
                                if str(q) not in st.session_state["confirmed_questions"]
                            ]
                            if not remaining_questions:
                                st.session_state["mask_student_names"] = False
                                st.session_state["current_page"] = "Student Reports"
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.session_state["mask_student_names"] = False
                st.info("No questions available to review.")
                st.session_state["current_page"] = "Student Reports"
                st.rerun()

        if st.session_state.get("evaluations", {}):
            st.markdown("---")
            st.subheader("One-Shot Confirmation")
            st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
            if st.button("✅ Confirm All Evaluations", key="confirm_all"):
                with st.spinner("Finalizing all evaluations and generating reports..."):
                    for student_file, student_data in st.session_state["evaluations"].items():
                        if student_file not in st.session_state["final_evals"]:
                            edited_questions = []
                            for q_data in student_data.get("questions", []):
                                q_num = q_data["question_number"]
                                max_marks = q_data.get("max_marks", 1)
                                score = q_data.get("score", f"0/{max_marks}")
                                feedback = q_data.get("feedback", {}).get("total_feedback", "")
                                edited_questions.append({
                                    "question_number": q_num,
                                    "question": q_data.get("question", ""),
                                    "correct_answer": q_data.get("correct_answer", ""),
                                    "marking_scheme": q_data.get("marking_scheme", ""),
                                    "student_answer": q_data.get("student_answer", ""),
                                    "image_count": q_data.get("image_count", 0),
                                    "images": q_data.get("images", []),
                                    "max_marks": max_marks,
                                    "score": score,
                                    "feedback": {"total_feedback": feedback}
                                })
                            json_input = {
                                student_file: {
                                    "questions": edited_questions,
                                    "summary": student_data.get("summary", {})
                                }
                            }
                            save_confirmed_evaluation(json_input, student_file)
                            st.session_state["final_evals"][student_file] = True
                            report_dir = Path("Evaluation_Reports")
                            report_dir.mkdir(exist_ok=True)
                            original_filename = os.path.basename(student_file).replace('.pdf', '')
                            safe_filename = re.sub(r'[\\/*?:"<>|]', "_", original_filename)
                            report_content = [
                                f"Evaluation Report: {original_filename}",
                                f"Student Name: {st.session_state['student_id_map'].get(student_file, {}).get('name', original_filename)}",
                                f"Original File: {student_file}\n"
                            ]
                            total_score = 0
                            max_score = 0
                            for q in st.session_state["evaluations"][student_file]["questions"]:
                                score_val = float(q["score"].split('/')[0]) if '/' in q["score"] else 0
                                max_val = float(q["score"].split('/')[1]) if '/' in q["score"] else 1
                                total_score += score_val
                                max_score += max_val
                                report_content.extend([
                                    f"\nQuestion {q['question_number']}: {q['question']}",
                                    f"Score: {q['score']}",
                                    f"Feedback: {q['feedback']['total_feedback']}",
                                    "-------------------------"
                                ])
                            percentage = (total_score / max_score) * 100 if max_score > 0 else 0
                            report_content.extend([
                                f"\nSummary:",
                                f"Total Questions: {st.session_state['evaluations'][student_file]['summary']['total_questions']}",
                                f"Total Marks: {total_score}/{max_score}",
                                f"Percentage: {percentage:.1f}%"
                            ])
                            try:
                                with open(report_dir / f"{safe_filename}_report.txt", 'w', encoding="utf-8") as f:
                                    f.write("\n".join(report_content))
                            except Exception as e:
                                st.error(f"Error saving report for {original_filename}: {str(e)}")
                    st.session_state["mask_student_names"] = False
                    st.success("All evaluations confirmed and reports generated!")
                    st.session_state["current_page"] = "Student Reports"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.session_state["mask_student_names"] = False
            st.info("No evaluations to review")
            st.session_state["current_page"] = "Student Reports"
            st.rerun()

    # Page: Student Reports
    elif st.session_state["current_page"] == "Student Reports":
        st.header("Individual Student Reports")

        if "topic_mapping" not in st.session_state:
            try:
                with open("topic_mapping.json", "r") as f:
                    st.session_state["topic_mapping"] = json.load(f)
            except FileNotFoundError:
                st.session_state["topic_mapping"] = {"topics": [], "question_mapping": {}}
                st.warning("topic_mapping.json not found. Using empty topic mapping.")

        if "final_evals" in st.session_state and st.session_state["final_evals"]:
            students = sorted(st.session_state["final_evals"].keys())
            display_options = ["-- Select Student --"] + [
                st.session_state["student_id_map"].get(student, {"id": f"ID_{i:03d}"}).get("id")
                if st.session_state["mask_student_names"]
                else os.path.basename(student).replace('.pdf', '')
                for i, student in enumerate(students)
            ]
            selected_display = st.selectbox(
                "Select Student Report",
                options=display_options,
                index=0,
                key="student_report_selector"
            )
            selected_student = next(
                (student for student in students if (
                    st.session_state["student_id_map"].get(student, {"id": f"ID_{i:03d}"}).get("id")
                    if st.session_state["mask_student_names"]
                    else os.path.basename(student).replace('.pdf', '')
                ) == selected_display),
                None
            )

            if selected_student and selected_display != "-- Select Student --":
                student_data = st.session_state["evaluations"].get(selected_student, {})
                questions = student_data.get("questions", [])
                summary = student_data.get("summary", {})
                total_score = summary.get("obtained_marks", 0)
                max_score = summary.get("total_marks", 1)
                percentage = summary.get("percentage", 0.0)

                topic_scores = calculate_topic_scores(
                    {selected_student: student_data},
                    st.session_state["topic_mapping"]
                )
                strong_topics = [(topic, score) for topic, score in topic_scores[selected_student].items() if score >= 60]
                weak_topics = [(topic, score) for topic, score in topic_scores[selected_student].items() if score < 60]

                with st.container():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<div style="font-size:0.9em; color:#5f6368;">Total Score</div>'
                            f'<div style="font-size:2em; font-weight:bold; color:#1a73e8;">{total_score:.1f}/{max_score}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with col2:
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<div style="font-size:0.9em; color:#5f6368;">Percentage</div>'
                            f'<div style="font-size:2em; font-weight:bold; color:#1a73e8;">{percentage:.1f}%</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    st.subheader("Topic Performance Analysis")
                    topics_col1, topics_col2 = st.columns(2)
                    with topics_col1:
                        if strong_topics:
                            st.markdown("### Strong Areas")
                            for topic, score in sorted(strong_topics, key=lambda x: -x[1]):
                                st.markdown(
                                    f'<div class="topic-pill strong-topic">'
                                    f'{clean_text_for_pdf(topic)} ({score:.1f}%)'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info("No strong areas identified")
                    with topics_col2:
                        if weak_topics:
                            st.markdown("### Weak Areas")
                            for topic, score in sorted(weak_topics, key=lambda x: x[1]):
                                st.markdown(
                                    f'<div class="topic-pill weak-topic">'
                                    f'{clean_text_for_pdf(topic)} ({score:.1f}%)'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info("No weak areas identified")

                    st.subheader("Question-wise Breakdown")
                    for q_data in sorted(questions, key=lambda x: int(x["question_number"])):
                        q_num = q_data["question_number"]
                        max_marks = q_data.get("max_marks", 1)
                        score = q_data.get("score", f"0/{max_marks}")
                        topic = st.session_state["topic_mapping"].get("question_mapping", {}).get(str(q_num), "Uncategorized")
                        with st.expander(f"Question {q_num} - Score: {score}", expanded=False):
                            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
                            st.markdown(f"**Question:** {clean_text_for_pdf(q_data.get('question', 'N/A'))}")
                            st.markdown(f"**Correct Answer:** {clean_text_for_pdf(q_data.get('correct_answer', 'N/A'))}")
                            st.markdown(f"**Student's Answer:** {clean_text_for_pdf(q_data.get('student_answer', 'No answer provided'))}")
                            st.markdown(f"**Feedback:** {clean_text_for_pdf(q_data.get('feedback', {}).get('total_feedback', 'N/A'))}")
                            st.markdown(f"**Topic:** {clean_text_for_pdf(topic)}")
                            st.markdown('</div>', unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        report_questions = {
                            q["question_number"]: {
                                "question": q["question"],
                                "correct_answer": q["correct_answer"],
                                "student_answer": q["student_answer"],
                                "score": q["score"],
                                "feedback": q["feedback"],
                                "max_marks": q["max_marks"]
                            } for q in questions
                        }
                        topic_summary = (
                            f"Strong topics: {', '.join([f'{clean_text_for_pdf(t)} ({s:.1f}%)' for t, s in strong_topics])}\n"
                            f"Weak topics: {', '.join([f'{clean_text_for_pdf(t)} ({s:.1f}%)' for t, s in weak_topics])}"
                        )
                        report_bytes = generate_combined_report(
                            report_questions,
                            total_score,
                            percentage,
                            topic_summary,
                            [],
                            st.session_state["topic_mapping"]
                        )
                        st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                        st.download_button(
                            label="Download Full Report",
                            data=report_bytes,
                            file_name=f"{os.path.basename(selected_student).replace('.pdf', '')}_report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                        if st.button("View Class Analytics →", use_container_width=True):
                            st.session_state["current_page"] = "Analytics for Instructor"
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No student evaluations available yet. Complete evaluations to view reports.")
            if st.button("Back to Cross-check & Edit"):
                st.session_state["current_page"] = "Cross-check & Edit"
                st.rerun()

    # Page: Analytics for Instructor
    elif st.session_state["current_page"] == "Analytics for Instructor":
        st.header("Class Analytics")

        if "final_evals" not in st.session_state or not st.session_state["final_evals"]:
            st.info("No evaluation data available yet. Please complete student evaluations first.")
            if st.button("← Back to Student Reports"):
                st.session_state["current_page"] = "Student Reports"
                st.rerun()
        else:
            topic_mapping = st.session_state.get("topic_mapping", {})
            st.subheader("Performance by Student")
            student_avg_scores = {}
            for student, data in st.session_state["evaluations"].items():
                summary = data.get("summary", {})
                percentage = summary.get("percentage", 0.0)
                display_name = (
                    st.session_state["student_id_map"].get(student, {"id": f"ID_{hash(student) % 1000:03d}"}).get("id")
                    if st.session_state["mask_student_names"]
                    else os.path.basename(student).replace('.pdf', '')
                )
                student_avg_scores[display_name] = percentage
            student_df = pd.DataFrame({
                "Student": list(student_avg_scores.keys()),
                "Average Score %": list(student_avg_scores.values())
            })
            student_df["Label"] = student_df["Average Score %"].round(1).astype(str)
            student_df = student_df.sort_values("Average Score %", ascending=False)
            fig1 = px.bar(
                student_df,
                x="Student",
                y="Average Score %",
                text="Label",
                color="Average Score %",
                color_continuous_scale="Blues",
                height=400
            )
            fig1.update_traces(textposition='auto')
            fig1.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Performance by Topic")
            topic_scores = calculate_topic_scores(st.session_state["evaluations"], topic_mapping)
            topic_avg_scores = defaultdict(list)
            for scores in topic_scores.values():
                for topic, score in scores.items():
                    topic_avg_scores[topic].append(score)
            topic_avg_scores = {topic: np.mean(scores) for topic, scores in topic_avg_scores.items()}
            topic_df = pd.DataFrame({
                "Topic": list(topic_avg_scores.keys()),
                "Average Score %": list(topic_avg_scores.values())
            })
            topic_df["Label"] = topic_df["Average Score %"].round(1).astype(str)
            topic_df = topic_df.sort_values("Average Score %", ascending=False)
            fig2 = px.bar(
                topic_df,
                x="Topic",
                y="Average Score %",
                text="Label",
                color="Average Score %",
                color_continuous_scale="Blues",
                height=500
            )
            fig2.update_traces(textposition='auto')
            fig2.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Student Performance by Topic")
            students = sorted(st.session_state["evaluations"].keys())
            display_options = ["-- Select Student --"] + [
                st.session_state["student_id_map"].get(student, {"id": f"ID_{i:03d}"}).get("id")
                if st.session_state["mask_student_names"]
                else os.path.basename(student).replace('.pdf', '')
                for i, student in enumerate(students)
            ]
            selected_display = st.selectbox(
                "Select Student for Detailed Table",
                options=display_options,
                index=0,
                key="analytics_student_selector"
            )
            selected_student = next(
                (student for student in students if (
                    st.session_state["student_id_map"].get(student, {"id": f"ID_{i:03d}"}).get("id")
                    if st.session_state["mask_student_names"]
                    else os.path.basename(student).replace('.pdf', '')
                ) == selected_display),
                None
            )
            if selected_student and selected_display != "-- Select Student --":
                topic_class_avg = defaultdict(list)
                for s, scores in topic_scores.items():
                    for t, score in scores.items():
                        topic_class_avg[t].append(score)
                topic_class_avg = {t: np.mean(scores) for t, scores in topic_class_avg.items()}
                structured_data = []
                for topic in sorted(set(topic_mapping.get("question_mapping", {}).values())):
                    questions = [q for q, t in topic_mapping.get("question_mapping", {}).items() if t == topic]
                    student_topic_score = topic_scores[selected_student].get(topic, 0)
                    class_avg = topic_class_avg.get(topic, 0)
                    structured_data.append({
                        "Topic": topic,
                        "Questions": ", ".join(map(str, questions)),
                        "Score (%)": student_topic_score,
                        "Class avg (%)": class_avg
                    })
                table_df = pd.DataFrame(structured_data)
                table_df.reset_index(drop=True, inplace=True)
                styled_table = (
                    table_df.style
                    .set_properties(subset=["Questions", "Score (%)", "Class avg (%)"], **{"text-align": "center"})
                    .set_table_styles([
                        {"selector": "th:not(:first-child)", "props": [("text-align", "center")]},
                        {"selector": "thead th:first-child", "props": [("display", "none")]},
                        {"selector": "tbody th:first-child", "props": [("display", "none")]}
                    ])
                )
                st.markdown(styled_table.to_html(), unsafe_allow_html=True)

            st.markdown("---")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                if st.button("← Back to Student Reports", use_container_width=True):
                    st.session_state["current_page"] = "Student Reports"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="full-width-button">', unsafe_allow_html=True)
                if st.button("↺ Back to Upload PDFs", use_container_width=True):
                    st.session_state["current_page"] = "Upload PDFs"
                    st.session_state["evaluations"] = {}
                    st.session_state["final_evals"] = {}
                    st.session_state["question_bank"] = {}
                    st.session_state["confirmed_evaluations"] = {}
                    st.session_state["confirmed_questions"] = set()
                    st.session_state["temp_confirmed_questions"] = set()
                    st.session_state["current_question"] = None
                    st.session_state["student_id_map"] = {}
                    st.session_state["topic_mapping"] = {}
                    st.session_state["edit_mode"] = "By Answer Sheet"
                    st.session_state["mask_student_names"] = False
                    st.session_state["pending_evaluations"] = set()
                    st.session_state["mark_scheme_questions"] = {}
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()