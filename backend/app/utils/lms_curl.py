import requests
import logging
import json
from typing import Dict, Any
from ..config.settings import settings

logger = logging.getLogger(__name__)

def login_to_lms(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate with the LMS platform using email and password
    Matches curl: curl --location 'learnx-dev.atriauniversity.in/api/v1/auth/signin'
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/auth/signin"
    
    payload = {
        "email": email,
        "password": password
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        logger.info(f"Attempting LMS login at {url} with email: {email}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        logger.info(f"LMS Response Status: {response.status_code}")
        logger.info(f"LMS Response Headers: {dict(response.headers)}")
        
        # Get response data
        response_data = response.json()
        logger.info(f"LMS Response Keys: {list(response_data.keys())}")
        
        # Check if successful
        if response.status_code == 200:
            # Extract cookies from Set-Cookie header
            cookies = response.headers.get('Set-Cookie', '')
            logger.info(f"Login successful! Set-Cookie header: {cookies[:100]}...")
            
            # Also check for token in response body (some APIs use both)
            token = response_data.get('token') or response_data.get('accessToken')
            if token:
                logger.info(f"Also found token in response: {token[:30]}...")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data,
                "cookies": cookies,
                "token": token  # Keep this for backward compatibility
            }
        else:
            # Non-200 status code
            error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail') or 'Authentication failed'
            logger.error(f"LMS login failed: {error_msg}")
            logger.error(f"Full response: {response_data}")
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg,
                "data": response_data
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to LMS at {url}")
        return {
            "success": False,
            "error": "Request timeout - LMS server took too long to respond",
            "status_code": 408
        }
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to LMS at {url}: {str(e)}")
        return {
            "success": False,
            "error": "Connection error - Could not connect to LMS server",
            "status_code": 503
        }
    
    except Exception as e:
        logger.error(f"Unexpected error during LMS login: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def get_lms_courses(lms_cookies: str) -> Dict[str, Any]:
    """
    Get courses from the LMS platform using authentication cookies
    
    Args:
        lms_cookies: Cookie string from Set-Cookie header (session-based auth)
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/course"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies  # Use Cookie header for session-based auth
    }
    
    try:
        logger.info(f"Fetching courses from LMS at {url}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        
        response = requests.get(url, headers=headers, timeout=30)
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = { "message": response.text }
        
        if response.status_code == 200:
            logger.info(f"Fetched courses successfully!")
            # Normalize to a list of courses regardless of LMS response shape
            normalized: Any
            if isinstance(response_data, list):
                normalized = response_data
            elif isinstance(response_data, dict):
                # Common keys that may contain the array
                for key in ["data", "courses", "results", "items", "records"]:
                    value = response_data.get(key)
                    if isinstance(value, list):
                        normalized = value
                        break
                else:
                    # If no known key, and the dict itself represents a single course, wrap it
                    normalized = [response_data]
            else:
                # Unknown payload type; return empty list but include raw for debugging
                logger.warning("Unexpected LMS course payload type; returning empty list")
                normalized = []

            return {
                "success": True,
                "status_code": response.status_code,
                "data": normalized
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to fetch courses'
            logger.error(f"Failed to fetch courses: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def get_all_modules(lms_cookies: str, lms_course_id: str) -> Dict[str, Any]:
    """
    Get all modules for a course from the LMS platform using authentication cookies
    
    Args:
        lms_cookies: Cookie string from Set-Cookie header (session-based auth)
        lms_course_id: The ID of the course to get modules for
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/course/{lms_course_id}/modules"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies  # Use Cookie header for session-based auth
    }
    
    try:
        logger.info(f"Fetching modules for course {lms_course_id} from LMS at {url}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code == 200:
            logger.info(f"Fetched modules successfully!")
            
            # Normalize to a list of modules regardless of LMS response shape
            normalized: Any
            if isinstance(response_data, list):
                normalized = response_data
            elif isinstance(response_data, dict):
                # Common keys that may contain the array
                for key in ["data", "modules", "results", "items", "records"]:
                    value = response_data.get(key)
                    if isinstance(value, list):
                        normalized = value
                        break
                else:
                    # If no known key, and the dict itself represents a single module, wrap it
                    normalized = [response_data]
            else:
                # Unknown payload type; return empty list but include raw for debugging
                logger.warning("Unexpected LMS module payload type; returning empty list")
                normalized = []

            return {
                "success": True,
                "status_code": response.status_code,
                "data": normalized
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to fetch modules'
            logger.error(f"Failed to fetch modules: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error fetching modules: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }
    
    # Ensure URL has protocol
def post_quiz_data_to_lms(lms_cookies: str, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post quiz data to the LMS platform using authentication cookies
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/activity/quiz"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies
    }
    
    try:
        logger.info(f"Posting quiz data to LMS at {url}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        logger.info(f"Quiz data: {quiz_data.get('title', 'Unknown')}")
        
        response = requests.post(url, json=quiz_data, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code in [200, 201]:
            logger.info(f"Quiz posted successfully!")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to post quiz'
            logger.error(f"Failed to post quiz: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error posting quiz: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def post_activity_data_to_lms(lms_cookies: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post activity data to the LMS platform using authentication cookies
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/activity"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies
    }
    
    try:
        logger.info(f"Posting activity data to LMS at {url}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        logger.info(f"Activity title: {activity_data.get('payload', {}).get('title', 'Unknown')}")
        logger.info(f"Activity data being sent to LMS: {json.dumps(activity_data, indent=2)}")
        
        response = requests.post(url, json=activity_data, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code in [200, 201]:
            logger.info(f"Activity posted successfully!")
            logger.info(f"LMS Response structure - Type: {type(response_data)}, Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            logger.info(f"LMS Response data: {response_data}")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to post activity'
            logger.error(f"Failed to post activity: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error posting activity: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def post_lecture_data_to_lms(lms_cookies: str, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post lecture data to the LMS platform using authentication cookies
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/activity"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies
    }
    
    try:
        logger.info(f"Posting lecture data to LMS at {url}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        logger.info(f"Lecture title: {lecture_data.get('payload', {}).get('title', 'Unknown')}")
        logger.info(f"Lecture data being sent to LMS: {json.dumps(lecture_data, indent=2)}")
        
        response = requests.post(url, json=lecture_data, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code in [200, 201]:
            logger.info(f"Lecture posted successfully!")
            logger.info(f"LMS Response structure - Type: {type(response_data)}, Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            logger.info(f"LMS Response data: {response_data}")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to post lecture'
            logger.error(f"Failed to post lecture: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error posting lecture: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def link_activity_to_course(lms_cookies: str, lms_course_id: str, lms_module_id: str, lms_activity_id: str, order: int = 0) -> Dict[str, Any]:
    """
    Link an activity to a course and topic/module in the LMS platform
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/activity/link"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies
    }
    
    payload = {
        "courseId": lms_course_id,
        "topicId": lms_module_id,
        "activityId": lms_activity_id,
        "order": order
    }
    
    try:
        logger.info(f"Linking activity {lms_activity_id} to course {lms_course_id}, topic {lms_module_id}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code in [200, 201]:
            logger.info(f"Activity linked successfully!")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to link activity'
            logger.error(f"Failed to link activity: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error linking activity: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }

def create_lms_module(lms_cookies: str, lms_course_id: str, module_title: str, order: int = 1) -> Dict[str, Any]:
    """
    Create a new module in the LMS platform
    
    Args:
        lms_cookies: Cookie string from Set-Cookie header (session-based auth)
        lms_course_id: The ID of the course to create the module in
        module_title: The title/name of the module
        order: The order of the module in the course (defaults to 1)
    """
    lms_base_url = settings.LMS_BASE_URL
    
    # Ensure URL has protocol
    if not lms_base_url.startswith('http://') and not lms_base_url.startswith('https://'):
        lms_base_url = f"https://{lms_base_url}"
    
    url = f"{lms_base_url}/api/v1/module"
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': lms_cookies
    }
    
    payload = {
        "courseId": lms_course_id,
        "title": module_title,
        "order": order
    }
    
    try:
        logger.info(f"Creating module '{module_title}' in course {lms_course_id}")
        logger.info(f"Using cookies: {lms_cookies[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Attempt to parse JSON but be defensive about non-JSON bodies
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        if response.status_code in [200, 201]:
            logger.info(f"Module created successfully!")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_msg = None
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('detail')
            if not error_msg:
                error_msg = 'Failed to create module'
            logger.error(f"Failed to create module: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error creating module: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 500
        }
    