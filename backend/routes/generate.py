from fastapi import APIRouter
from models.course import CourseRequest
from services.openai_service import generate_course_prompt, call_openai

router = APIRouter()

@router.post("/generate_course")
async def generate_course(data: CourseRequest):
    try:
        print("Received data:", data)
        prompt = generate_course_prompt(data)
        print("Generated prompt:\n", prompt[:200])
        result = call_openai(prompt)
        return {"result": result}
    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
