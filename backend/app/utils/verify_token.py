from firebase_admin import auth
from fastapi import HTTPException, Header
import logging

logger = logging.getLogger(__name__)

def verify_token(authorization: str = Header(...)) -> str:
    try:
        decoded_token = auth.verify_id_token(authorization.replace("Bearer ", ""))
        return decoded_token["uid"]
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")