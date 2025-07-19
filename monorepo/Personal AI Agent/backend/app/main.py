import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.constants import DEFAULT_DESCRIPTION, OPENAPI_URL_SUFFIX
from app.db.database import get_db, Base, engine
from app.api.endpoints import auth, documents, queries, gmail, emails, sources, admin
from app.middleware.rate_limiting import apply_rate_limits
from app.middleware.session_monitoring import session_monitoring_middleware

# Create logger for this module
logger = logging.getLogger("personal_ai_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    # Startup
    logger.info("Application startup: Initializing...")
    
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    os.makedirs(settings.EMAIL_STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.EMAIL_VECTOR_DB_PATH, exist_ok=True)
    logger.info("Created necessary directories")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Test database connection
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        logger.info("Database connection successful!")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise
    finally:
        db.close()
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


# Initialize FastAPI app with modern lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=DEFAULT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}{OPENAPI_URL_SUFFIX}",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply rate limiting
try:
    apply_rate_limits(app)
    logger.info("Rate limiting enabled")
except ImportError as e:
    logger.warning(f"Rate limiting not available (install slowapi): {e}")
except Exception as e:
    logger.error(f"Failed to apply rate limiting: {e}")

# Add session monitoring middleware
app.middleware("http")(session_monitoring_middleware)
logger.info("Session monitoring enabled")

# Add custom middleware for request validation
@app.middleware("http")
async def validate_login_requests(request: Request, call_next):
    """Middleware to validate login requests and provide helpful error messages"""
    
    # Check if this is a login request
    if request.url.path == "/api/login" and request.method == "POST":
        content_type = request.headers.get("content-type", "")
        
        # Check for common mistake: sending JSON to login endpoint
        if "application/json" in content_type:
            logger.warning(f"Login request received with JSON content-type from {request.client.host}")
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Login endpoint expects form data, not JSON",
                    "error_type": "invalid_content_type",
                    "expected_format": "application/x-www-form-urlencoded",
                    "received_format": content_type,
                    "help": "Please send login data as form fields, not JSON",
                    "example": "username=your_username&password=your_password",
                    "timestamp": datetime.now().isoformat()
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
                    "Access-Control-Allow-Credentials": "true"
                }
            )
    
    # Continue with the request
    response = await call_next(request)
    return response

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])
app.include_router(queries.router, prefix=settings.API_V1_STR, tags=["queries"])
app.include_router(gmail.router, prefix=settings.API_V1_STR, tags=["gmail"])
app.include_router(emails.router, prefix=settings.API_V1_STR, tags=["emails"])
app.include_router(sources.router, prefix=settings.API_V1_STR, tags=["sources"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint serves the main frontend page
@app.get("/")
async def root():
    """Serve the main frontend page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

# API root endpoint for backend detection
@app.get("/api/")
async def api_root():
    """API root endpoint - used by frontend to detect backend"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Personal AI Agent Backend API",
        "api_version": "v1",
        "status": "running",
        "backend_installed": True,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health-check",
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/login",
            "documents": f"{settings.API_V1_STR}/documents",
            "queries": f"{settings.API_V1_STR}/queries",
            "gmail": f"{settings.API_V1_STR}/gmail",
            "emails": f"{settings.API_V1_STR}/emails",
            "sources": f"{settings.API_V1_STR}/sources"
        }
    }

@app.get(f"{settings.API_V1_STR}/health-check")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": settings.VERSION}

@app.get("/api/backend-status")
async def backend_status():
    """Backend detection endpoint for frontend"""
    return {
        "backend_installed": True,
        "backend_running": True,
        "version": settings.VERSION,
        "api_available": True,
        "database_connected": True,  # Could add actual DB check here
        "ready": True
    }

@app.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str = None
):
    """
    Handle OAuth2 callback from Google - redirects to Gmail callback
    """
    from fastapi.responses import RedirectResponse
    
    # Redirect to the actual Gmail callback endpoint with the code
    redirect_url = f"{settings.API_V1_STR}/gmail/callback?code={code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(url=redirect_url)

@app.get("/api/gmail/auth")
async def oauth_callback_alt(
    code: str,
    state: str = None
):
    """
    Alternative OAuth2 callback endpoint for current Google Cloud Console configuration
    """
    from fastapi.responses import RedirectResponse
    
    # Redirect to the actual Gmail callback endpoint with the code
    redirect_url = f"{settings.API_V1_STR}/gmail/callback?code={code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(url=redirect_url)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with CORS support and detailed error information"""
    
    # Determine if this is a login-related error
    is_auth_error = "/login" in str(request.url) or "/register" in str(request.url)
    
    # Create response content
    error_content = {
        "detail": exc.detail,
        "error_type": "authentication_error" if is_auth_error else "http_error",
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add helpful context for authentication errors
    if is_auth_error:
        if exc.status_code == 401:
            error_content["help"] = "Please check your username and password"
        elif exc.status_code == 400:
            error_content["help"] = "Please ensure all required fields are filled"
        elif exc.status_code == 422:
            error_content["help"] = "Please check your request format - login requires form data, not JSON"
            error_content["expected_format"] = "application/x-www-form-urlencoded"
            error_content["example"] = "username=your_username&password=your_password"
    
    # Create response with CORS headers
    response = JSONResponse(
        status_code=exc.status_code,
        content=error_content,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Allow-Credentials": "true"
        }
    )
    
    # Log the error for debugging
    logger.warning(f"HTTP {exc.status_code} error on {request.method} {request.url}: {exc.detail}")
    
    return response

# Deprecated startup event removed - using modern lifespan approach above 