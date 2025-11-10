import json
import re
import logging
import markdown
from fastapi import HTTPException
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..utils.openai_client import client
from ..config.settings import settings
import uuid
from app.services.mongo import (
    get_course, 
    get_assets_by_course_id,
    get_asset_by_course_id_and_asset_name
)

logger = logging.getLogger(__name__)

def fetch_course_data(course_id: str, user_id: str) -> Dict[str, Any]:
    """
    Fetch all data for a given course and user ID from MongoDB
    Returns a formatted dictionary with all course information
    """
    try:
        # Step 1: Get basic course information
        course = get_course(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Verify user access
        if course.get("user_id") != user_id:
            raise ValueError("User does not have access to this course")
        
        # Step 2: Get all related data
        assets = get_assets_by_course_id(course_id)
        
        # Step 3: Format the data according to the required structure
        formatted_data = format_course_data(course, assets)
        
        return formatted_data
        
    except Exception as e:
        raise Exception(f"Error fetching course data: {str(e)}")

# fuction which will take course_id asset name, asset type and give the json output of the details of that from mongo db
def get_asset_details(course_id, asset_name):
    asset = get_asset_by_course_id_and_asset_name(course_id, asset_name)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_details = {
        "asset_name": asset["asset_name"],
        "asset_type": asset["asset_type"],
        "asset_category": asset["asset_category"],
        "asset_content": asset["asset_content"],
        "asset_last_updated_by": asset["asset_last_updated_by"],
        "asset_last_updated_at": asset["asset_last_updated_at"]
    }
    return asset_details

def format_course_data(course: Dict, assets: List[Dict]) -> Dict[str, Any]:
    """
    Format the raw course data into a simple structure with course info and all assets
    """
    formatted_data = {
        "course_info": {
            "course_id": course.get("_id"),
            "course_name": course.get("name", ""),
            "description": course.get("description", ""),
            "user_id": course.get("user_id"),
            "settings": course.get("settings", {}),
            "created_at": course.get("created_at", ""),
            "updated_at": course.get("updated_at", "")
        },
        "assets": []
    }

    # Include assessment assets (projects, activities, quizzes, question papers, mark schemes, mock interviews)
    assessment_types = {"project", "activity", "quiz", "question-paper", "mark-scheme", "mock-interview"}
    assessment_assets = [asset for asset in assets if asset.get("asset_type") in assessment_types]
    for asset in assessment_assets:
        asset_data = {
            "asset_id": asset.get("_id"),
            "asset_name": asset.get("asset_name", ""),
            "asset_type": asset.get("asset_type", ""),
            "asset_category": asset.get("asset_category", ""),
            "asset_content": asset.get("asset_content", ""),
            "last_updated_by": asset.get("asset_last_updated_by", ""),
            "last_updated_at": asset.get("asset_last_updated_at", ""),
            "course_id": asset.get("course_id", "")
        }
        formatted_data["assets"].append(asset_data)

    return formatted_data


def get_formatted_course_data(course_id: str, user_id: str) -> str:
    """
    Main function to get formatted course data as JSON string
    """
    try:
        data = fetch_course_data(course_id, user_id)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

def get_formatted_course_data_dict(course_id: str, user_id: str) -> Dict[str, Any]:
    """
    Alternative function that returns the formatted data as a dictionary instead of JSON string
    """
    try:
        return fetch_course_data(course_id, user_id)
    except Exception as e:
        return {"error": str(e)}

# Example usage function (for testing purposes)
def example_usage():
    """
    Example of how to use the data formatting functions
    """
    # Example course_id and user_id
    course_id = "example-course-id"
    user_id = "example-user-id"
    
    try:
        # Get formatted data as JSON string
        json_data = get_formatted_course_data(course_id, user_id)
        print("JSON formatted data:")
        print(json_data)
        
        # Get formatted data as dictionary
        dict_data = get_formatted_course_data_dict(course_id, user_id)
        print("\nDictionary formatted data:")
        print(dict_data)
        
    except Exception as e:
        print(f"Error: {e}")

def format_quiz_content(course_id: str, asset_name: str):
    """
    Format quiz content using OpenAI structured output
    """
    # Get the quiz content from mongo
    asset = get_asset_by_course_id_and_asset_name(course_id, asset_name)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_name}' not found")
    
    asset_content = asset.get("asset_content", "")
    
    # Get the assistant from mongo 
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    
    assistant_id = course.get("assistant_id", "")
    
    # Prepare the prompt
    system_prompt = """You are a quiz formatting assistant. Your task is to take quiz content (which may be in various formats) and convert it into a well-structured JSON format.

Extract or infer the following:
- A clear title for the quiz
- A brief description of what the quiz covers
- Estimated time in hours (contentHours) to complete the quiz
- All questions with their options, correct answer index, marks, and explanations

Guidelines:
- Each question should have multiple choice options in an array
- correctOptionIndex is 0-based (0 for first option, 1 for second, etc.)
- If marks are not specified, default to 1 mark per question
- Provide helpful explanations for each answer
- Ensure options are clear and distinct"""

    user_prompt = f"Please format the following quiz content into the required JSON structure:\n\n{asset_content}"
    if asset_name:
        user_prompt = f"Quiz: {asset_name}\n\n" + user_prompt
    
    # Use chat completions with structured output
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "quiz_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the quiz"
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of what the quiz covers"
                        },
                        "contentHours": {
                            "type": "number",
                            "description": "Estimated time in hours to complete the quiz"
                        },
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The question text"
                                    },
                                    "options": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "description": "Array of answer options"
                                    },
                                    "correctOptionIndex": {
                                        "type": "integer",
                                        "description": "0-based index of the correct answer"
                                    },
                                    "marks": {
                                        "type": "number",
                                        "description": "Points for this question"
                                    },
                                    "explanation": {
                                        "type": "string",
                                        "description": "Explanation of the correct answer"
                                    }
                                },
                                "required": ["question", "options", "correctOptionIndex", "marks", "explanation"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["title", "description", "contentHours", "questions"],
                    "additionalProperties": False
                }
            }
        }
    )
    
    # Parse the response
    structured_output = response.choices[0].message.content
    
    if not structured_output:
        raise HTTPException(status_code=500, detail="No content returned from OpenAI")
    
    # Parse JSON
    try:
        quiz_data = json.loads(structured_output)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse quiz JSON: {structured_output}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {str(e)}")
    
    # Convert markdown to HTML for quiz fields that may contain markdown
    if 'description' in quiz_data and isinstance(quiz_data['description'], str):
        quiz_data['description'] = markdown.markdown(
            quiz_data['description'],
            extensions=['markdown.extensions.fenced_code', 'markdown.extensions.nl2br']
        )
    
    # Convert markdown in questions, options, and explanations
    if 'questions' in quiz_data and isinstance(quiz_data['questions'], list):
        for question in quiz_data['questions']:
            if 'question' in question and isinstance(question['question'], str):
                question['question'] = markdown.markdown(
                    question['question'],
                    extensions=['markdown.extensions.fenced_code', 'markdown.extensions.nl2br']
                )
            if 'explanation' in question and isinstance(question['explanation'], str):
                question['explanation'] = markdown.markdown(
                    question['explanation'],
                    extensions=['markdown.extensions.fenced_code', 'markdown.extensions.nl2br']
                )
            # Convert markdown in options
            if 'options' in question and isinstance(question['options'], list):
                question['options'] = [
                    markdown.markdown(opt, extensions=['markdown.extensions.fenced_code', 'markdown.extensions.nl2br']) 
                    if isinstance(opt, str) else opt 
                    for opt in question['options']
                ]
        logger.info("Converted markdown to HTML in quiz content")
    
    logger.info(f"Successfully formatted quiz with {len(quiz_data.get('questions', []))} questions")
    return quiz_data

def format_activity_content(course_id: str, asset_name: str):
    """
    Format activity content using OpenAI structured output
    """
    # Get the activity content from mongo
    asset = get_asset_by_course_id_and_asset_name(course_id, asset_name)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_name}' not found")
    
    asset_content = asset.get("asset_content", "")
    
    # Get the assistant from mongo 
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    
    assistant_id = course.get("assistant_id", "")
    
    # Prepare the prompt    
    system_prompt = """You are an activity formatting assistant. Your task is to take activity content (which may be in various formats) and convert it into a well-structured JSON format compatible with the LMS assignment payload.

Extraction & Inference Rules:
payload.title → A clear, concise title for the activity.
payload.description → A brief summary of what the activity covers.
payload.content → The main instructional or task content.
payload.submissionOptions → Suggested submission methods (e.g., ["file", "link"]).
Use ["file"] as a default if unspecified.
payload.deadline → Include only if clearly stated or inferable, in ISO 8601 format.
payload.contentHours → Estimated time to complete the activity.
If not specified or inferable, set to 60 (representing 60 minutes).
This field must always be present.
payload.rubrics → Include structured rubrics if explicitly mentioned or inferable; otherwise, omit this key entirely or use an empty array ([]).
type → Always "assignment".
isLocked → Always false.
isGraded → Always true.

Guidelines:
Do not invent deadlines or rubrics unless clearly implied.
Be strictly JSON-compliant — no explanations or extra text.
Ensure all keys and structure match the schema above exactly.
"""

    user_prompt = f"Please format the following activity content into the required JSON structure:\n\n{asset_content}"
    if asset_name:
        user_prompt = f"Activity: {asset_name}\n\n" + user_prompt
    
    # Use chat completions with structured output
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "activity_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "The type of activity"
                        },
                        "payload": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The title of the activity"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "A brief description of the activity"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The main content or text of the activity"
                                },
                                "submissionOptions": {
                                    "type": "array",
                                    "items": { "type": "string" },
                                    "description": "Submission methods supported (e.g., file, link)"
                                },
                                "deadline": {
                                    "type": ["string", "null"],
                                    "description": "ISO 8601 deadline if available"
                                },
                                "rubrics": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": { "type": "string" },
                                            "name": { "type": "string" },
                                            "description": { "type": "string" },
                                            "maxScore": { "type": "number" },
                                            "criteria": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": { "type": "string" },
                                                        "name": { "type": "string" },
                                                        "description": { "type": "string" },
                                                        "maxPoints": { "type": "number" },
                                                        "levels": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "id": { "type": "string" },
                                                                    "name": { "type": "string" },
                                                                    "description": { "type": "string" },
                                                                    "points": { "type": "number" }
                                                                },
                                                                "required": ["id", "name", "description", "points"],
                                                                "additionalProperties": False
                                                            }
                                                        }
                                                    },
                                                    "required": ["id", "name", "description", "maxPoints", "levels"],
                                                    "additionalProperties": False
                                                }
                                            }
                                        },
                                        "required": ["id", "name", "description", "maxScore", "criteria"],
                                        "additionalProperties": False
                                    },
                                    "description": "Rubric definition for grading"
                                },
                                "contentHours": {
                                    "type": ["number", "null"],
                                    "description": "Estimated time to complete in hours"
                                }
                            },
                            "required": [
                                "title",
                                "description",
                                "content",
                                "submissionOptions",
                                "deadline",
                                "rubrics",
                                "contentHours"
                            ],
                            "additionalProperties": False
                        },
                        "isLocked": {
                            "type": "boolean",
                            "description": "Indicates whether the activity is locked for editing (default: false)"
                        },
                        "isGraded": {
                            "type": "boolean",
                            "description": "Indicates whether the activity is graded (default: true for assignments)"
                        }
                    },
                    "required": ["type", "payload", "isLocked", "isGraded"],
                    "additionalProperties": False
                }
            }
        }
    )
    
    # Parse the response
    structured_output = response.choices[0].message.content
    
    if not structured_output:
        raise HTTPException(status_code=500, detail="No content returned from OpenAI")
    
    # Parse JSON
    try:
        activity_data = json.loads(structured_output)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse activity JSON: {structured_output}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {str(e)}")
    
    # Ensure payload is an object, not a string
    if isinstance(activity_data.get('payload'), str):
        try:
            activity_data['payload'] = json.loads(activity_data['payload'])
            logger.warning("Payload was a string, converted to object")
        except:
            logger.error(f"Failed to parse payload string: {activity_data.get('payload')}")
    
    # Ensure boolean fields are actual booleans
    if 'isLocked' in activity_data:
        activity_data['isLocked'] = bool(activity_data['isLocked'])
    if 'isGraded' in activity_data:
        activity_data['isGraded'] = bool(activity_data['isGraded'])
    
    # Set a more appropriate type if it's generic
    if activity_data.get('type') in ['object', 'activity', '']:
        activity_data['type'] = 'assignment'  # Default to assignment activity
    
    # For assignment type activities, ensure isGraded is true by default
    if activity_data.get('type') == 'assignment':
        if 'isGraded' not in activity_data or activity_data['isGraded'] is None:
            activity_data['isGraded'] = True
        if 'isLocked' not in activity_data or activity_data['isLocked'] is None:
            activity_data['isLocked'] = False
    
    # Fill sensible defaults and attempt to extract rubric from any markdown table present in the original content
    try:
        # Defaults for submission options and content hours
        if isinstance(activity_data.get('payload'), dict):
            payload = activity_data['payload']
            if 'submissionOptions' not in payload or not isinstance(payload.get('submissionOptions'), list):
                payload['submissionOptions'] = ["file"]
            # Do not invent deadline; leave as-is if not present
            if 'contentHours' in payload and payload['contentHours'] is None:
                del payload['contentHours']

        def _extract_rubric_from_markdown(md_text: str) -> Optional[List[Dict[str, Any]]]:
            """
            Parse a markdown table under a section likely named 'Assessment Rubric' and convert
            it into the expected rubrics structure.

            Expected table headers example:
            | Criterion | Exemplary | Proficient | Developing | Beginning | Points |
            """
            if not isinstance(md_text, str) or '|' not in md_text:
                return None

            # Find rubric section start heuristically
            lower = md_text.lower()
            section_start = max(lower.find("assessment rubric"), lower.find("rubric"))
            scan_text = md_text[section_start:] if section_start != -1 else md_text

            # Extract the first markdown table from the scan_text
            lines = [l.strip() for l in scan_text.splitlines() if l.strip()]
            table_lines: List[str] = []
            in_table = False
            for line in lines:
                if line.startswith('|') and line.endswith('|'):
                    table_lines.append(line)
                    in_table = True
                else:
                    if in_table:
                        break
            if len(table_lines) < 2:
                return None

            # Parse headers (first line) and separator (second line)
            def _split_row(row: str) -> List[str]:
                # Remove leading/trailing pipe and split
                cells = [c.strip() for c in row.strip('|').split('|')]
                return cells

            headers = _split_row(table_lines[0])
            # Basic validation: need at least Criterion and Points columns
            try:
                criterion_idx = headers.index('Criterion') if 'Criterion' in headers else headers.index('Criteria')
            except ValueError:
                # Look for case-insensitive match
                criterion_idx = next((i for i, h in enumerate(headers) if h.lower() in ['criterion', 'criteria']), -1)
            points_idx = next((i for i, h in enumerate(headers) if h.lower() in ['points', 'score', 'max points', 'weight', 'weightage']), -1)
            if criterion_idx == -1 or points_idx == -1:
                return None

            # Level columns are the rest between criterion and points
            level_indices = [i for i in range(len(headers)) if i not in [criterion_idx, points_idx]]
            level_headers = [headers[i] for i in level_indices]
            if not level_headers:
                return None

            # Parse data rows (skip header and separator)
            data_rows = [r for r in table_lines[2:]] if len(table_lines) >= 3 else []
            if not data_rows:
                return None

            criteria_list: List[Dict[str, Any]] = []

            def _parse_points(value: str) -> float:
                v = value.strip()
                if v.endswith('%'):
                    try:
                        return float(v[:-1])
                    except:
                        return 0.0
                try:
                    return float(v)
                except:
                    return 0.0

            for row in data_rows:
                cells = _split_row(row)
                # Align mismatched cell counts
                if len(cells) < len(headers):
                    cells += [''] * (len(headers) - len(cells))
                name = cells[criterion_idx]
                max_points = _parse_points(cells[points_idx])
                # Distribute level points descending as a simple heuristic
                if len(level_headers) >= 4:
                    scale = [1.0, 0.75, 0.5, 0.25] + [0.0] * (len(level_headers) - 4)
                else:
                    # If fewer levels, split equally descending
                    step = 1.0 / max(1, len(level_headers))
                    scale = [1.0 - i * step for i in range(len(level_headers))]
                levels = []
                for idx, li in enumerate(level_indices):
                    level_name = headers[li]
                    level_desc = cells[li]
                    level_points = round(max_points * max(0.0, scale[idx]), 2)
                    levels.append({
                        "id": f"level-{uuid.uuid4().hex[:8]}",
                        "name": level_name,
                        "description": level_desc,
                        "points": level_points
                    })
                criteria_list.append({
                    "id": f"criteria-{uuid.uuid4().hex[:8]}",
                    "name": name,
                    "description": name,
                    "maxPoints": max_points,
                    "levels": levels
                })

            rubric = [{
                "id": f"rubric-{uuid.uuid4().hex[:8]}",
                "name": "Assessment Rubric",
                "description": "Generated from activity rubric table",
                "maxScore": 100,
                "criteria": criteria_list
            }]
            return rubric

        extracted_rubrics = _extract_rubric_from_markdown(asset_content)
        if extracted_rubrics:
            if isinstance(activity_data.get('payload'), dict):
                activity_data['payload']['rubrics'] = extracted_rubrics
    except Exception as e:
        logger.warning(f"Failed to extract rubric table: {e}")

    # Convert markdown content to HTML for proper rendering in LMS
    if isinstance(activity_data.get('payload'), dict):
        payload = activity_data['payload']
        if 'content' in payload and isinstance(payload['content'], str):
            # Convert markdown to HTML with extensions for better formatting
            html_content = markdown.markdown(
                payload['content'],
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.tables',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.sane_lists'
                ]
            )
            payload['content'] = html_content
            logger.info("Converted markdown content to HTML")
    
    logger.info(f"Successfully formatted activity: {activity_data.get('payload', {}).get('title', 'Unknown')}")
    logger.info(f"Activity data structure - type: {activity_data.get('type')}, payload type: {type(activity_data.get('payload'))}, isLocked: {activity_data.get('isLocked')}, isGraded: {activity_data.get('isGraded')}")
    return activity_data

def format_lecture_content(course_id: str, asset_name: str):
    """
    Format lecture content using OpenAI structured output
    """
    # Get the lecture content from mongo
    asset = get_asset_by_course_id_and_asset_name(course_id, asset_name)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_name}' not found")
    
    asset_content = asset.get("asset_content", "")
    
    # Get the assistant from mongo 
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    
    assistant_id = course.get("assistant_id", "")
    
    # Prepare the prompt    
    system_prompt = """You are a lecture formatting assistant. Your task is to take lecture content (which may be in various formats) and convert it into a well-structured JSON format compatible with the LMS lecture payload.

Extraction & Inference Rules:
payload.title → A clear, concise title for the lecture.
payload.description → A brief summary of what the lecture covers.
payload.videoUrl → Video URL if specified; otherwise, use an empty string ("").
payload.durationSeconds → Duration in seconds if specified; otherwise, infer from content or default to 3600 (1 hour).
payload.transcript → The full lecture content, transcript, or outline.
payload.links → Array of link objects with "url" and "description" fields if any references are mentioned; otherwise, use an empty array ([]).
payload.contentHours → Estimated lecture duration in minutes (e.g., 90 for 90 minutes).
If not specified, calculate from durationSeconds or default to 1.
type → Always "lecture".
isLocked → Always false.
isGraded → Always false.

Guidelines:
Do not invent URLs or links unless clearly implied or stated in the content.
Be strictly JSON-compliant — no explanations or extra text.
Ensure all keys and structure match the schema above exactly.
Extract any mentioned resources or reference materials as links.
"""

    user_prompt = f"Please format the following lecture content into the required JSON structure:\n\n{asset_content}"
    if asset_name:
        user_prompt = f"Lecture: {asset_name}\n\n" + user_prompt
    
    # Use chat completions with structured output
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "lecture_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "The type of activity - always 'lecture'"
                        },
                        "payload": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The title of the lecture"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "A brief description of the lecture"
                                },
                                "videoUrl": {
                                    "type": "string",
                                    "description": "URL to the video if available, empty string otherwise"
                                },
                                "durationSeconds": {
                                    "type": "number",
                                    "description": "Duration of the lecture in seconds"
                                },
                                "transcript": {
                                    "type": "string",
                                    "description": "The lecture transcript or content"
                                },
                                "links": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "URL of the resource"
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Description of the resource"
                                            }
                                        },
                                        "required": ["url", "description"],
                                        "additionalProperties": False
                                    },
                                    "description": "Array of reference links and resources"
                                },
                                "contentHours": {
                                    "type": "number",
                                    "description": "Estimated lecture duration in hours"
                                }
                            },
                            "required": [
                                "title",
                                "description",
                                "videoUrl",
                                "durationSeconds",
                                "transcript",
                                "links",
                                "contentHours"
                            ],
                            "additionalProperties": False
                        },
                        "isLocked": {
                            "type": "boolean",
                            "description": "Indicates whether the lecture is locked for editing (default: false)"
                        },
                        "isGraded": {
                            "type": "boolean",
                            "description": "Indicates whether the lecture is graded (default: false for lectures)"
                        }
                    },
                    "required": ["type", "payload", "isLocked", "isGraded"],
                    "additionalProperties": False
                }
            }
        }
    )
    
    # Parse the response
    structured_output = response.choices[0].message.content
    
    if not structured_output:
        raise HTTPException(status_code=500, detail="No content returned from OpenAI")
    
    # Parse JSON
    try:
        lecture_data = json.loads(structured_output)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse lecture JSON: {structured_output}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {str(e)}")
    
    # Ensure payload is an object, not a string
    if isinstance(lecture_data.get('payload'), str):
        try:
            lecture_data['payload'] = json.loads(lecture_data['payload'])
            logger.warning("Payload was a string, converted to object")
        except:
            logger.error(f"Failed to parse payload string: {lecture_data.get('payload')}")
    
    # Ensure boolean fields are actual booleans
    if 'isLocked' in lecture_data:
        lecture_data['isLocked'] = bool(lecture_data['isLocked'])
    if 'isGraded' in lecture_data:
        lecture_data['isGraded'] = bool(lecture_data['isGraded'])
    
    # Ensure type is 'lecture'
    lecture_data['type'] = 'lecture'
    
    # For lecture type, ensure isGraded is false and isLocked is false by default
    if 'isGraded' not in lecture_data or lecture_data['isGraded'] is None:
        lecture_data['isGraded'] = False
    if 'isLocked' not in lecture_data or lecture_data['isLocked'] is None:
        lecture_data['isLocked'] = False
    
    # Validate and set defaults for payload fields
    if isinstance(lecture_data.get('payload'), dict):
        payload = lecture_data['payload']
        
        # Ensure videoUrl is a string
        if 'videoUrl' not in payload or payload['videoUrl'] is None:
            payload['videoUrl'] = ""
        
        # Ensure durationSeconds has a default
        if 'durationSeconds' not in payload or payload['durationSeconds'] is None:
            payload['durationSeconds'] = 3600  # 1 hour default
        
        # Ensure links is an array
        if 'links' not in payload or not isinstance(payload.get('links'), list):
            payload['links'] = []
        
        # Calculate contentHours from durationSeconds if not present
        if 'contentHours' not in payload or payload['contentHours'] is None:
            payload['contentHours'] = payload.get('durationSeconds', 3600) / 3600.0
    
    logger.info(f"Successfully formatted lecture: {lecture_data.get('payload', {}).get('title', 'Unknown')}")
    logger.info(f"Lecture data structure - type: {lecture_data.get('type')}, payload type: {type(lecture_data.get('payload'))}, isLocked: {lecture_data.get('isLocked')}, isGraded: {lecture_data.get('isGraded')}")
    return lecture_data