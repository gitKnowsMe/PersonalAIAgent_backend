#!/usr/bin/env python3
"""
Backend Startup Script
Starts the Personal AI Agent backend with proper configuration and validation.
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import jose
        import bcrypt
        logger.info("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

def check_models():
    """Check if AI models are downloaded."""
    logger.info("Checking AI models...")
    
    model_path = Path("models/mistral-7b-instruct-v0.1.Q4_K_M.gguf")
    if not model_path.exists():
        logger.warning("⚠️  LLM model not found. Downloading...")
        try:
            subprocess.run([sys.executable, "download_model.py"], check=True)
            logger.info("✅ LLM model downloaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download LLM model: {e}")
            return False
    else:
        logger.info("✅ LLM model found")
    
    # Check embedding model
    try:
        import sentence_transformers
        logger.info("✅ Embedding model available")
    except ImportError:
        logger.warning("⚠️  Embedding model not found. Downloading...")
        try:
            subprocess.run([sys.executable, "download_embedding_model.py"], check=True)
            logger.info("✅ Embedding model downloaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download embedding model: {e}")
            return False
    
    return True

def validate_configuration():
    """Validate configuration."""
    logger.info("Validating configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("⚠️  .env file not found. Creating from template...")
        try:
            # Copy from .env.example or create basic one
            env_example = Path(".env.example")
            if env_example.exists():
                subprocess.run(["cp", str(env_example), str(env_file)], check=True)
            else:
                # Create basic .env file
                with open(env_file, 'w') as f:
                    f.write("""# Basic configuration
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
DATABASE_URL=postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
API_V1_STR=/api
DEBUG=true
""")
            logger.info("✅ .env file created")
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    else:
        logger.info("✅ .env file found")
    
    return True

def setup_database():
    """Setup database."""
    logger.info("Setting up database...")
    
    try:
        subprocess.run([sys.executable, "setup_db.py"], check=True)
        logger.info("✅ Database setup completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    logger.info("Starting Personal AI Agent backend...")
    
    # Check if port 8000 is available
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result == 0:
        logger.warning("⚠️  Port 8000 is already in use")
        response = input("Kill existing process and start new one? (y/N): ")
        if response.lower() != 'y':
            logger.info("Exiting...")
            return False
        
        # Try to kill existing process
        try:
            subprocess.run(["pkill", "-f", "uvicorn.*main"], check=False)
            time.sleep(2)
        except:
            pass
    
    # Start server
    try:
        logger.info("🚀 Starting backend server on http://localhost:8000")
        logger.info("📚 API documentation: http://localhost:8000/docs")
        logger.info("🔍 Health check: http://localhost:8000/api/health-check")
        logger.info("⚡ Backend status: http://localhost:8000/api/backend-status")
        logger.info("\nPress Ctrl+C to stop the server")
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main startup function."""
    logger.info("🔧 Personal AI Agent Backend Startup")
    logger.info("=" * 50)
    
    # Run checks
    checks = [
        ("Dependencies", check_dependencies),
        ("AI Models", check_models),
        ("Configuration", validate_configuration),
        ("Database", setup_database)
    ]
    
    for check_name, check_func in checks:
        logger.info(f"\n📋 {check_name} Check:")
        if not check_func():
            logger.error(f"❌ {check_name} check failed. Exiting.")
            return 1
    
    logger.info("\n✅ All checks passed! Starting server...")
    
    # Start server
    if not start_server():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())