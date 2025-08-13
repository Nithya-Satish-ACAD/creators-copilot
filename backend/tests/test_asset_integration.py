import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.openai_client import client
import tempfile

client_api = TestClient(app)

@pytest.mark.integration
def test_asset_file_search_retrieval():
    # Step 1: Create an Assistant with file_search enabled
    assistant = client.beta.assistants.create(
        name="Test Assistant for File Search",
        instructions="You are a helpful assistant that answers questions using attached files.",
        model="gpt-4-turbo",  # or your default model
        tools=[{"type": "file_search"}]
    )
    assistant_id = assistant.id

    # Step 2: Upload a nonsense file to the Assistant's vector store
    nonsense_phrase = "blorptastic123"
    file_content = f"This is a test file. The secret code is: {nonsense_phrase}."
    with tempfile.NamedTemporaryFile(delete=False, mode="w+t") as tmp:
        tmp.write(file_content)
        tmp.flush()
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        openai_file = client.files.create(file=f, purpose="assistants")
    os.unlink(tmp_path)
    # Attach file to Assistant
    client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={
            "file_search": {"vector_stores": [{"file_ids": [openai_file.id]}]}
        }
    )

    # Step 3: Use this Assistant to create an asset using the test_asset prompt
    course_id = "test-course-asset"  # Use a test/dummy course
    asset_name = "test_asset"        # Uses the test prompt template
    input_variables = {
        "query": "What is the secret code in the attached file?"
    }
    response = client_api.post(
        f"/api/courses/{course_id}/assets/{asset_name}",
        json={"input_variables": input_variables}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # Step 4: Assert the nonsense phrase is in the response
    assert nonsense_phrase in data["response"], f"Expected '{nonsense_phrase}' in response: {data['response']}" 