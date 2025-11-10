import logging
from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi
from uuid import uuid4

uri = "mongodb+srv://acad:nPyjuhmdeIgTxySD@creators-copilot-demo.aoq6p75.mongodb.net/?retryWrites=true&w=majority&appName=creators-copilot-demo&tls=true&tlsAllowInvalidCertificates=true"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["creators-copilot-demo"]

def add_to_collection(collection_name: str, data: dict):
    collection = db[collection_name]
    collection.insert_one(data)

def get_one_from_collection(collection_name: str, query: dict):
    collection = db[collection_name]
    doc = collection.find_one(query)
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_many_from_collection(collection_name: str, query: dict):
    docs = []
    collection = db[collection_name]
    for doc in collection.find(query):
        # Convert ObjectId to string for JSON serialization
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        docs.append(doc)
    return docs

def update_in_collection(collection_name: str, query: dict, data: dict):
    collection = db[collection_name]
    collection.update_one(query, {"$set": data})

def delete_from_collection(collection_name: str, query: dict):
    collection = db[collection_name]
    collection.delete_one(query)

# Users
def create_user(user_id: str, email: str, display_name: str = None):
    user_data = {"_id": user_id, "email": email}
    if display_name:
        user_data["display_name"] = display_name
    add_to_collection("users", user_data)

def get_user_by_user_id(user_id: str):
    return get_one_from_collection("users", {"_id": user_id})

def get_email_by_user_id(user_id: str):
    user_doc = get_one_from_collection("users", {"_id": user_id})
    if not user_doc:
        return None
    return user_doc.get("email")

# Courses
def create_course(data: dict):
    course_id = str(uuid4())
    add_to_collection("courses", {"_id": course_id, **data})
    return course_id

def get_course(course_id: str):
    return get_one_from_collection("courses", {"_id": course_id})

def get_courses_by_user_id(user_id: str):
    return get_many_from_collection("courses", {"user_id": user_id})

def update_course(course_id: str, data: dict):
    update_in_collection("courses", {"_id": course_id}, data)

def delete_course(course_id: str):
    delete_from_collection("courses", {"_id": course_id})

# Resources
def create_resource(course_id: str, resource_name: str, content: str = None):
    resource_data = {"course_id": course_id, "resource_name": resource_name}
    if content is not None:
        resource_data["content"] = content
    add_to_collection("resources", resource_data)

def get_resources_by_course_id(course_id: str):
    return get_many_from_collection("resources", {"course_id": course_id})

def get_resource_by_course_id_and_resource_name(course_id: str, resource_name: str):
    return get_one_from_collection("resources", {"course_id": course_id, "resource_name": resource_name})

def delete_resource(course_id: str, resource_name: str):
    delete_from_collection("resources", {"course_id": course_id, "resource_name": resource_name})

# Assets
def create_asset(course_id: str, asset_name: str, asset_category: str, asset_type: str, asset_content: str, asset_last_updated_by: str, asset_last_updated_at: str):
    add_to_collection("assets", {"course_id": course_id, "asset_name": asset_name, "asset_category": asset_category, "asset_type": asset_type, "asset_content": asset_content, "asset_last_updated_by": asset_last_updated_by, "asset_last_updated_at": asset_last_updated_at})

def get_assets_by_course_id(course_id: str):
    return get_many_from_collection("assets", {"course_id": course_id})

def get_asset_by_course_id_and_asset_name(course_id: str, asset_name: str):
    return get_one_from_collection("assets", {"course_id": course_id, "asset_name": asset_name})

def get_asset_by_course_id_and_asset_type(course_id: str, asset_type: str):
    return get_one_from_collection("assets", {"course_id": course_id, "asset_type": asset_type})

def get_asset_by_evaluation_id(evaluation_id: str):
    """Get asset that references this evaluation_id"""
    return get_one_from_collection("assets", {"asset_content": evaluation_id, "asset_type": "evaluation"})

def delete_asset_from_db(course_id: str, asset_name: str):
    delete_from_collection("assets", {"course_id": course_id, "asset_name": asset_name})

# Evaluation    
def create_evaluation(evaluation_id: str, course_id: str, evaluation_assistant_id: str, vector_store_id: str, 
                     mark_scheme_path: str = None, mark_scheme_file_id: str = None,
                     answer_sheet_paths: list[str] = None, answer_sheet_file_ids: list[str] = None, 
                     answer_sheet_filenames: list[str] = None):
    """Create evaluation record supporting both local paths and OpenAI file IDs"""
    evaluation = {
        "evaluation_id": evaluation_id, 
        "course_id": course_id,
        "evaluation_assistant_id": evaluation_assistant_id, 
        "vector_store_id": vector_store_id,
        "mark_scheme_path": mark_scheme_path,
        "mark_scheme_file_id": mark_scheme_file_id,
        "answer_sheet_paths": answer_sheet_paths or [],
        "answer_sheet_file_ids": answer_sheet_file_ids or [],
        "answer_sheet_filenames": answer_sheet_filenames or []
    }
    add_to_collection("evaluations", evaluation)
    return evaluation

def get_evaluation_by_evaluation_id(evaluation_id: str):
    return get_one_from_collection("evaluations", {"evaluation_id": evaluation_id})

def get_evaluations_by_course_id(course_id: str):
    return get_many_from_collection("evaluations", {"course_id": course_id})

def update_evaluation(evaluation_id: str, data: dict):
    """Update an evaluation record with new data"""
    logger = logging.getLogger(__name__)
    logger.info(f"Updating evaluation {evaluation_id} with data: {list(data.keys())}")
    update_in_collection("evaluations", {"evaluation_id": evaluation_id}, data)
    
def update_evaluation_with_result(evaluation_id: str, evaluation_result: dict):
    """
    Update an evaluation with the evaluation result.
    Stores the complete evaluation result including all student scores and feedback.
    """
    logger = logging.getLogger(__name__)
    
    # Log the update operation
    students_count = len(evaluation_result.get('students', []))
    logger.info(f"Updating evaluation {evaluation_id} with results for {students_count} students")
    # Store the evaluation result with timestamp
    update_data = {
        "evaluation_result": evaluation_result,
        "evaluation_completed_at": datetime.utcnow().isoformat(),
        "status": "completed"
    }
    
    update_in_collection("evaluations", {"evaluation_id": evaluation_id}, update_data)
    logger.info(f"Successfully updated evaluation {evaluation_id} in MongoDB")

# Minimal helper: update one question's score and feedback

def update_question_score_feedback(evaluation_id: str, file_id: str, question_number: str, score, feedback):
    collection = db["evaluations"]
    
    # First, try the correct array filter approach
    result = collection.update_one(
        {"evaluation_id": evaluation_id},
        {"$set": {
            "evaluation_result.students.$[s].answers.$[a].score": score,
            "evaluation_result.students.$[s].answers.$[a].feedback": feedback
        }},
        array_filters=[
            {"s.file_id": file_id},
            {"a.question_number": {"$in": [question_number, int(question_number)]}}
        ]
    )
    
    # Log the result for debugging
    logger = logging.getLogger(__name__)
    logger.info(f"Updated question {question_number} for file {file_id} in evaluation {evaluation_id}. Modified count: {result.modified_count}")
    
    if result.modified_count == 0:
        logger.warning(f"No questions were updated with array filters. Trying alternative approach...")
        
        # Alternative approach: Update the specific student and answer directly
        try:
            # First, find the evaluation to get the exact structure
            evaluation = collection.find_one({"evaluation_id": evaluation_id})
            if evaluation and "evaluation_result" in evaluation:
                for student_idx, student in enumerate(evaluation["evaluation_result"].get("students", [])):
                    if student.get("file_id") == file_id:
                        # Find the answer index
                        for answer_idx, answer in enumerate(student.get("answers", [])):
                            if str(answer.get("question_number")) == question_number or answer.get("question_number") == int(question_number):
                                # Update using positional operators
                                update_result = collection.update_one(
                                    {"evaluation_id": evaluation_id},
                                    {"$set": {
                                        f"evaluation_result.students.{student_idx}.answers.{answer_idx}.score": score,
                                        f"evaluation_result.students.{student_idx}.answers.{answer_idx}.feedback": feedback
                                    }}
                                )
                                logger.info(f"Alternative update successful. Modified count: {update_result.modified_count}")
                                return
                
                logger.warning(f"Could not find student with file_id {file_id} or question {question_number}")
            else:
                logger.warning(f"Evaluation {evaluation_id} not found or missing evaluation_result")
        except Exception as e:
            logger.error(f"Error in alternative update approach: {str(e)}")
            raise

# Extraction
def create_extracted_data(evaluation_id: str, extracted_data: dict):
    add_to_collection("extracted_data", {"evaluation_id": evaluation_id, "extracted_data": extracted_data})

def get_extracted_data_by_evaluation_id(evaluation_id: str):
    return get_one_from_collection("extracted_data", {"evaluation_id": evaluation_id})

# AI Feedback
def create_ai_feedback(evaluation_id: str, ai_feedback: dict):
    add_to_collection("ai_feedback", {"evaluation_id": evaluation_id, "ai_feedback": ai_feedback})

def get_ai_feedback_by_evaluation_id(evaluation_id: str):
    return get_one_from_collection("ai_feedback", {"evaluation_id": evaluation_id})

def update_ai_feedback(evaluation_id: str, ai_feedback: dict):
    """Update AI feedback in ai_feedback collection"""
    update_in_collection("ai_feedback", {"evaluation_id": evaluation_id}, {"ai_feedback": ai_feedback})