import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.database import get_db, Base, engine
from app.api.endpoints import auth, documents, queries

# Create logger for this module
logger = logging.getLogger("personal_ai_agent")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A fully private AI assistant for your documents",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])
app.include_router(queries.router, prefix=settings.API_V1_STR, tags=["queries"])

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

@app.get("/")
async def root():
    """Serve the main index page"""
    return FileResponse(os.path.join(settings.STATIC_DIR, "index.html"))

@app.get("/favicon.ico")
async def favicon():
    """Serve the favicon"""
    return FileResponse(os.path.join(settings.STATIC_DIR, "favicon.ico"))

@app.get(f"{settings.API_V1_STR}/health-check")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "0.1.0"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.on_event("startup")
async def startup_event():
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Test database connection
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        print("Database connection successful!")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        print(f"Database connection failed: {str(e)}")
        raise 