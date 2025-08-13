from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List
import logging
import os
import io
from pathlib import Path
from ..services import openai_service
from ..services.mongo import get_course, get_resources_by_course_id, create_resource, delete_resource as delete_resource_in_db
from ..services.openai_service import create_file, connect_file_to_vector_store
from ..utils.course_pdf_utils import generate_course_pdf
from ..utils.verify_token import verify_token
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Inline models
class ResourceResponse(BaseModel):
    resourceName: str

class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]

class DeleteResponse(BaseModel):
    message: str

class ResourceCreateResponse(BaseModel):
    message: str

def check_course_exists(course_id: str):
    # check if the course exists
    # if it exists, return True
    # if it doesn't exist, raise error
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return True

def create_course_description_file(course_id: str, user_id: str = Depends(verify_token)):
    """
    Create a course description file using PDF utility and add it to vector store
    """
    try:
        # Get course information from MongoDB
        course = get_course(course_id)
        if not course:
            logger.error(f"Course not found: {course_id}")
            return None
        
        # Generate PDF using the utility
        pdf_path = generate_course_pdf(course_id)
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"Failed to generate PDF for course {course_id}")
            return None
        
        # Get relative path starting from 'local_storage'
        pdf_relative_path = Path(pdf_path).as_posix().split("local_storage", 1)[-1]
        pdf_relative_path = "local_storage" + pdf_relative_path
        
        #name of the pdf should be the title
        resource_name = os.path.basename(pdf_path)

        # Create resource in MongoDB
        create_resource(course_id, resource_name)

        # Upload the PDF to OpenAI (open as binary stream)
        with open(pdf_path, "rb") as f:
            content = f.read()
            file_obj = io.BytesIO(content)
            file_obj.name = resource_name  # ✅ Required for OpenAI
            openai_file_id = create_file(file_obj)
        
        # Get vector store for the course
        assistant_id = course.get('assistant_id')
        if not assistant_id:
            logger.error(f"No assistant ID found for course {course_id}")
            return None
        
        # Check if vector store exists, if not create one
        vector_store_id = course.get('vector_store_id')
        if not vector_store_id:
            logger.error(f"No vector_store_id found for course {course_id}")
            return None
        
        # Connect file to vector store
        batch_id = connect_file_to_vector_store(vector_store_id, openai_file_id)
        
        logger.info(f"Created course description PDF for {course_id}: {openai_file_id}")
        logger.info(f"Connected to vector store {vector_store_id}, batch: {batch_id}")
        
        return {
            "file_id": openai_file_id,
            "vector_store_id": vector_store_id,
            "batch_id": batch_id,
            "pdf_path": pdf_path
        }
    except Exception as e:
        logger.error(f"Error creating course description file for {course_id}: {str(e)}")
        return None

# Keep this route, we add the file to the vector store attached to the Assistant
@router.post("/courses/{course_id}/resources", response_model=ResourceCreateResponse)
def upload_resources(course_id: str, files: List[UploadFile] = File(...), user_id: str = Depends(verify_token)):
    try:
        check_course_exists(course_id)
        # if course exists, get the assistant id and vector store id from the course
        course = get_course(course_id)

        # Build a set of existing resource names for collision handling
        existing_resources = get_resources_by_course_id(course_id) or []
        existing_names = set([r.get("resource_name") for r in existing_resources if r.get("resource_name")])

        def ensure_unique_name(filename: str, used: set[str]) -> str:
            base, ext = os.path.splitext(filename or "")
            if not base:
                base = "resource"
            candidate = f"{base}{ext}"
            n = 1
            while candidate in used:
                candidate = f"{base} ({n}){ext}"
                n += 1
            used.add(candidate)
            return candidate

        # Rename duplicates in-place so downstream uses the new name
        for f in files:
            f.filename = ensure_unique_name(f.filename, existing_names)

        # Upload files to vector store (this uses f.filename for the OpenAI file name)
        openai_service.upload_resources(user_id, course_id, course["vector_store_id"], files)

        # Create resource records with the possibly renamed filenames
        for file in files:
            create_resource(course_id, file.filename)

        return ResourceCreateResponse(message="Resources uploaded successfully")
    except Exception as e:
        logger.error(f"Error uploading resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/resources", response_model=ResourceListResponse) 
def list_resources(course_id: str, user_id: str = Depends(verify_token)):
    try:
        check_course_exists(course_id)
        resources = get_resources_by_course_id(course_id)
        resource_list = [
            ResourceResponse(resourceName=data.get("resource_name", "Unknown Name"))
            for data in resources
        ]
        return ResourceListResponse(resources=resource_list)
    except Exception as e:
        logger.error(f"Error listing resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/courses/{course_id}/resources/{resource_name}", response_model=DeleteResponse)
def delete_resource(course_id: str, resource_name: str, user_id: str = Depends(verify_token)):
    try:    
        check_course_exists(course_id)
        delete_resource_in_db(course_id, resource_name)
        return DeleteResponse(message="Resource deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/courses/{course_id}/resources/{resource_name}/view")
# def view_resource(course_id: str, resource_name: str, user_id: str = Depends(verify_token)):
#     # 1. Check course exists
#     check_course_exists(course_id)
#     # 2. Check resource exists
#     resources = get_resources_by_course_id(course_id)
#     if not resources:
#         raise HTTPException(status_code=404, detail="Resource not found")
#     resource = next((r for r in resources if r.get("resource_name") == resource_name), None)
#     if not resource:
#         raise HTTPException(status_code=404, detail="Resource not found")
#     # 3. Find file path
#     path_to_file = resource.get("file_path")
#     if not path_to_file:
#         raise HTTPException(status_code=404, detail="File path not found")
#     # 4. Return FileResponse
#     return FileResponse(path_to_file, filename=resource_name)

# @router.get("/courses/{course_id}/resources/{resource_name}/download")
# def download_resource(course_id: str, resource_name: str, user_id: str = Depends(verify_token)):
#     check_course_exists(course_id)
#     resources = get_resources_by_course_id(course_id)
#     if not resources:
#         raise HTTPException(status_code=404, detail="Resource not found")
#     resource = next((r for r in resources if r.get("resource_name") == resource_name), None)
#     if not resource:
#         raise HTTPException(status_code=404, detail="Resource not found")
#     path_to_file = resource.get("file_path")
#     if not path_to_file:
#         raise HTTPException(status_code=404, detail="File path not found")
#     return FileResponse(path_to_file, filename=resource_name, media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename={resource_name}"})