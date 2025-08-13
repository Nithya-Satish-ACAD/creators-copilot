import os
import tempfile
import json
import pytest
from app.utils.prompt_parser import PromptParser

@pytest.fixture
def sample_prompt_json():
    return {
        "prompt": "Hello, {{ name }}! Your age is {{ age }}. {{ extra|default('') }}",
        "required_input_variables": ["name", "age"],
        "optional_input_variables": ["extra"]
    }

@pytest.fixture
def temp_prompt_file(sample_prompt_json):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        json.dump(sample_prompt_json, f)
        f.flush()
        yield f.name
    os.remove(f.name)

def test_render_prompt_success(temp_prompt_file):
    parser = PromptParser()
    result = parser.render_prompt(temp_prompt_file, {"name": "Alice", "age": 30})
    assert "Hello, Alice! Your age is 30." in result

def test_render_prompt_with_optional(temp_prompt_file):
    parser = PromptParser()
    result = parser.render_prompt(temp_prompt_file, {"name": "Bob", "age": 25, "extra": "Welcome!"})
    assert "Hello, Bob! Your age is 25. Welcome!" in result

def test_render_prompt_missing_required(temp_prompt_file):
    parser = PromptParser()
    with pytest.raises(ValueError) as exc:
        parser.render_prompt(temp_prompt_file, {"name": "Charlie"})
    assert "Missing required input variables" in str(exc.value) 