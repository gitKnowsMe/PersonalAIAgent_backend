#!/usr/bin/env python3
"""
Portable Startup Script for Personal AI Agent Backend

This script handles the initialization and startup of the Personal AI Agent
backend in portable/executable mode.
"""

import os
import sys
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

# Setup logging for portable mode
def setup_portable_logging():
    """Setup logging for portable deployment."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "personal_ai_agent.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("personal_ai_agent")

def setup_portable_environment():
    """Setup environment for portable mode."""
    # Set portable mode
    os.environ['PORTABLE_MODE'] = 'true'
    
    # Set default database URL for SQLite
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'sqlite:///data/personal_ai_agent_portable.db'
    
    # Set default host and port
    if 'HOST' not in os.environ:
        os.environ['HOST'] = 'localhost'
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '8000'
    
    # Set model path if not specified
    if 'LLM_MODEL_PATH' not in os.environ:
        models_dir = Path("models")
        if models_dir.exists():
            model_files = list(models_dir.glob("*.gguf"))
            if model_files:
                os.environ['LLM_MODEL_PATH'] = str(model_files[0])
    
    # Enable Metal on macOS if available
    if sys.platform == 'darwin' and 'USE_METAL' not in os.environ:
        os.environ['USE_METAL'] = 'true'
        os.environ['METAL_N_GPU_LAYERS'] = '1'

def create_data_directories():
    """Create necessary data directories for portable mode."""
    directories = [
        "data",
        "data/uploads",
        "data/vector_db",
        "data/vector_db/financial", 
        "data/vector_db/long_form",
        "data/vector_db/generic",
        "data/vector_db/emails",
        "data/emails",
        "logs",
        "models",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def check_requirements():
    """Check if all requirements are met for portable mode."""
    logger = logging.getLogger("personal_ai_agent")
    
    # Check if models exist
    models_dir = Path("models")
    if not models_dir.exists() or not list(models_dir.glob("*.gguf")):
        logger.warning("No AI models found in models/ directory")
        logger.warning("Please download models using: python download_model.py")
        logger.warning("The application will start but AI features may not work")
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        logger.info("No .env file found, using environment variables and defaults")
    
    return True

async def initialize_portable_database():
    """Initialize database for portable mode."""
    logger = logging.getLogger("personal_ai_agent")
    
    try:
        # Import portable database configuration
        from app.db.database_portable import create_portable_database, get_database_info
        
        # Create and initialize database
        db_config = create_portable_database()
        db_info = get_database_info()
        
        logger.info(f"Database initialized: {db_info['type']}")
        logger.info(f"Database URL: {db_info['url']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error("The application may not function properly")
        return False

async def check_first_run():
    """Check if this is the first run and setup admin user if needed."""
    logger = logging.getLogger("personal_ai_agent")
    
    try:
        from app.db.database_portable import SessionLocal
        from app.db.models import User
        
        # Check if any users exist
        with SessionLocal() as db:
            user_count = db.query(User).count()
            
        if user_count == 0:
            logger.info("First run detected - creating default admin user")
            
            # Create default admin user
            from app.core.security import get_password_hash
            from app.db.models import User
            
            admin_user = User(
                email="admin@localhost",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_admin=True,
                is_active=True
            )
            
            with SessionLocal() as db:
                db.add(admin_user)
                db.commit()
                
            logger.info("Default admin user created:")
            logger.info("  Email: admin@localhost")
            logger.info("  Username: admin")
            logger.info("  Password: admin123")
            logger.info("  Please change the password after first login!")
            
    except Exception as e:
        logger.error(f"Failed to check/create admin user: {e}")

@asynccontextmanager
async def portable_lifespan(app):
    """Application lifespan for portable mode."""
    logger = logging.getLogger("personal_ai_agent")
    
    try:
        logger.info("🚀 Starting Personal AI Agent in portable mode")
        
        # Initialize database
        await initialize_portable_database()
        
        # Check for first run
        await check_first_run()
        
        # Load models (if available)
        try:
            from app.utils.llm import initialize_llm
            await initialize_llm()
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load AI models: {e}")
            logger.warning("AI features may not be available")
        
        logger.info("✅ Personal AI Agent started successfully")
        logger.info(f"🌐 Web interface: http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', '8000')}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        logger.info("🛑 Personal AI Agent shutting down")

def main():
    """Main entry point for portable mode."""
    # Setup logging
    logger = setup_portable_logging()
    
    try:
        logger.info("Personal AI Agent - Portable Mode")
        logger.info("=" * 50)
        
        # Setup environment
        setup_portable_environment()
        
        # Create directories
        create_data_directories()
        
        # Check requirements
        if not check_requirements():
            logger.error("Requirements check failed")
            return 1
        
        # Import and start the FastAPI application
        from app.main import app
        
        # Replace the lifespan with our portable version
        app.router.lifespan_context = portable_lifespan
        
        # Start the server
        import uvicorn
        
        host = os.getenv('HOST', 'localhost')
        port = int(os.getenv('PORT', '8000'))
        
        logger.info(f"Starting server on {host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())