import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from .routes import auth, course, resources, asset
from .config.settings import settings
from .routes.auth import google_callback
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

app = FastAPI(
    title="Creator Copilot API",
    description="AI-powered course creation and management system",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS middleware with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=settings.CORS_EXPOSE_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router, prefix="/api")
app.include_router(course.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(asset.router, prefix="/api")

# Google OAuth callback is now handled by the auth router at /api/callback

@app.get("/")
async def root():
    return {"message": "Welcome to the Course Copilot API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "firebase_configured": bool(settings.FIREBASE_PROJECT_ID)
    }

if __name__ == "__main__":
    logger.info(f"Starting Course Copilot API on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )