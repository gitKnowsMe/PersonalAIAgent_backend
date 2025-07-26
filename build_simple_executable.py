#!/usr/bin/env python3
"""
Simple PyInstaller Build Script for Personal AI Agent
Simplified approach to avoid module path conflicts
"""

import os
import subprocess
import shutil
from pathlib import Path

def build_simple_executable():
    """Build a simple executable that works reliably."""
    base_dir = Path(__file__).parent
    
    # Clean previous builds
    for dir_path in ["build", "dist"]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    # Simple PyInstaller command without complex spec file
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=PersonalAIAgent",
        "--add-data=static:static",
        "--add-data=.env.example:.",
        "--hidden-import=app",
        "--hidden-import=app.main",
        "--hidden-import=app.core.config",
        "--hidden-import=app.db.database",
        "--hidden-import=app.api.endpoints.auth",
        "--hidden-import=app.api.endpoints.documents", 
        "--hidden-import=app.api.endpoints.queries",
        "--hidden-import=app.api.endpoints.gmail",
        "--hidden-import=app.services.embedding_service",
        "--hidden-import=app.services.vector_store_service",
        "--hidden-import=app.utils.llm",
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=sqlalchemy",
        "--hidden-import=sentence_transformers",
        "--hidden-import=llama_cpp",
        "--hidden-import=faiss",
        "--noconfirm",
        "main.py"
    ]
    
    print("Building simple executable...")
    result = subprocess.run(cmd, cwd=base_dir)
    
    if result.returncode == 0:
        print("✅ Simple executable built successfully!")
        print("📁 Output: dist/PersonalAIAgent")
        
        # Test the executable
        exe_path = base_dir / "dist" / "PersonalAIAgent"
        if exe_path.exists():
            print(f"📊 Executable size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
    else:
        print("❌ Build failed")
        return False

if __name__ == "__main__":
    build_simple_executable()