from fastapi import APIRouter
from services.openai_service import call_openai, chat_revise_prompt

router = APIRouter()

@router.post("/chat_revise")
async def chat_revise(body: dict):
    instruction = body.get("instruction")
    course_data = body.get("course_data")
    prompt = chat_revise_prompt(course_data, instruction)
    result = call_openai(prompt)
    return {"result": result}
