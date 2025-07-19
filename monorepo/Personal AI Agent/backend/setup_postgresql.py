#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Personal AI Agent

This script helps set up PostgreSQL database for development and production.
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible."""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PostgreSQL found: {result.stdout.strip()}")
            return True
        return False
    except FileNotFoundError:
        return False

def check_postgresql_running():
    """Check if PostgreSQL service is running."""
    try:
        result = subprocess.run(['pg_isready'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_postgresql_macos():
    """Install PostgreSQL on macOS using Homebrew."""
    logger.info("Installing PostgreSQL using Homebrew...")
    try:
        # Install PostgreSQL
        result = subprocess.run(['brew', 'install', 'postgresql@15'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to install PostgreSQL: {result.stderr}")
            return False
        
        # Start PostgreSQL service
        result = subprocess.run(['brew', 'services', 'start', 'postgresql@15'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to start PostgreSQL: {result.stderr}")
            return False
        
        logger.info("PostgreSQL installed and started successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing PostgreSQL: {e}")
        return False

def create_database_and_user():
    """Create database and user for the application."""
    try:
        # Try to connect to PostgreSQL and create user/databases
        logger.info("Creating database and user...")
        
        # Create user
        result = subprocess.run([
            'psql', 'postgres', '-c',
            "CREATE USER personal_ai_agent WITH PASSWORD 'dev_password';"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Created user: personal_ai_agent")
        elif "already exists" in result.stderr:
            logger.info("User 'personal_ai_agent' already exists")
        else:
            logger.error(f"Failed to create user: {result.stderr}")
            return False
        
        # Create development database
        result = subprocess.run([
            'psql', 'postgres', '-c',
            "CREATE DATABASE personal_ai_agent_dev OWNER personal_ai_agent ENCODING 'UTF8';"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Created database: personal_ai_agent_dev")
        elif "already exists" in result.stderr:
            logger.info("Database 'personal_ai_agent_dev' already exists")
        else:
            logger.error(f"Failed to create dev database: {result.stderr}")
            return False
        
        # Create production database
        result = subprocess.run([
            'psql', 'postgres', '-c',
            "CREATE DATABASE personal_ai_agent_prod OWNER personal_ai_agent ENCODING 'UTF8';"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Created database: personal_ai_agent_prod")
        elif "already exists" in result.stderr:
            logger.info("Database 'personal_ai_agent_prod' already exists")
        else:
            logger.error(f"Failed to create prod database: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error creating database: {e}")
        return False

def test_application_connection():
    """Test connection with application credentials."""
    try:
        result = subprocess.run([
            'psql', 
            'postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev',
            '-c', 'SELECT version();'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Application database connection successful")
            return True
        else:
            logger.error(f"Application connection failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        logger.info(".env file already exists")
        return True
    
    if env_example.exists():
        # Copy from example
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        logger.info("Created .env file from .env.example")
        return True
    else:
        # Create basic .env with PostgreSQL
        env_content = """# Personal AI Agent Configuration
DATABASE_URL=postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev
DATABASE_TIMEOUT=30
HOST=0.0.0.0
PORT=8000
DEBUG=true
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
API_V1_STR=/api
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
GMAIL_CLIENT_ID=your-gmail-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-gmail-client-secret
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info("Created basic .env file with PostgreSQL configuration")
        return True

def initialize_database_schema():
    """Initialize database schema using SQLAlchemy."""
    try:
        # Set environment to use PostgreSQL
        os.environ['DATABASE_URL'] = 'postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev'
        
        from app.db.database import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        logger.error("Make sure the application code is compatible with PostgreSQL")
        return False

def main():
    """Main setup function."""
    logger.info("🐘 PostgreSQL Setup for Personal AI Agent")
    logger.info("=" * 50)
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        logger.info("PostgreSQL not found. Attempting to install...")
        if sys.platform == "darwin":  # macOS
            if not install_postgresql_macos():
                logger.error("❌ Failed to install PostgreSQL")
                sys.exit(1)
        else:
            logger.error("❌ PostgreSQL is not installed")
            logger.info("Please install PostgreSQL manually:")
            logger.info("  Ubuntu/Debian: sudo apt-get install postgresql-15")
            logger.info("  CentOS/RHEL: sudo yum install postgresql15-server")
            logger.info("  Windows: Download from postgresql.org")
            sys.exit(1)
    
    # Check if PostgreSQL is running
    if not check_postgresql_running():
        if sys.platform == "darwin":  # macOS
            logger.info("Starting PostgreSQL...")
            subprocess.run(['brew', 'services', 'start', 'postgresql@15'])
            import time
            time.sleep(3)  # Wait for service to start
            
            if not check_postgresql_running():
                logger.error("❌ PostgreSQL failed to start")
                sys.exit(1)
        else:
            logger.error("❌ PostgreSQL is not running")
            logger.info("Start PostgreSQL:")
            logger.info("  Ubuntu/Debian: sudo systemctl start postgresql")
            logger.info("  CentOS/RHEL: sudo systemctl start postgresql-15")
            logger.info("  Windows: Start PostgreSQL service")
            sys.exit(1)
    
    # Create database and user
    logger.info("📋 Creating database and user...")
    if not create_database_and_user():
        logger.error("❌ Failed to create database and user")
        sys.exit(1)
    
    # Test connection
    logger.info("🔌 Testing application connection...")
    if not test_application_connection():
        logger.error("❌ Application connection test failed")
        sys.exit(1)
    
    # Create .env file
    logger.info("📄 Setting up environment file...")
    if not create_env_file():
        logger.error("❌ Failed to create .env file")
        sys.exit(1)
    
    # Initialize schema
    logger.info("🗄️ Initializing database schema...")
    if not initialize_database_schema():
        logger.error("❌ Failed to initialize database schema")
        logger.info("You may need to update the code to remove SQLite dependencies first")
        sys.exit(1)
    
    # Success
    logger.info("🎉 PostgreSQL setup completed successfully!")
    logger.info("")
    logger.info("📋 What was created:")
    logger.info("  ✅ Database: personal_ai_agent_dev")
    logger.info("  ✅ Database: personal_ai_agent_prod")
    logger.info("  ✅ User: personal_ai_agent")
    logger.info("  ✅ Schema: All tables initialized")
    logger.info("  ✅ Environment: .env file created")
    logger.info("")
    logger.info("🚀 Next steps:")
    logger.info("  1. Review and customize .env file")
    logger.info("  2. Download LLM models: python download_model.py")
    logger.info("  3. Start the application: python main.py")
    logger.info("")
    logger.info("🔗 Connection details:")
    logger.info("  Database URL: postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev")

if __name__ == "__main__":
    main() 