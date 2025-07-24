#!/usr/bin/env python3
"""
Personal AI Agent Installer

This script sets up the Personal AI Agent on your system.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main installer function."""
    print("🚀 Personal AI Agent Installer")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # Create directories
    directories = [
        "data", "data/uploads", "data/vector_db", "data/vector_db/financial",
        "data/vector_db/long_form", "data/vector_db/generic", "data/vector_db/emails",
        "data/emails", "logs", "models", "backups"
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {directory}")
    
    # Create .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚙️ Creating configuration...")
        import secrets
        secret_key = secrets.token_hex(32)
        use_metal = 'true' if platform.system().lower() == 'darwin' else 'false'
        
        env_content = f"""# Personal AI Agent Configuration
PORTABLE_MODE=true
DATABASE_URL=sqlite:///data/personal_ai_agent_portable.db
HOST=localhost
PORT=8000
DEBUG=false
SECRET_KEY={secret_key}
API_V1_STR=/api
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8080
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL={use_metal}
METAL_N_GPU_LAYERS=1
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,txt,docx,xlsx
GMAIL_CLIENT_ID=your-gmail-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
LOG_LEVEL=INFO
LOG_FILE=logs/personal_ai_agent.log
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("  Created .env configuration")
    
    print()
    print("🎉 Installation completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Download AI models: python download_models.py")
    print("2. Start the application: open PersonalAIAgent.app")
    print("3. Open browser to: http://localhost:8000")
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())