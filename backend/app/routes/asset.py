import logging
from openai import AssistantEventHandler
from typing_extensions import override
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from ..utils.verify_token import verify_token
from ..utils.prompt_parser import PromptParser
from ..utils.openai_client import client
from ..services.mongo import get_course, create_asset, get_assets_by_course_id, get_asset_by_course_id_and_asset_name
from ..services.openai_service import clean_text

logger = logging.getLogger(__name__)
router = APIRouter()

class AssetViewResponse(BaseModel):
    asset_name: str
    asset_type: str
    asset_category: str
    asset_content: str
    asset_last_updated_by: str
    asset_last_updated_at: str

class AssetPromptRequest(BaseModel):
    user_prompt: str

class AssetRequest(BaseModel):
    file_names: list[str]

class AssetResponse(BaseModel):
    response: str
    thread_id: str

class AssetCreateResponse(BaseModel):
    message: str

class AssetCreateRequest(BaseModel):
    content: str

class Asset(BaseModel):
    asset_name: str
    asset_type: str
    asset_category: str
    asset_content: str
    asset_last_updated_by: str
    asset_last_updated_at: str

class AssetListResponse(BaseModel):
    assets: list[Asset]

class ImageRequest(BaseModel):
    prompt: str

class ImageResponse(BaseModel):
    image_url: str

class AssetChatStreamHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()  # ✅ This is the fix
        self.response_text = ""

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        self.response_text += delta.value
        

def construct_input_variables(course: dict, file_names: list[str]) -> dict:
    input_variables = {
        "course_name": course.get("name", ""),
        "course_level": course.get("settings", {}).get("course_level", ""),
        "study_area": course.get("settings", {}).get("study_area", ""),
        "pedagogical_components": course.get("settings", {}).get("pedagogical_components", ""),
        "ask_clarifying_questions": course.get("settings", {}).get("ask_clarifying_questions", ""),
        "file_names": file_names
    }
    return input_variables

@router.post("/courses/{course_id}/asset_chat/{asset_type_name}", response_model=AssetResponse)
async def create_asset_chat(course_id: str, asset_type_name: str, request: AssetRequest, user_id: str = Depends(verify_token)):
    try:
        course = get_course(course_id)
        if not course or "assistant_id" not in course:
            raise HTTPException(status_code=404, detail="Course or assistant not found")

        assistant_id = course["assistant_id"]

        # Prepare prompt
        input_variables = construct_input_variables(course, request.file_names)
        parser = PromptParser()
        prompt = parser.get_asset_prompt(asset_type_name, input_variables)
        logger.info(f"Prompt for asset '{asset_type_name}': {prompt}")

        # Create a new thread
        thread = client.beta.threads.create()
        thread_id = thread.id

        # Send message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

        # Stream run
        handler = AssetChatStreamHandler()
        with client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=handler
        ) as stream:
            stream.until_done()

        # Get complete response from thread messages
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        complete_response = latest_message.content[0].text.value

        return AssetResponse(response=complete_response, thread_id=thread_id)

    except Exception as e:
        logger.error(f"Exception in create_asset for asset '{asset_type_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/courses/{course_id}/asset_chat/{asset_name}", response_model=AssetResponse)
def continue_asset_chat(course_id: str, asset_name: str, thread_id: str, request: AssetPromptRequest, user_id: str = Depends(verify_token)):
    try:
        course = get_course(course_id)
        if not course or "assistant_id" not in course:
            raise HTTPException(status_code=404, detail="Course or assistant not found")
        assistant_id = course["assistant_id"]

        # Send user prompt to the thread
        message_response = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.user_prompt
        )

        # Create and stream the run
        handler = AssetChatStreamHandler()
        with client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=handler
        ) as stream:
            stream.until_done()

        # Get complete response from thread messages
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        complete_response = latest_message.content[0].text.value
        
        return AssetResponse(response=complete_response, thread_id=thread_id)

    except Exception as e:
        logger.error(f"Exception in continue_asset for asset '{asset_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/assets", response_model=AssetCreateResponse)
def save_asset(course_id: str, asset_name: str, asset_type: str, request: AssetCreateRequest, user_id: str = Depends(verify_token)):
    # TODO: Make this a configuration for the app overall, add the remaining categories and asset types here
    category_map = {
        "brainstorm": "curriculum",
        "course-outcomes": "curriculum",
        "modules-topics": "curriculum",
        "lesson-plans": "curriculum",
        "concept-map": "curriculum",
        "course-notes": "curriculum",
        "project": "assessments",
        "activity": "assessments",
        "quiz": "assessments",
        "question-paper": "assessments",
        "mock-interview": "assessments",
    }
    # Default to a safe category so saving never fails due to unmapped type
    asset_category = category_map.get(asset_type, "content")
    #this text should go to openai and get cleaned up and than use the text to create the asset
    cleaned_text = clean_text(request.content)
    try:
        create_asset(course_id, asset_name, asset_category, asset_type, cleaned_text, "You", datetime.now().strftime("%d %B %Y %H:%M:%S"))
    except ValueError as e:
        # Duplicate asset name or other validation errors
        raise HTTPException(status_code=409, detail=str(e))
    return AssetCreateResponse(message=f"Asset '{asset_name}' created successfully")

@router.get("/courses/{course_id}/assets", response_model=AssetListResponse)
def get_assets(course_id: str, user_id: str = Depends(verify_token)):
    assets = get_assets_by_course_id(course_id)
    return AssetListResponse(assets=assets)

@router.get("/courses/{course_id}/assets/{asset_name}/view", response_model=AssetViewResponse)
def view_asset(course_id: str, asset_name: str, user_id: str = Depends(verify_token)):
    asset = get_asset_by_course_id_and_asset_name(course_id, asset_name)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetViewResponse(
        asset_name=asset["asset_name"], 
        asset_type=asset["asset_type"], 
        asset_category=asset["asset_category"], 
        asset_content=asset["asset_content"], 
        asset_last_updated_by=asset["asset_last_updated_by"], 
        asset_last_updated_at=asset["asset_last_updated_at"]
    )

@router.post("/courses/{course_id}/assets/image", response_model=ImageResponse)
def create_image(course_id: str, asset_type_name: str, user_id: str = Depends(verify_token)):
    course = get_course(course_id)
    if not course or "assistant_id" not in course:
        raise HTTPException(status_code=404, detail="Course or assistant not found")

    input_variables = construct_input_variables(course, [])
    parser = PromptParser()
    prompt = parser.get_asset_prompt(asset_type_name, input_variables)

    image = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )

    # Extract URL
    image_url = image.data[0].url

    return ImageResponse(image_url=image_url)


