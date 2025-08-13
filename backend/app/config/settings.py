import os
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

class Settings:
    """Application settings configuration"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_API_VERSION: str = "assistants=v2"
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_PRIVATE_KEY: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY")
    FIREBASE_CLIENT_EMAIL: Optional[str] = os.getenv("FIREBASE_CLIENT_EMAIL")
    FIREBASE_CLIENT_ID: Optional[str] = os.getenv("FIREBASE_CLIENT_ID")
    FIREBASE_AUTH_URI: str = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    FIREBASE_TOKEN_URI: str = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    FIREBASE_CLIENT_X509_CERT_URL: Optional[str] = os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://localhost:8501").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    CORS_ALLOW_METHODS: List[str] = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    CORS_ALLOW_HEADERS: List[str] = os.getenv("CORS_ALLOW_HEADERS", "Authorization,Content-Type,Accept,Origin,User-Agent").split(",")
    CORS_EXPOSE_HEADERS: List[str] = os.getenv("CORS_EXPOSE_HEADERS", "Content-Length,Content-Range").split(",")
    CORS_MAX_AGE: int = int(os.getenv("CORS_MAX_AGE", "3600"))
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/callback")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Firebase Client SDK
    FIREBASE_API_KEY: Optional[str] = os.getenv("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN: Optional[str] = os.getenv("FIREBASE_AUTH_DOMAIN")
    FIREBASE_STORAGE_BUCKET: Optional[str] = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID: Optional[str] = os.getenv("FIREBASE_APP_ID")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        # Firebase configuration: allow either serviceAccountKey.json or all env vars
        firebase_key_file = os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey.json')
        firebase_key_file = os.path.abspath(firebase_key_file)
        firebase_vars = [
            cls.FIREBASE_PROJECT_ID,
            cls.FIREBASE_PRIVATE_KEY_ID,
            cls.FIREBASE_PRIVATE_KEY,
            cls.FIREBASE_CLIENT_EMAIL,
            cls.FIREBASE_CLIENT_ID,
            cls.FIREBASE_CLIENT_X509_CERT_URL
        ]
        has_key_file = os.path.exists(firebase_key_file)
        has_all_env = all(firebase_vars)
        if not (has_key_file or has_all_env):
            raise ValueError("Firebase configuration missing: provide serviceAccountKey.json or set all Firebase env vars")

# Create global settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    raise 