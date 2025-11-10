from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel
from ..services.mongo import get_course, get_asset_by_course_id_and_asset_name
from ..utils.data_formating import format_quiz_content, format_activity_content, format_lecture_content
from ..utils.verify_token import verify_token
from ..utils.lms_curl import login_to_lms, get_lms_courses, get_all_modules, post_quiz_data_to_lms, post_activity_data_to_lms, post_lecture_data_to_lms, link_activity_to_course, create_lms_module
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ExportLMSRequest(BaseModel):
    asset_type: list[str]
    asset_names: list[str]

class LoginLMSRequest(BaseModel):
    email: str
    password: str

class GoogleLoginLMSRequest(BaseModel):
    email: str

class GetCoursesLMSRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header

class GetModulesLMSRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    lms_course_id: str  # The ID of the course to get modules for

class CreateModuleLMSRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    lms_course_id: str  # The ID of the course to create module in
    module_title: str  # The title of the module to create
    order: int = 1  # The order of the module (defaults to 1)

class PostQuizRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    course_id: str  # Course ID in our system (to get quiz data)
    asset_name: str  # Name of the quiz asset to export
    lms_course_id: str  # LMS course ID (destination)
    lms_module_id: str  # LMS module ID (destination)
    order: int = 0  # Order of the activity in the module (optional, defaults to 0)

class PostActivityRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    course_id: str  # Course ID in our system (to get activity data)
    asset_name: str  # Name of the activity asset to export
    lms_course_id: str  # LMS course ID (destination)
    lms_module_id: str  # LMS module ID (destination)
    order: int = 0  # Order of the activity in the module (optional, defaults to 0)

class PostLectureRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    course_id: str  # Course ID in our system (to get lecture data)
    asset_name: str  # Name of the lecture asset to export
    lms_course_id: str  # LMS course ID (destination)
    lms_module_id: str  # LMS module ID (destination)
    order: int = 0  # Order of the lecture in the module (optional, defaults to 0)

class PostAssetRequest(BaseModel):
    lms_cookies: str  # LMS authentication cookies from Set-Cookie header
    course_id: str  # Course ID in our system (to get asset data)
    asset_name: str  # Name of the asset to export
    asset_type: str  # Type of asset (quiz, activity, project, etc.)
    lms_course_id: str  # LMS course ID (destination)
    lms_module_id: str  # LMS module ID (destination)
    order: int = 0  # Order of the activity in the module (optional, defaults to 0)

class ExportToModuleRequest(BaseModel):
    asset_names: list[str]  # List of asset names to export
    asset_type: list[str]  # List of asset types
    lms_cookies: str  # LMS authentication cookies
    lms_course_id: str  # LMS course ID (destination)
    lms_module_id: str  # LMS module ID (destination)

def post_quiz_to_lms(request: PostQuizRequest, user_id: str=Depends(verify_token)):
    """
    Post quiz data to the LMS platform and link it to course/module
    
    This endpoint:
    1. Gets the quiz asset from MongoDB
    2. Formats it using OpenAI into the LMS-compatible structure
    3. Posts it to the LMS platform
    4. Links the activity to the specified course and module
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        if not request.course_id:
            raise HTTPException(status_code=400, detail="Course ID is required")
        if not request.asset_name:
            raise HTTPException(status_code=400, detail="Asset name is required")
        if not request.lms_course_id:
            raise HTTPException(status_code=400, detail="LMS course ID is required")
        if not request.lms_module_id:
            raise HTTPException(status_code=400, detail="LMS module ID is required")
        
        logger.info(f"User {user_id} posting quiz '{request.asset_name}' to LMS course {request.lms_course_id}")
        
        # Step 1: Format the quiz content using OpenAI
        formatted_quiz_data = format_quiz_content(
            course_id=request.course_id,
            asset_name=request.asset_name
        )
        
        logger.info(f"Formatted quiz data: {formatted_quiz_data.get('title', 'Unknown')}")
        
        # Step 2: Post the formatted quiz to LMS
        result = post_quiz_data_to_lms(
            lms_cookies=request.lms_cookies,
            quiz_data=formatted_quiz_data
        )
        
        # Check if request was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("error", "Failed to post quiz to LMS")
            )
        
        logger.info(f"Successfully posted quiz '{request.asset_name}' to LMS")
        
        # Step 3: Extract activity ID from response and link to course/module
        activity_data = result.get("data", {})
        
        # Log the full response for debugging
        logger.info(f"Full quiz response data: {activity_data}")
        
        # Extract activity ID - try multiple possible locations
        activity_id = None
        # First, check if response has nested "activity" object with "id"
        if isinstance(activity_data, dict) and "activity" in activity_data:
            activity_id = activity_data.get("activity", {}).get("id")
        # Fall back to top-level ID fields
        if not activity_id:
            activity_id = activity_data.get("id") or activity_data.get("activityId") or activity_data.get("_id")
        
        if not activity_id:
            logger.warning(f"No activity ID found in response. Available keys: {list(activity_data.keys()) if isinstance(activity_data, dict) else 'Not a dict'}")
            return {
                "message": "Successfully posted quiz to LMS (but could not link - no activity ID returned)",
                "quiz_data": activity_data
            }
        
        logger.info(f"Linking activity {activity_id} to course {request.lms_course_id}, module {request.lms_module_id}")
        
        # Link the activity to the course and module
        link_result = link_activity_to_course(
            lms_cookies=request.lms_cookies,
            lms_course_id=request.lms_course_id,
            lms_module_id=request.lms_module_id,
            lms_activity_id=str(activity_id),
            order=request.order
        )
        
        # Check if linking was successful
        if not link_result.get("success"):
            logger.error(f"Failed to link activity: {link_result.get('error')}")
            # Return success for posting but warn about linking failure
            return {
                "message": "Quiz posted successfully but failed to link to course/module",
                "quiz_data": activity_data,
                "link_error": link_result.get("error")
            }
        
        logger.info(f"Successfully linked activity to course/module")
        
        # Return complete success response
        return {
            "message": "Successfully posted quiz to LMS and linked to course/module",
            "quiz_data": activity_data,
            "link_data": link_result.get("data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting quiz to LMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def post_activity_to_lms(request: PostActivityRequest, user_id: str=Depends(verify_token)):
    """
    Post activity data to the LMS platform and link it to course/module
    
    This endpoint:
    1. Gets the activity asset from MongoDB
    2. Formats it using OpenAI into the LMS-compatible structure
    3. Posts it to the LMS platform
    4. Links the activity to the specified course and module
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        if not request.course_id:
            raise HTTPException(status_code=400, detail="Course ID is required")
        if not request.asset_name:
            raise HTTPException(status_code=400, detail="Asset name is required")
        if not request.lms_course_id:
            raise HTTPException(status_code=400, detail="LMS course ID is required")
        if not request.lms_module_id:
            raise HTTPException(status_code=400, detail="LMS module ID is required")
        
        logger.info(f"User {user_id} posting activity '{request.asset_name}' to LMS course {request.lms_course_id}")
        
        # Step 1: Format the activity content using OpenAI
        formatted_activity_data = format_activity_content(
            course_id=request.course_id,
            asset_name=request.asset_name
        )
        
        logger.info(f"Formatted activity data: {formatted_activity_data.get('payload', {}).get('title', 'Unknown')}")
        
        # Step 2: Post the formatted activity to LMS
        result = post_activity_data_to_lms(
            lms_cookies=request.lms_cookies,
            activity_data=formatted_activity_data
        )
        
        # Check if request was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("error", "Failed to post activity to LMS")
            )
        
        logger.info(f"Successfully posted activity '{request.asset_name}' to LMS")
        
        # Step 3: Extract activity ID from response and link to course/module
        activity_data = result.get("data", {})
        
        # Log the full response for debugging
        logger.info(f"Full activity response data: {activity_data}")
        
        # Extract activity ID - try multiple possible locations
        activity_id = None
        # First, check if response has nested "activity" object with "id"
        if isinstance(activity_data, dict) and "activity" in activity_data:
            activity_id = activity_data.get("activity", {}).get("id")
        # Fall back to top-level ID fields
        if not activity_id:
            activity_id = activity_data.get("id") or activity_data.get("activityId") or activity_data.get("_id")
        
        if not activity_id:
            logger.warning(f"No activity ID found in response. Available keys: {list(activity_data.keys()) if isinstance(activity_data, dict) else 'Not a dict'}")
            return {
                "message": "Successfully posted activity to LMS (but could not link - no activity ID returned)",
                "activity_data": activity_data
            }
        
        logger.info(f"Linking activity {activity_id} to course {request.lms_course_id}, module {request.lms_module_id}")
        
        # Link the activity to the course and module
        link_result = link_activity_to_course(
            lms_cookies=request.lms_cookies,
            lms_course_id=request.lms_course_id,
            lms_module_id=request.lms_module_id,
            lms_activity_id=str(activity_id),
            order=request.order
        )
        
        # Check if linking was successful
        if not link_result.get("success"):
            logger.error(f"Failed to link activity: {link_result.get('error')}")
            # Return success for posting but warn about linking failure
            return {
                "message": "Activity posted successfully but failed to link to course/module",
                "activity_data": activity_data,
                "link_error": link_result.get("error")
            }
        
        logger.info(f"Successfully linked activity to course/module")
        
        # Return complete success response
        return {
            "message": "Successfully posted activity to LMS and linked to course/module",
            "activity_data": activity_data,
            "link_data": link_result.get("data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting activity to LMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def post_lecture_to_lms(request: PostLectureRequest, user_id: str=Depends(verify_token)):
    """
    Post lecture data to the LMS platform and link it to course/module
    
    This endpoint:
    1. Gets the lecture asset from MongoDB
    2. Formats it using OpenAI into the LMS-compatible structure
    3. Posts it to the LMS platform
    4. Links the activity to the specified course and module
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        if not request.course_id:
            raise HTTPException(status_code=400, detail="Course ID is required")
        if not request.asset_name:
            raise HTTPException(status_code=400, detail="Asset name is required")
        if not request.lms_course_id:
            raise HTTPException(status_code=400, detail="LMS course ID is required")
        if not request.lms_module_id:
            raise HTTPException(status_code=400, detail="LMS module ID is required")
        
        logger.info(f"User {user_id} posting lecture '{request.asset_name}' to LMS course {request.lms_course_id}")
        
        # Step 1: Format the lecture content using OpenAI
        formatted_lecture_data = format_lecture_content(
            course_id=request.course_id,
            asset_name=request.asset_name
        )
        
        logger.info(f"Formatted lecture data: {formatted_lecture_data.get('payload', {}).get('title', 'Unknown')}")
        
        # Step 2: Post the formatted lecture to LMS
        result = post_lecture_data_to_lms(
            lms_cookies=request.lms_cookies,
            lecture_data=formatted_lecture_data
        )
        
        # Check if request was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("error", "Failed to post lecture to LMS")
            )
        
        logger.info(f"Successfully posted lecture '{request.asset_name}' to LMS")
        
        # Step 3: Extract activity ID from response and link to course/module
        activity_data = result.get("data", {})
        
        # Log the full response for debugging
        logger.info(f"Full lecture response data: {activity_data}")
        
        # Extract activity ID - try multiple possible locations
        activity_id = None
        # First, check if response has nested "activity" object with "id"
        if isinstance(activity_data, dict) and "activity" in activity_data:
            activity_id = activity_data.get("activity", {}).get("id")
        # Fall back to top-level ID fields
        if not activity_id:
            activity_id = activity_data.get("id") or activity_data.get("activityId") or activity_data.get("_id")
        
        if not activity_id:
            logger.warning(f"No activity ID found in response. Available keys: {list(activity_data.keys()) if isinstance(activity_data, dict) else 'Not a dict'}")
            return {
                "message": "Successfully posted lecture to LMS (but could not link - no activity ID returned)",
                "lecture_data": activity_data
            }
        
        logger.info(f"Linking activity {activity_id} to course {request.lms_course_id}, module {request.lms_module_id}")
        
        # Link the activity to the course and module
        link_result = link_activity_to_course(
            lms_cookies=request.lms_cookies,
            lms_course_id=request.lms_course_id,
            lms_module_id=request.lms_module_id,
            lms_activity_id=str(activity_id),
            order=request.order
        )
        
        # Check if linking was successful
        if not link_result.get("success"):
            logger.error(f"Failed to link activity: {link_result.get('error')}")
            # Return success for posting but warn about linking failure
            return {
                "message": "Lecture posted successfully but failed to link to course/module",
                "lecture_data": activity_data,
                "link_error": link_result.get("error")
            }
        
        logger.info(f"Successfully linked activity to course/module")
        
        # Return complete success response
        return {
            "message": "Successfully posted lecture to LMS and linked to course/module",
            "lecture_data": activity_data,
            "link_data": link_result.get("data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting lecture to LMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
#route to login to the lms
@router.post("/login-lms")
def login_lms(request: LoginLMSRequest, user_id: str=Depends(verify_token)):
    """
    Login to the LMS platform with user credentials
    
    Returns authentication cookies that must be used for subsequent LMS requests.
    """
    try:
        # Validate input
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        # Call the LMS login utility function
        result = login_to_lms(request.email, request.password)
        
        # Check if login was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 401),
                detail=result.get("error", "LMS authentication failed")
            )
        
        logger.info(f"User {user_id} successfully logged into LMS")
        
        # Return the success response with cookies from Set-Cookie header
        return {
            "message": "Successfully logged into LMS",
            "data": result.get("data", {}),
            "cookies": result.get("cookies", ""),  # Cookies for session-based auth
            "token": result.get("token")  # Keep for backward compatibility if API also returns token
        }
        
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during LMS login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


#route to get the courses from the lms
@router.post("/courses-lms")
def get_courses_lms(request: GetCoursesLMSRequest, user_id: str=Depends(verify_token)):
    """
    Get courses from the LMS platform using session cookies from login
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        
        # Check if LMS_BASE_URL is configured in settings
        if not settings.LMS_BASE_URL:
            raise HTTPException(status_code=500, detail="LMS base URL is not configured in server settings")
        
        # Log cookie info (first few characters only for security)
        logger.info(f"Using LMS cookies to fetch courses: {request.lms_cookies[:50]}...")
        
        # Call the LMS courses utility function with the cookies
        result = get_lms_courses(request.lms_cookies)
        
        # Check if request was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("error", "Failed to fetch courses from LMS")
            )
        
        logger.info(f"User {user_id} successfully fetched courses from LMS")
        
        # Normalize and down-select fields: only return id and name
        raw_data = result.get("data", [])
        courses_list = []
        if isinstance(raw_data, list):
            for course in raw_data:
                if not isinstance(course, dict):
                    continue
                course_id = (
                    course.get("id") or course.get("_id") or course.get("course_id") or course.get("uuid")
                )
                course_name = course.get("name") or course.get("title") or course.get("course_title")
                if course_id is None and course_name is None:
                    # Skip malformed item
                    continue
                courses_list.append({
                    "id": course_id,
                    "name": course_name or str(course_id) or "Unnamed Course"
                })
        else:
            logger.warning("Unexpected LMS courses payload; expected list, got %s", type(raw_data))

        # Return the success response
        return {
            "message": "Successfully fetched courses from LMS",
            "data": courses_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LMS courses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
#route to get all modules for a course
@router.post("/modules-lms")
def get_modules_lms(request: GetModulesLMSRequest, user_id: str=Depends(verify_token)):
    """
    Get all modules for a course from the LMS platform using authentication cookies
    """
    try:
        result = get_all_modules(request.lms_cookies, request.lms_course_id)
        
        # Filter to only include id and name fields
        if result.get("success") and "data" in result:
            filtered_data = [
                {"id": module.get("id"), "name": module.get("name")}
                for module in result["data"]
            ]
            return {
                "data": filtered_data 
            }
        
        # If not successful, return error with proper status code
        error_message = result.get("error", "Failed to fetch modules from LMS")
        status_code = result.get("status_code", 500)
        
        raise HTTPException(
            status_code=status_code if status_code != 200 else 500,
            detail=error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_modules_lms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#route to create a module in LMS
@router.post("/create-module-lms")
def create_module_lms(request: CreateModuleLMSRequest, user_id: str=Depends(verify_token)):
    """
    Create a new module in the LMS platform using authentication cookies
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        if not request.lms_course_id:
            raise HTTPException(status_code=400, detail="LMS course ID is required")
        if not request.module_title:
            raise HTTPException(status_code=400, detail="Module title is required")
        
        logger.info(f"User {user_id} creating module '{request.module_title}' in LMS course {request.lms_course_id}")
        
        # Call the LMS module creation utility function
        result = create_lms_module(
            lms_cookies=request.lms_cookies,
            lms_course_id=request.lms_course_id,
            module_title=request.module_title,
            order=request.order
        )
        
        # Check if request was successful
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("error", "Failed to create module in LMS")
            )
        
        logger.info(f"User {user_id} successfully created module in LMS")
        
        # Return the success response with module data
        return {
            "message": "Successfully created module in LMS",
            "data": result.get("data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating module in LMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#post asset to lms which will take the asset name and type and use the function to post to lms
@router.post("/post-asset-to-lms")
def post_asset_to_lms_endpoint(request: PostAssetRequest, user_id: str=Depends(verify_token)):
    """
    Post asset to the LMS platform based on asset type
    
    This is a generic endpoint that routes to specific asset handlers:
    - quiz: posts quiz and links to course/module
    - activity: posts activity and links to course/module
    - lecture: posts lecture and links to course/module
    """
    try:
        # Validate input
        if not request.asset_name:
            raise HTTPException(status_code=400, detail="Asset name is required")
        if not request.asset_type:
            raise HTTPException(status_code=400, detail="Asset type is required")
        
        logger.info(f"User {user_id} posting {request.asset_type} '{request.asset_name}' to LMS")
        
        # Define supported asset types
        SUPPORTED_ASSET_TYPES = ['quiz', 'activity', 'lecture']
        
        # Check if asset type is supported
        if request.asset_type not in SUPPORTED_ASSET_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Asset type '{request.asset_type}' is not supported for export. Supported types: {', '.join(SUPPORTED_ASSET_TYPES)}"
            )
        
        # Route to appropriate handler based on asset type
        if request.asset_type == "quiz":
            # Create PostQuizRequest from PostAssetRequest
            quiz_request = PostQuizRequest(
                lms_cookies=request.lms_cookies,
                course_id=request.course_id,
                asset_name=request.asset_name,
                lms_course_id=request.lms_course_id,
                lms_module_id=request.lms_module_id,
                order=request.order
            )
            # Call the quiz posting function
            return post_quiz_to_lms(quiz_request, user_id)
        
        elif request.asset_type == "activity":
            # Create PostActivityRequest from PostAssetRequest
            activity_request = PostActivityRequest(
                lms_cookies=request.lms_cookies,
                course_id=request.course_id,
                asset_name=request.asset_name,
                lms_course_id=request.lms_course_id,
                lms_module_id=request.lms_module_id,
                order=request.order
            )
            # Call the activity posting function
            return post_activity_to_lms(activity_request, user_id)
        
        elif request.asset_type == "lecture":
            # Create PostLectureRequest from PostAssetRequest
            lecture_request = PostLectureRequest(
                lms_cookies=request.lms_cookies,
                course_id=request.course_id,
                asset_name=request.asset_name,
                lms_course_id=request.lms_course_id,
                lms_module_id=request.lms_module_id,
                order=request.order
            )
            # Call the lecture posting function
            return post_lecture_to_lms(lecture_request, user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting asset to LMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#route to export multiple assets to an LMS module
@router.post("/courses/{course_id}/export-to-lms-module")
def export_multiple_assets_to_module(course_id: str, request: ExportToModuleRequest, user_id: str=Depends(verify_token)):
    """
    Export multiple assets to a specific LMS module
    
    This endpoint processes multiple assets at once and returns detailed status for each.
    Supported asset types: quiz, activity, lecture
    """
    try:
        # Validate input
        if not request.lms_cookies:
            raise HTTPException(status_code=400, detail="LMS authentication cookies are required")
        if not request.lms_course_id:
            raise HTTPException(status_code=400, detail="LMS course ID is required")
        if not request.lms_module_id:
            raise HTTPException(status_code=400, detail="LMS module ID is required")
        if not request.asset_names or len(request.asset_names) == 0:
            raise HTTPException(status_code=400, detail="At least one asset must be selected")
        
        logger.info(f"User {user_id} exporting {len(request.asset_names)} assets to LMS module {request.lms_module_id}")
        
        # Define supported asset types
        SUPPORTED_ASSET_TYPES = ['quiz', 'activity', 'lecture']
        
        results = []
        unsupported_assets = []
        
        # Process each asset
        for i, asset_name in enumerate(request.asset_names):
            asset_type_val = request.asset_type[i] if i < len(request.asset_type) else 'unknown'
            
            # Check if asset type is supported
            if asset_type_val not in SUPPORTED_ASSET_TYPES:
                logger.warning(f"Unsupported asset type '{asset_type_val}' for asset '{asset_name}'")
                unsupported_assets.append({
                    "asset_name": asset_name,
                    "asset_type": asset_type_val,
                    "reason": f"Asset type '{asset_type_val}' is not supported for export. Supported types: {', '.join(SUPPORTED_ASSET_TYPES)}"
                })
                continue
            
            try:
                # Use the single asset endpoint
                asset_request = PostAssetRequest(
                    lms_cookies=request.lms_cookies,
                    course_id=course_id,
                    asset_name=asset_name,
                    asset_type=asset_type_val,
                    lms_course_id=request.lms_course_id,
                    lms_module_id=request.lms_module_id,
                    order=i
                )
                
                # Call the single asset posting function
                result = post_asset_to_lms_endpoint(asset_request, user_id)
                
                # Extract relevant info from result
                results.append({
                    "asset_name": asset_name,
                    "asset_type": asset_type_val,
                    "status": "success",
                    "message": result.get("message", "Success")
                })
                    
            except HTTPException as he:
                logger.error(f"Error exporting asset '{asset_name}': {he.detail}")
                results.append({
                    "asset_name": asset_name,
                    "asset_type": asset_type_val,
                    "status": "failed",
                    "error": he.detail
                })
            except Exception as e:
                logger.error(f"Error exporting asset '{asset_name}': {str(e)}")
                results.append({
                    "asset_name": asset_name,
                    "asset_type": asset_type_val,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Prepare response
        success_count = len([r for r in results if r["status"] == "success"])
        failed_count = len([r for r in results if r["status"] == "failed"])
        unsupported_count = len(unsupported_assets)
        
        response_message = f"Export complete: {success_count} succeeded, {failed_count} failed"
        if unsupported_count > 0:
            response_message += f", {unsupported_count} unsupported"
        
        logger.info(f"Export completed for user {user_id}: {response_message}")
        
        return {
            "message": response_message,
            "data": {
                "exported_assets": results,
                "unsupported_assets": unsupported_assets,
                "summary": {
                    "total": len(request.asset_names),
                    "success": success_count,
                    "failed": failed_count,
                    "unsupported": unsupported_count
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in export_multiple_assets_to_module: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")