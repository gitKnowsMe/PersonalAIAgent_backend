#!/usr/bin/env python3
"""
Create Enhanced DMG with Source Bundle
Since PyInstaller has module conflicts, use source code distribution instead
"""

import os
import shutil
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_source_bundle():
    """Create a source code bundle for distribution."""
    base_dir = Path(__file__).parent
    dist_dir = base_dir / "dist"
    app_bundle_name = "Personal AI Agent.app"
    app_bundle_path = dist_dir / app_bundle_name
    
    # Clean and create dist directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)
    
    # Create .app bundle structure
    contents_dir = app_bundle_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    for dir_path in [contents_dir, macos_dir, resources_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Copy source code to Resources
    logger.info("Copying source code to app bundle...")
    
    # Copy Python app code
    shutil.copytree(base_dir / "app", resources_dir / "app")
    
    # Copy essential files
    essential_files = [
        "main.py",
        "start_backend.py", 
        "requirements.txt",
        ".env",
        "download_model.py",
        "setup_db.py"
    ]
    
    for file_name in essential_files:
        src = base_dir / file_name
        if src.exists():
            shutil.copy2(src, resources_dir / file_name)
    
    # Copy static directory if it exists
    static_dir = base_dir / "static"
    if static_dir.exists():
        shutil.copytree(static_dir, resources_dir / "static")
    
    # Create launcher script
    launcher_script = f"""#!/bin/bash
cd "$(dirname "$0")/../Resources"
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if models exist, download if needed
if [ ! -f "models/phi-2-instruct-Q4_K_M.gguf" ]; then
    echo "📥 Downloading Phi-2 model (~1.7GB)..."
    python3 download_model.py
fi

# Start the backend
echo "🚀 Starting Personal AI Agent..."
python3 start_backend.py --skip-setup

# Open browser
sleep 3
open http://localhost:8000
"""
    
    launcher_path = macos_dir / "Personal AI Agent"
    with open(launcher_path, 'w') as f:
        f.write(launcher_script)
    
    # Make launcher executable
    launcher_path.chmod(0o755)
    
    # Create Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Personal AI Agent</string>
    <key>CFBundleIdentifier</key>
    <string>com.personalaiagent.app</string>
    <key>CFBundleName</key>
    <string>Personal AI Agent</string>
    <key>CFBundleVersion</key>
    <string>1.0.3</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.3</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
"""
    
    with open(contents_dir / "Info.plist", 'w') as f:
        f.write(info_plist)
    
    # Copy icon if available
    icon_path = base_dir / "icon-windowed.icns"
    if icon_path.exists():
        shutil.copy2(icon_path, resources_dir / "icon-windowed.icns")
    
    logger.info(f"✅ Source bundle created: {app_bundle_path}")
    
    # Create install script
    install_script = """#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

print("🚀 Personal AI Agent Installation")
print("=" * 50)

# Create data directories
data_dirs = [
    "data", "data/uploads", "data/vector_db", 
    "data/vector_db/financial", "data/vector_db/long_form", 
    "data/vector_db/generic", "data/vector_db/emails",
    "data/emails", "logs"
]

for dir_name in data_dirs:
    Path(dir_name).mkdir(parents=True, exist_ok=True)
    print(f"📁 Created: {dir_name}")

print("\\n✅ Installation complete!")
print("\\nNext steps:")
print("1. Move 'Personal AI Agent.app' to Applications folder")
print("2. Double-click to launch")
print("3. First run will download Phi-2 model (~1.7GB)")
print("4. Browser opens at http://localhost:8000")
"""
    
    with open(dist_dir / "install.py", 'w') as f:
        f.write(install_script)
    
    # Create README
    readme = """# Personal AI Agent - Enhanced DMG Distribution

## Installation

1. Run: `python3 install.py`
2. Move `Personal AI Agent.app` to Applications folder  
3. Double-click to launch
4. First run downloads Phi-2 model (~1.7GB)
5. Browser opens automatically at http://localhost:8000

## Features

- 🔒 Complete privacy - all AI processing local
- 📄 PDF document analysis with category-aware processing  
- 📧 Gmail integration with OAuth2
- 🧠 Local Phi-2 LLM (no external API calls)
- 🔍 Semantic search across documents and emails

## System Requirements

- macOS 10.14+
- Python 3.10+
- 8GB RAM (16GB recommended)
- 15GB free storage (for models and data)

## Support

- Documentation: https://github.com/gitKnowsMe/PersonalAIAgent_backend
- Issues: https://github.com/gitKnowsMe/PersonalAIAgent_backend/issues
"""
    
    with open(dist_dir / "README.md", 'w') as f:
        f.write(readme)
    
    logger.info("✅ Source bundle distribution created successfully!")
    return True

if __name__ == "__main__":
    create_source_bundle()