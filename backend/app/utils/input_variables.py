from ..services.storage_course import storage_service
from typing import Dict, Any, Optional

# This function gathers all input variables needed for prompt generation
# It fetches course info, settings, and resource file names, and merges with any user-provided variables

def gather_input_variables(course_id: str, user_id: Optional[str] = None, thread_id: Optional[str] = None, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Gather all input variables needed for prompt generation.
    - course_id: ID of the course
    - user_id: ID of the user (optional, for access control)
    - thread_id: If asset-level resources are needed
    - user_input: Any user-provided variables (overrides defaults)
    Returns a dict with all variables needed for prompt rendering.
    """
    course = storage_service.get_course(course_id, user_id)
    if not course:
        raise ValueError(f"Course {course_id} not found or unauthorized.")

    # Gather course info
    input_vars = {}
    input_vars["course_name"] = course.get("name", "Unknown Course")
    input_vars["course_level"] = course.get("level", "Unknown Level")
    input_vars["study_area"] = course.get("settings", {}).get("study_area", "Unknown Study Area")
    input_vars["pedagogical_components"] = course.get("settings", {}).get("pedagogical_components", [])
    input_vars["ask_clarifying_questions"] = course.get("settings", {}).get("ask_clarifying_questions", False)

    # Gather resource file names (checked-in files)
    resources = storage_service.get_resources(course_id, thread_id=thread_id, user_id=user_id)
    print("[gather_input_variables] Resources fetched:", resources)
    file_names = [r.get("title", r.get("fileName", "Unknown file")) for r in resources if r.get("status") == "checked_in"]
    input_vars["file_names"] = file_names

    # Merge with user-provided variables (user_input takes precedence)
    if user_input:
        input_vars.update(user_input)

    return input_vars 