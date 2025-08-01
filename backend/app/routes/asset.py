import asyncio
from openai import AssistantEventHandler
from typing_extensions import override
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
from ..utils.verify_token import verify_token
from ..utils.prompt_parser import PromptParser
from ..utils.openai_client import client, async_client
import logging
from ..services.mongo import get_course, create_asset, get_assets_by_course_id

logger = logging.getLogger(__name__)
router = APIRouter()

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

class AssetChatStreamHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()  # ✅ This is the fix
        self.response_text = ""

    @override
    def on_text_delta(self, delta, snapshot):
        self.response_text += delta.value   

async def stream_assistant_response(thread_id: str, assistant_id: str):
    logger.info(f"Starting stream for thread {thread_id}, assistant {assistant_id}")
    stream = async_client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
    async with stream as stream:
        async for text in stream.text_deltas:
            yield f"data: {text}\n\n" 

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
async def create_asset_chat(course_id: str, asset_type_name: str, request: AssetRequest, user_id: str = "CUXuu3Xw5jgM8sYE8Pn2OZM7tHY2"):
    try:
        logger.info(f"Creating asset chat for course {course_id}, asset type {asset_type_name}")
        course = get_course(course_id)
        if not course or "assistant_id" not in course:
            raise HTTPException(status_code=404, detail="Course or assistant not found")

        assistant_id = course["assistant_id"]
        # Prepare prompt
        input_variables = construct_input_variables(course, request.file_names)
        parser = PromptParser()
        prompt = parser.get_asset_prompt(asset_type_name, input_variables)
        logger.info(f"Prepared prompt for asset.")

        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        logger.info(f"Created thread {thread.id} for asset chat")
        return StreamingResponse(
            stream_assistant_response(thread.id, assistant_id), 
            media_type="text/event-stream",
            headers={"X-Thread-ID": thread.id}
        )

    except Exception as e:
        logger.error(f"Exception in create_asset for asset '{asset_type_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/courses/{course_id}/asset_chat/{asset_name}", response_model=AssetResponse)
def continue_asset_chat(course_id: str, asset_name: str, thread_id: str, request: AssetPromptRequest, user_id: str = "CUXuu3Xw5jgM8sYE8Pn2OZM7tHY2"):
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

        return AssetResponse(response=handler.response_text, thread_id=thread_id)

    except Exception as e:
        logger.error(f"Exception in continue_asset for asset '{asset_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/assets", response_model=AssetCreateResponse)
def save_asset(course_id: str, asset_name: str, asset_type: str, request: AssetCreateRequest, user_id: str = "CUXuu3Xw5jgM8sYE8Pn2OZM7tHY2"):
    # TODO: Make this a configuration for the app overall, add the remaining categories and asset types here
    category_map = {
        "course-outcomes": "curriculum"
    }
    asset_category = category_map.get(asset_type)
    if not asset_category:
        raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
    create_asset(course_id, asset_name, asset_category, asset_type, request.content, "You", datetime.now().strftime("%d %B %Y %H:%M:%S"))
    return AssetCreateResponse(message=f"Asset '{asset_name}' created successfully")

@router.get("/courses/{course_id}/assets", response_model=AssetListResponse)
def get_assets(course_id: str, user_id: str = "CUXuu3Xw5jgM8sYE8Pn2OZM7tHY2"):
    assets = get_assets_by_course_id(course_id)
    return AssetListResponse(assets=assets)