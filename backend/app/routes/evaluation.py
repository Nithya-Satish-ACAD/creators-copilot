from fastapi import APIRouter, Request, UploadFile, Depends
from pydantic import BaseModel
from fastapi import Form, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
import json
from uuid import uuid4
import shutil
import asyncio
from datetime import datetime
from flask import request
import os
from pathlib import Path
import csv
import io
from ..utils.verify_token import verify_token
from app.services.mongo import create_evaluation, get_evaluation_by_evaluation_id, update_evaluation_with_result, update_question_score_feedback, update_evaluation, get_evaluations_by_course_id, create_asset, db, get_email_by_user_id, create_ai_feedback, get_ai_feedback_by_evaluation_id, update_ai_feedback
from app.services.openai_service import create_evaluation_assistant_and_vector_store, evaluate_files_all_in_one
from concurrent.futures import ThreadPoolExecutor
from app.utils.eval_mail import send_eval_completion_email, send_eval_error_email
from app.utils.extraction_answersheet import extract_text_tables, split_into_qas
from app.utils.extraction_markscheme import extract_text_from_mark_scheme
logger = logging.getLogger(__name__)
router = APIRouter()

class UploadFilesRequest(BaseModel):
    user_id: str
    course_id: str
    files: List[UploadFile]

class EvaluationResponse(BaseModel):
    evaluation_id: str
    evaluation_result: dict

class EditresultRequest(BaseModel):
    evaluation_id: str
    file_id: str
    question_number: str
    score: float
    feedback: str

@router.post("/evaluation/upload-mark-scheme")
def upload_mark_scheme(course_id: str = Form(...), user_id: str = Depends(verify_token), mark_scheme: UploadFile = File(...)):
    try:
        evaluation_id = str(uuid4())
        
        # Create directory for this evaluation
        eval_dir = Path(f"local_storage/temp_evaluations/{evaluation_id}")
        eval_dir.mkdir(parents=True, exist_ok=True)
        
        # Save mark scheme file locally
        mark_scheme_filename = f"mark_scheme_{mark_scheme.filename}"
        mark_scheme_path = eval_dir / mark_scheme_filename
        
        with open(mark_scheme_path, "wb") as f:
            content = mark_scheme.file.read()
            f.write(content)
        
        logger.info(f"Saved mark scheme to {mark_scheme_path}")
        
        # Create evaluation assistant for LLM evaluation later
        eval_info = create_evaluation_assistant_and_vector_store(evaluation_id)
        evaluation_assistant_id = eval_info[0]
        vector_store_id = eval_info[1]
        
        # Create evaluation record
        create_evaluation(
            evaluation_id=evaluation_id,
            course_id=course_id,
            evaluation_assistant_id=evaluation_assistant_id,
            vector_store_id=vector_store_id,
            mark_scheme_path=str(mark_scheme_path),
            answer_sheet_paths=[],
            answer_sheet_filenames=[]
        )
        
        # Verify creation
        created_evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not created_evaluation:
            logger.error(f"Failed to create evaluation {evaluation_id}")
            raise HTTPException(status_code=500, detail="Failed to create evaluation record")
        
        logger.info(f"Successfully created evaluation {evaluation_id}")
        
        return {
            "evaluation_id": evaluation_id,
            "message": "Mark scheme uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading mark scheme: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading mark scheme: {str(e)}")

@router.post("/evaluation/upload-answer-sheets")
def upload_answer_sheets(evaluation_id: str = Form(...), answer_sheets: List[UploadFile] = File(...), user_id: str = Depends(verify_token)):
    try:
        # Validate inputs
        if not answer_sheets:
            raise HTTPException(status_code=400, detail="No answer sheet files provided")
        
        logger.info(f"Uploading {len(answer_sheets)} answer sheets for evaluation {evaluation_id}")
        
        # Get evaluation record
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Check if mark scheme exists
        if not evaluation.get("mark_scheme_path"):
            raise HTTPException(status_code=400, detail="Mark scheme must be uploaded first")
        
        # Save answer sheets locally
        eval_dir = Path(f"local_storage/temp_evaluations/{evaluation_id}")
        eval_dir.mkdir(parents=True, exist_ok=True)
        
        answer_sheet_paths = []
        answer_sheet_filenames = []
        
        for i, answer_sheet in enumerate(answer_sheets):
            filename = f"answer_sheet_{i+1}_{answer_sheet.filename}"
            file_path = eval_dir / filename
            
            with open(file_path, "wb") as f:
                content = answer_sheet.file.read()
                f.write(content)
            
            answer_sheet_paths.append(str(file_path))
            answer_sheet_filenames.append(answer_sheet.filename)
            logger.info(f"Saved answer sheet to {file_path}")
        
        # Update evaluation record
        update_evaluation(evaluation_id, {
            "answer_sheet_paths": answer_sheet_paths,
            "answer_sheet_filenames": answer_sheet_filenames
        })
        
        logger.info(f"Successfully uploaded {len(answer_sheet_paths)} answer sheets for evaluation {evaluation_id}")

        return {
            "evaluation_id": evaluation_id,
            "answer_sheet_count": len(answer_sheet_paths),
            "answer_sheet_filenames": answer_sheet_filenames
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading answer sheets for evaluation {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading answer sheets: {str(e)}")

def _process_evaluation(evaluation_id: str, user_id: str):
    """Process evaluation in background using local file extraction with parallel workers"""
    try:
        # Check if evaluation is already completed
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            logger.error(f"Evaluation {evaluation_id} not found")
            return
        
        # If evaluation is already completed, don't process again
        if evaluation.get("status") == "completed" and "evaluation_result" in evaluation:
            logger.info(f"Evaluation {evaluation_id} is already completed, skipping processing")
            return
        
        logger.info(f"Starting evaluation processing for {evaluation_id}")
        
        mark_scheme_path = evaluation.get("mark_scheme_path")
        answer_sheet_paths = evaluation.get("answer_sheet_paths", [])
        answer_sheet_filenames = evaluation.get("answer_sheet_filenames", [])
        
        if not mark_scheme_path or not answer_sheet_paths:
            logger.error(f"Missing file paths for evaluation {evaluation_id}")
            return
        
        # Extract mark scheme - returns {"mark_scheme": [...]}
        logger.info(f"Extracting mark scheme from {mark_scheme_path}")
        extracted_mark_scheme = extract_text_from_mark_scheme(mark_scheme_path)
        
        # Extract answer sheets - split_into_qas returns a list of Q&A pairs
        logger.info(f"Extracting {len(answer_sheet_paths)} answer sheets")
        extracted_answer_sheets = []
        for i, answer_sheet_path in enumerate(answer_sheet_paths):
            pages = extract_text_tables(answer_sheet_path)
            qas_list = split_into_qas(pages)  # Returns list of {"question": "...", "answer": [...]}
            
            # Transform the extracted data to match the expected schema
            transformed_answers = []
            for idx, qa in enumerate(qas_list):
                # Extract answer content from the answer array
                answer_content = ""
                if qa.get("answer") and isinstance(qa["answer"], list):
                    for ans_item in qa["answer"]:
                        if isinstance(ans_item, dict) and ans_item.get("type") == "text":
                            answer_content += ans_item.get("content", "")
                        elif isinstance(ans_item, dict) and ans_item.get("type") == "table":
                            # Format table data as readable text
                            table_data = ans_item.get("content", [])
                            if table_data and isinstance(table_data, list):
                                answer_content += "\n[Table]:\n"
                                for row in table_data:
                                    if row:  # Skip empty rows
                                        # Join cells with | separator
                                        row_text = " | ".join(str(cell) if cell else "" for cell in row)
                                        answer_content += row_text + "\n"
                                answer_content += "[End Table]\n"
                
                # Create properly structured answer
                transformed_answer = {
                    "question_number": str(idx + 1),
                    "question_text": qa.get("question", ""),
                    "student_answer": answer_content if answer_content else None
                }
                transformed_answers.append(transformed_answer)
            
            # Wrap in proper structure
            answer_sheet_data = {
                "file_id": f"answer_sheet_{i+1}",
                "filename": answer_sheet_filenames[i] if i < len(answer_sheet_filenames) else f"answer_sheet_{i+1}.pdf",
                "student_name": answer_sheet_filenames[i].replace('.pdf', '').replace('_', ' ') if i < len(answer_sheet_filenames) else f"Student {i+1}",
                "answers": transformed_answers
            }
            extracted_answer_sheets.append(answer_sheet_data)
        
        # Log for debugging
        logger.info(f"Extracted {len(extracted_answer_sheets)} answer sheets")
        question_count = len(extracted_mark_scheme.get('mark_scheme', []))
        logger.info(f"Mark scheme has {question_count} questions")

        # Dynamic batching logic based on number of questions
        total_sheets = len(extracted_answer_sheets)
        logger.info(f"Starting evaluation for {evaluation_id} with {total_sheets} answer sheets")
        
        # Determine batch size based on question count
        if question_count < 15:
            BATCH_SIZE = 10
            logger.info(f"Using batch size 10 for {question_count} questions (< 15)")
        else:
            BATCH_SIZE = 6
            logger.info(f"Using batch size 6 for {question_count} questions (>= 15)")
        
        all_students = []
        
        # Process in batches
        for batch_start in range(0, total_sheets, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_sheets)
            batch_sheets = extracted_answer_sheets[batch_start:batch_end]
            batch_num = (batch_start // BATCH_SIZE) + 1
            
            logger.info(f"Processing batch {batch_num}: sheets {batch_start + 1} to {batch_end}")
            
            if BATCH_SIZE == 10:
                # For batch size 5, process in rounds of 10 sheets max (2 workers * 5 sheets)
                max_sheets_per_round = 10
                logger.info(f"Batch {batch_num}: Processing {len(batch_sheets)} sheets in rounds of max 10")
                round_num = 1
                for round_start in range(0, len(batch_sheets), max_sheets_per_round):
                    round_end = min(round_start + max_sheets_per_round, len(batch_sheets))
                    round_sheets = batch_sheets[round_start:round_end]
                    
                    logger.info(f"Batch {batch_num}, Round {round_num}: Processing {len(round_sheets)} sheets")
                    
                    if len(round_sheets) <= 5:
                        # If 5 or fewer sheets, use single worker
                        logger.info(f"Round {round_num}: Using 1 worker for {len(round_sheets)} sheets")
                        round_data = {"answer_sheets": round_sheets}
                        round_result = evaluate_files_all_in_one(evaluation_id, user_id, extracted_mark_scheme, round_data)
                        all_students.extend(round_result.get("students", []))
                    else:
                        # If more than 5 sheets, split between 2 workers, max 5 sheets each
                        mid_point = len(round_sheets) // 2
                        worker1_sheets = round_sheets[:mid_point]
                        worker2_sheets = round_sheets[mid_point:]
                        
                        # Ensure no worker gets more than 5 sheets
                        if len(worker1_sheets) > 5:
                            worker1_sheets = round_sheets[:5]
                            worker2_sheets = round_sheets[5:]
                        
                        logger.info(f"Round {round_num}: Using 2 workers - Worker 1: {len(worker1_sheets)} sheets, Worker 2: {len(worker2_sheets)} sheets")
                        
                        def evaluate_worker_batch(sheets, worker_num):
                            """Helper function to evaluate sheets in a worker"""
                            logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Started processing {len(sheets)} sheets")
                            if not sheets:
                                logger.warning(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: No sheets to process")
                                return {"students": []}
                            worker_data = {"answer_sheets": sheets}
                            logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Worker data contains {len(worker_data['answer_sheets'])} sheets")
                            result = evaluate_files_all_in_one(evaluation_id, user_id, extracted_mark_scheme, worker_data)
                            logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Completed processing")
                            return result
                        
                        # Use ThreadPoolExecutor with 2 workers for this round
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            future1 = executor.submit(evaluate_worker_batch, worker1_sheets, 1)
                            future2 = executor.submit(evaluate_worker_batch, worker2_sheets, 2)
                            
                            # Get results from both workers
                            result1 = future1.result()
                            result2 = future2.result()
                        
                        # Merge results from both workers in this round
                        round_students = result1.get("students", []) + result2.get("students", [])
                        all_students.extend(round_students)
                        logger.info(f"Batch {batch_num}, Round {round_num}: Completed with {len(round_students)} students")
                    round_num += 1
            else:
                # For batch size 6, process in rounds of 6 sheets max (2 workers * 3 sheets)
                max_sheets_per_round = 6
                logger.info(f"Batch {batch_num}: Processing {len(batch_sheets)} sheets in rounds of max 6")
                round_num = 1
                for round_start in range(0, len(batch_sheets), max_sheets_per_round):
                    round_end = min(round_start + max_sheets_per_round, len(batch_sheets))
                    round_sheets = batch_sheets[round_start:round_end]
                    
                    logger.info(f"Batch {batch_num}, Round {round_num}: Processing {len(round_sheets)} sheets")
                    
                    # Equal split between 2 workers
                    mid_point = len(round_sheets) // 2
                    worker1_sheets = round_sheets[:mid_point]
                    worker2_sheets = round_sheets[mid_point:]
                    
                    logger.info(f"Round {round_num}: Using 2 workers - Worker 1: {len(worker1_sheets)} sheets, Worker 2: {len(worker2_sheets)} sheets")
                    
                    def evaluate_worker_batch(sheets, worker_num):
                        """Helper function to evaluate sheets in a worker"""
                        logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Started processing {len(sheets)} sheets")
                        if not sheets:
                            logger.warning(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: No sheets to process")
                            return {"students": []}
                        worker_data = {"answer_sheets": sheets}
                        logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Worker data contains {len(worker_data['answer_sheets'])} sheets")
                        result = evaluate_files_all_in_one(evaluation_id, user_id, extracted_mark_scheme, worker_data)
                        logger.info(f"Batch {batch_num}, Round {round_num}, Worker {worker_num}: Completed processing")
                        return result
                    
                    # Use ThreadPoolExecutor with 2 workers for this round
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future1 = executor.submit(evaluate_worker_batch, worker1_sheets, 1)
                        future2 = executor.submit(evaluate_worker_batch, worker2_sheets, 2)
                        
                        # Get results from both workers
                        result1 = future1.result()
                        result2 = future2.result()
                    
                    # Merge results from both workers in this round
                    round_students = result1.get("students", []) + result2.get("students", [])
                    all_students.extend(round_students)
                    logger.info(f"Batch {batch_num}, Round {round_num}: Completed with {len(round_students)} students")
                    round_num += 1
        
        # Create final evaluation result with all students
        evaluation_result = {
            "evaluation_id": evaluation_id,
            "students": all_students
        }
        logger.info(f"All batches completed: {len(all_students)} total students processed")
        logger.info(f"Evaluation result: {evaluation_result}")
        logger.info(f"Extracted mark scheme: {extracted_mark_scheme}")
        logger.info(f"Extracted answer sheets: {extracted_answer_sheets}")
        # Verify and recalculate scores for each student
        for student in evaluation_result.get("students", []):
            answers = student.get("answers", [])
            calculated_total = sum((a.get("score") or 0) for a in answers if a.get("score") is not None)
            calculated_max = sum((a.get("max_score") or 0) for a in answers)
            student["total_score"] = calculated_total
            student["max_total_score"] = calculated_max

        # Calculate aggregate totals
        overall_total = sum(s.get("total_score", 0) for s in evaluation_result.get("students", []))
        overall_max = sum(s.get("max_total_score", 0) for s in evaluation_result.get("students", []))
        evaluation_result["total_score"] = overall_total
        evaluation_result["max_total_score"] = overall_max
        
        logger.info(f"Evaluation completed - {len(evaluation_result.get('students', []))} students")
        
        # Save evaluation result to MongoDB
        try:
            update_evaluation_with_result(evaluation_id, evaluation_result)
            logger.info(f"Successfully saved evaluation result for {evaluation_id}")
        except Exception as save_error:
            logger.error(f"Failed to save evaluation result for {evaluation_id}: {str(save_error)}")
            raise save_error
        
        # Extract all feedback from students' answers
        all_feedback = []
        
        # Get answer sheet filenames from evaluation record
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        answer_sheet_filenames = evaluation.get("answer_sheet_filenames", [])
        
        for i, student in enumerate(evaluation_result.get("students", [])):
            # Extract student name from filename
            student_name = "Unknown Student"
            if i < len(answer_sheet_filenames):
                filename = answer_sheet_filenames[i]
                # Remove .pdf extension and extract name before underscore
                if filename.endswith('.pdf'):
                    filename = filename[:-4]  # Remove .pdf
                # Extract name before first underscore (e.g., "Vaibhav Shukla_exam_answers" -> "Vaibhav Shukla")
                if '_' in filename:
                    student_name = filename.split('_')[0]
                else:
                    student_name = filename
            
            student_feedback = {
                "file_id": student.get("file_id"),
                "student_name": student_name,
                "answers_feedback": []
            }
            
            for answer in student.get("answers", []):
                if answer.get("feedback"):
                    student_feedback["answers_feedback"].append({
                        "question_number": answer.get("question_number"),
                        "feedback": answer.get("feedback")
                    })
            
            if student_feedback["answers_feedback"]:  # Only add if there's feedback
                all_feedback.append(student_feedback)
        
        # Save AI feedback to MongoDB
        if all_feedback:
            create_ai_feedback(evaluation_id, {"feedback": all_feedback})
        logger.info(f"AI feedback saved to ai_feedback collection for evaluation {evaluation_id}")
        # Send completion email
        try:
            send_eval_completion_email(evaluation_id, user_id)
            update_evaluation(evaluation_id, {"email_sent": True})
            logger.info(f"Completion email sent for evaluation {evaluation_id}")
        except Exception as email_error:
            logger.error(f"Failed to send completion email for {evaluation_id}: {str(email_error)}")
            # Don't raise - evaluation was successful, email is just notification
        
        # Clean up: Delete temporary files after successful evaluation
        try:
            eval_dir = Path(f"local_storage/temp_evaluations/{evaluation_id}")
            if eval_dir.exists():
                shutil.rmtree(eval_dir)
                logger.info(f"Successfully deleted temporary files for evaluation {evaluation_id}")
            else:
                logger.warning(f"Temporary directory not found for evaluation {evaluation_id}")
        except Exception as cleanup_error:
            logger.error(f"Failed to delete temporary files for evaluation {evaluation_id}: {str(cleanup_error)}")
            # Don't raise the error - evaluation was successful, cleanup is just housekeeping
        
        return evaluation_result
    except Exception as e:
        logger.error(f"Error in _process_evaluation for {evaluation_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Send error email to user
        try:
            send_eval_error_email(evaluation_id, user_id, str(e))
            logger.info(f"Error email sent for evaluation {evaluation_id}")
        except Exception as email_error:
            logger.error(f"Failed to send error email for {evaluation_id}: {str(email_error)}")
            # Don't raise - we still want to clean up files

        # Update evaluation status to failed
        try:
            update_evaluation(evaluation_id, {"status": "failed"})
            logger.info(f"Updated evaluation {evaluation_id} status to failed")
        except Exception as status_error:
            logger.error(f"Failed to update evaluation status for {evaluation_id}: {str(status_error)}")
            # Don't raise - we still want to clean up files

        # Clean up temporary files even on error
        try:
            eval_dir = Path(f"local_storage/temp_evaluations/{evaluation_id}")
            if eval_dir.exists():
                shutil.rmtree(eval_dir)
                logger.info(f"Deleted temporary files after error for evaluation {evaluation_id}")
        except Exception as cleanup_error:
            logger.error(f"Failed to delete temporary files after error: {str(cleanup_error)}")
        
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/evaluation/evaluate-files")
async def evaluate_files(evaluation_id: str, user_id: str):
    try:
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        # If results already exist, return completed immediately (idempotent)
        if "evaluation_result" in evaluation:
            return {
                "evaluation_id": evaluation_id,
                "evaluation_result": evaluation["evaluation_result"]
            }
        
        # Verify files are uploaded
        if not evaluation.get("mark_scheme_path"):
            raise HTTPException(status_code=400, detail="Mark scheme not uploaded")
        
        if not evaluation.get("answer_sheet_paths"):
            raise HTTPException(status_code=400, detail="Answer sheets not uploaded")

        # Mark as processing and start evaluation in background
        update_evaluation(evaluation_id, {"status": "processing"})
        asyncio.create_task(asyncio.to_thread(_process_evaluation, evaluation_id, user_id))
        
        return {
            "evaluation_id": evaluation_id,
            "message": "Evaluation started in background"
        }
        
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting evaluation {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting evaluation: {str(e)}")

@router.put("/evaluation/edit-results")
def edit_results(request: EditresultRequest, user_id: str = Depends(verify_token)):
    try:
        # Update the question score and feedback
        update_question_score_feedback(request.evaluation_id, request.file_id, request.question_number, request.score, request.feedback)
        
        # Get current evaluation to calculate new total score
        evaluation = get_evaluation_by_evaluation_id(request.evaluation_id)
        if evaluation and "evaluation_result" in evaluation:
            for student in evaluation["evaluation_result"].get("students", []):
                if student.get("file_id") == request.file_id:
                    # Calculate new total score
                    total_score = sum(
                        answer.get("score", 0) 
                        for answer in student.get("answers", [])
                        if answer.get("score") is not None
                    )
                    
                    # Update the total score using MongoDB directly with proper positional operator
                    db["evaluations"].update_one(
                        {"evaluation_id": request.evaluation_id, "evaluation_result.students.file_id": request.file_id},
                        {"$set": {"evaluation_result.students.$.total_score": total_score}}
                    )
                    break
        
        # Update evaluation status
        update_evaluation(request.evaluation_id, {"status": "updated"})
        
        return {"message": "Results updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evaluation/status/{evaluation_id}")
def check_evaluation(evaluation_id: str, user_id: str = Depends(verify_token)):
    try:
        logger.info(f"Checking status for evaluation_id: {evaluation_id}")
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        
        if not evaluation:
            logger.warning(f"Evaluation {evaluation_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        logger.info(f"Found evaluation {evaluation_id}, checking for evaluation_result...")
        
        # Check if evaluation failed
        if evaluation.get("status") == "failed":
            logger.info(f"Evaluation {evaluation_id} failed")
            return {
                "status": "failed",
                "message": "Evaluation processing failed. Please try again or contact support.",
                "answer_sheet_filenames": evaluation.get("answer_sheet_filenames", [])
            }
        
        if "evaluation_result" in evaluation:
            logger.info(f"Evaluation {evaluation_id} has results, returning completed status")
            # Trigger completion email once
            try:
                if not evaluation.get("email_sent"):
                    # send_eval_completion_email(evaluation_id, user_id)
                    update_evaluation(evaluation_id, {"email_sent": True})
            except Exception as e:
                logger.error(f"Failed to send completion email for {evaluation_id}: {str(e)}")
            return {
                "status": "completed",
                "evaluation_result": evaluation["evaluation_result"],
                "answer_sheet_filenames": evaluation.get("answer_sheet_filenames", [])
            }
        else:
            logger.info(f"Evaluation {evaluation_id} exists but no evaluation_result yet, returning processing status")
            return {
                "status": "processing",
                "answer_sheet_filenames": evaluation.get("answer_sheet_filenames", [])
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking evaluation status for {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking evaluation status: {str(e)}")

@router.post("/evaluation/save/{evaluation_id}")
def save_evaluation(evaluation_id: str, asset_name: str = Form(...), user_id: str = Depends(verify_token)):
    try:
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # Save a lightweight evaluation asset that references the evaluation_id
        # This enables listing a card and opening the live Evaluation UI by ID
        logger.info(f"Saving evaluation reference {evaluation_id}")
        create_asset(
            course_id=evaluation["course_id"],
            asset_name=asset_name,
            asset_category="evaluation",
            asset_type="evaluation",
            asset_content=evaluation_id,
            asset_last_updated_by="You",
            asset_last_updated_at=datetime.now().strftime("%d %B %Y %H:%M:%S")
        )
        
        return {"message": "Evaluation saved successfully", "asset_name": asset_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving evaluation {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving evaluation: {str(e)}")

def format_evaluation_report(evaluation):
    """Format evaluation data into a readable combined report for all students"""
    result = evaluation["evaluation_result"]
    students = result.get("students", [])
    stored_filenames = evaluation.get("answer_sheet_filenames", [])
    logger.info(f"Stored filenames: {stored_filenames}")
    report = f"# Evaluation Report\n\n"
    report += f"**Total Students:** {len(students)}\n"
    report += f"**Evaluation Date:** {datetime.now().strftime('%d %B %Y')}\n\n"
    
    for i, student in enumerate(students, 1):
        # Use stored filename if available, otherwise fall back to student_name or file_id
        original_filename = "Unknown"
        if i <= len(stored_filenames):
            original_filename = stored_filenames[i-1]
        elif student.get('student_name'):
            original_filename = student.get('student_name')
        elif student.get('file_id'):
            original_filename = f"File_{student.get('file_id')}"
            
        report += f"## Student {i}\n"
        report += f"**File:** {original_filename}\n"
        report += f"**Total Score:** {student.get('total_score', 0)}/{student.get('max_total_score', 0)}\n"
        report += f"**Status:** {student.get('status', 'completed')}\n\n"
        
        answers = student.get('answers', [])
        for j, answer in enumerate(answers, 1):
            report += f"### Question {j}\n"
            report += f"**Question:** {answer.get('question_text', 'N/A')}\n"
            report += f"**Student Answer:** {answer.get('student_answer', 'N/A')}\n"
            report += f"**Score:** {answer.get('score', 0)}/{answer.get('max_score', 0)}\n"
            report += f"**Feedback:** {answer.get('feedback', 'N/A')}\n\n"
        
        report += "---\n\n"
    
    return report

def format_student_report(evaluation, student_index: int):
    """Format evaluation data into a readable report for a single student"""
    result = evaluation["evaluation_result"]
    students = result.get("students", [])
    stored_filenames = evaluation.get("answer_sheet_filenames", [])
    
    if student_index < 0 or student_index >= len(students):
        return None
    
    student = students[student_index]
    
    # Use stored filename if available, otherwise fall back to student_name or file_id
    original_filename = "Unknown"
    if student_index < len(stored_filenames):
        original_filename = stored_filenames[student_index]
    elif student.get('student_name'):
        original_filename = student.get('student_name')
    elif student.get('file_id'):
        original_filename = f"File_{student.get('file_id')}"
    
    report = f"# Student Report\n\n"
    report += f"**Student:** {student_index + 1}\n"
    report += f"**File:** {original_filename}\n"
    report += f"**Total Score:** {student.get('total_score', 0)}/{student.get('max_total_score', 0)}\n"
    report += f"**Status:** {student.get('status', 'completed')}\n"
    report += f"**Evaluation Date:** {datetime.now().strftime('%d %B %Y')}\n\n"
    
    answers = student.get('answers', [])
    for j, answer in enumerate(answers, 1):
        report += f"## Question {j}\n"
        report += f"**Question:** {answer.get('question_text', 'N/A')}\n"
        report += f"**Student Answer:** {answer.get('student_answer', 'N/A')}\n"
        report += f"**Score:** {answer.get('score', 0)}/{answer.get('max_score', 0)}\n"
        report += f"**Feedback:** {answer.get('feedback', 'N/A')}\n\n"
    
    return report

def format_evaluation_csv(evaluation):
    """Format evaluation data into CSV format matching the template structure"""
    result = evaluation["evaluation_result"]
    students = result.get("students", [])
    stored_filenames = evaluation.get("answer_sheet_filenames", [])
    
    # Determine the maximum number of questions across all students
    max_questions = 0
    for student in students:
        answers = student.get('answers', [])
        if len(answers) > max_questions:
            max_questions = len(answers)
    
    # Build CSV header
    header = ["email"]
    for i in range(1, max_questions + 1):
        header.extend([f"Q{i}_score", f"Q{i}_feedback"])
    header.extend(["total_marks", "max_score", "overall_feedback"])
    
    # Build CSV rows
    rows = []
    for idx, student in enumerate(students):
        # Extract email from filename if possible, otherwise use stored filename
        email = ""
        if idx < len(stored_filenames):
            filename = stored_filenames[idx]
            # Remove .pdf extension from filename
            email = filename.replace('.pdf', '') if filename.endswith('.pdf') else filename
        elif student.get('student_name'):
            email = student.get('student_name')
        else:
            email = f"student_{idx + 1}"
        
        row = [email]
        
        # Add question scores and feedback
        answers = student.get('answers', [])
        for i in range(max_questions):
            if i < len(answers):
                answer = answers[i]
                score = answer.get('score', '')
                feedback = answer.get('feedback', '')
                # Clean feedback text - remove newlines and quotes
                if feedback:
                    feedback = str(feedback).replace('\n', ' ').replace('\r', ' ').replace('"', '""')
                row.extend([score if score != '' else '', feedback])
            else:
                # Empty cells for questions this student doesn't have
                row.extend(['', ''])
        
        # Add total marks, max score, and overall feedback
        total_score = student.get('total_score', 0)
        max_total_score = student.get('max_total_score', 0)
        row.extend([total_score, max_total_score, ''])
        
        rows.append(row)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(rows)
    
    return output.getvalue()

@router.get("/evaluation/report/{evaluation_id}")
def get_evaluation_report(evaluation_id: str, user_id: str = Depends(verify_token)):
    """Get combined evaluation report for all students"""
    try:
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        if not evaluation.get("evaluation_result"):
            raise HTTPException(status_code=400, detail="Evaluation not yet completed")
        report = format_evaluation_report(evaluation)
        return {"report": report}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation report for {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting evaluation report: {str(e)}")

@router.get("/evaluation/report/{evaluation_id}/student/{student_index}")
def get_student_report(evaluation_id: str, student_index: int, user_id: str = Depends(verify_token)):
    """Get evaluation report for a specific student by index (0-based)"""
    try:
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        if not evaluation.get("evaluation_result"):
            raise HTTPException(status_code=400, detail="Evaluation not yet completed")
        
        result = evaluation["evaluation_result"]
        students = result.get("students", [])
        
        if student_index < 0 or student_index >= len(students):
            raise HTTPException(
                status_code=404, 
                detail=f"Student index {student_index} not found. Valid range: 0-{len(students)-1}"
            )
        
        report = format_student_report(evaluation, student_index)
        if report is None:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {
            "report": report,
            "student_index": student_index,
            "total_students": len(students)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student report for {evaluation_id}, student {student_index}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting student report: {str(e)}")

@router.get("/evaluation/report/{evaluation_id}/csv")
def download_evaluation_csv(evaluation_id: str, user_id: str = Depends(verify_token)):
    """Download evaluation report as CSV file"""
    try:
        evaluation = get_evaluation_by_evaluation_id(evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        if not evaluation.get("evaluation_result"):
            raise HTTPException(status_code=400, detail="Evaluation not yet completed")
        
        # Generate CSV content
        csv_content = format_evaluation_csv(evaluation)
        
        # Create a streaming response with CSV content
        output = io.BytesIO(csv_content.encode('utf-8'))
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evaluation_report_{evaluation_id[:8]}_{timestamp}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading CSV report for {evaluation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading CSV report: {str(e)}")