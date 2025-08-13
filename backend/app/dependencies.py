import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status, Request
from functools import lru_cache
from .config.settings import settings

@lru_cache()
def get_firebase_app():
    # Use GOOGLE_APPLICATION_CREDENTIALS env var or path to service account key
    cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

def get_current_user(request: Request):
    get_firebase_app()  # Ensure Firebase is initialized
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    id_token = auth_header.split(" ", 1)[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token.get("email", "")
        if not email.endswith("@atriauniversity.edu.in"):
            raise HTTPException(status_code=403, detail="Email domain not allowed")
        return decoded_token  # Contains uid, email, etc.
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")