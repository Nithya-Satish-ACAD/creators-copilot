from fastapi import APIRouter, UploadFile, File
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # Save temporarily
    with open(file.filename, "wb") as f:
        f.write(contents)

    try:
        openai_file = openai.File.create(
            file=open(file.filename, "rb"),
            purpose="assistants"
        )

        os.remove(file.filename)

        return {
            "file_id": openai_file["id"],
            "filename": file.filename
        }

    except Exception as e:
        return {"error": str(e)}
