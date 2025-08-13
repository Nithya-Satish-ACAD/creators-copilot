import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from .routes import auth, course, resources, asset
from .config.settings import settings
from .routes.auth import google_callback
import logging
import uvicorn
import time

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
        
        # Allow same-origin for OAuth popup communication, but deny external framing
        if request.url.path == "/api/callback":
            # For OAuth callback, allow same-origin to enable popup communication
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            # For all other routes, deny framing
            response.headers["X-Frame-Options"] = "DENY"
            
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for debugging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        
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

# Add logging middleware for production debugging
if not settings.DEBUG:
    app.add_middleware(LoggingMiddleware)

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
        "firebase_configured": bool(settings.FIREBASE_PROJECT_ID),
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        "debug_mode": settings.DEBUG
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error logging"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"error": "Internal server error", "detail": str(exc) if settings.DEBUG else "An error occurred"}

if __name__ == "__main__":
    logger.info(f"Starting Course Copilot API on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )