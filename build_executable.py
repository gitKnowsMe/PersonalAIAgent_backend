#!/usr/bin/env python3
"""
PyInstaller Build Script for Personal AI Agent Backend Executable

This script creates a single executable from the FastAPI backend that includes:
- All Python dependencies
- Database compatibility (PostgreSQL/SQLite)
- LLM models (optional progressive download)
- Static frontend files
- Configuration templates

Usage:
    python build_executable.py [--include-models] [--platform TARGET] [--debug]
"""

import os
import sys
import shutil
import subprocess
import argparse
import platform
from pathlib import Path
import json
import logging
import plistlib
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutableBuilder:
    def __init__(self, include_models=False, target_platform=None, debug=False, create_dmg=False):
        self.include_models = include_models
        self.target_platform = target_platform or platform.system().lower()
        self.debug = debug
        self.create_dmg = create_dmg
        self.base_dir = Path(__file__).parent
        self.build_dir = self.base_dir / "build"
        self.dist_dir = self.base_dir / "dist"
        self.spec_file = self.base_dir / "personal_ai_agent.spec"
        
    def clean_build_directories(self):
        """Clean previous build artifacts."""
        logger.info("Cleaning build directories...")
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Removed {dir_path}")
        
        if self.spec_file.exists():
            self.spec_file.unlink()
            logger.info(f"Removed {self.spec_file}")
    
    def get_hidden_imports(self) -> List[str]:
        """Get list of hidden imports for PyInstaller."""
        hidden_imports = [
            # FastAPI and related
            'fastapi',
            'fastapi.responses',
            'fastapi.middleware',
            'fastapi.middleware.cors',
            'fastapi.security',
            'fastapi.staticfiles',
            'uvicorn',
            'uvicorn.protocols',
            'uvicorn.protocols.http',
            'uvicorn.protocols.websockets',
            'uvicorn.lifespan',
            'uvicorn.lifespan.on',
            'starlette',
            'starlette.responses',
            'starlette.middleware',
            'starlette.staticfiles',
            
            # Database
            'sqlalchemy',
            'sqlalchemy.orm',
            'sqlalchemy.sql',
            'sqlalchemy.engine',
            'sqlalchemy.dialects',
            'sqlalchemy.dialects.postgresql',
            'sqlalchemy.dialects.sqlite',
            'psycopg2',
            'sqlite3',
            
            # AI/ML Libraries
            'sentence_transformers',
            'transformers',
            'torch',
            'numpy',
            'scipy',
            'sklearn',
            'faiss',
            'langchain',
            'langchain_community',
            'langchain_core',
            'llama_cpp',
            
            # Google APIs
            'google',
            'google.auth',
            'google.oauth2',
            'google_auth_oauthlib',
            'googleapiclient',
            'googleapiclient.discovery',
            
            # Other dependencies
            'pydantic',
            'pydantic_settings',
            'bcrypt',
            'passlib',
            'python_jose',
            'cryptography',
            'python_multipart',
            'aiofiles',
            'httpx',
            'requests',
            'pandas',
            'pypdf',
            'python_docx',
            'openpyxl',
            'pikepdf',
            'pymupdf',
            'fitz',
            
            # Email processing
            'email',
            'email.mime',
            'email.utils',
            'imaplib',
            'smtplib',
            
            # Utilities
            'json',
            'yaml',
            'toml',
            'configparser',
            'dateutil',
            'pytz',
            'chardet',
            'magic',
            'mimetypes',
        ]
        
        # Add platform-specific imports
        if self.target_platform == 'darwin':
            hidden_imports.extend([
                'Foundation',
                'AppKit',
                'objc',
            ])
        elif self.target_platform == 'windows':
            hidden_imports.extend([
                'win32api',
                'win32con',
                'win32gui',
                'winreg',
            ])
        elif self.target_platform == 'linux':
            hidden_imports.extend([
                'gi',
                'gi.repository',
            ])
        
        return hidden_imports
    
    def get_data_files(self) -> List[tuple]:
        """Get list of data files to include in executable."""
        data_files = []
        
        # Static frontend files
        static_dir = self.base_dir / "static"
        if static_dir.exists():
            for file_path in static_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(static_dir)
                    data_files.append((str(file_path), f"static/{rel_path}"))
        
        # Configuration templates
        config_files = [
            ".env.example",
            ".env.development", 
            ".env.production",
            "requirements.txt",
        ]
        
        for config_file in config_files:
            config_path = self.base_dir / config_file
            if config_path.exists():
                data_files.append((str(config_path), config_file))
        
        # Models (if including)
        if self.include_models:
            models_dir = self.base_dir / "models"
            if models_dir.exists():
                for model_file in models_dir.glob("*.gguf"):
                    data_files.append((str(model_file), f"models/{model_file.name}"))
                    logger.info(f"Including model: {model_file.name}")
        
        # Database migration scripts
        migration_files = [
            "setup_db.py",
            "setup_postgresql.py",
            "migrate_to_postgresql.py",
            "create_admin.py",
        ]
        
        for migration_file in migration_files:
            migration_path = self.base_dir / migration_file
            if migration_path.exists():
                data_files.append((str(migration_path), migration_file))
        
        # Add portable database configuration
        portable_db_files = [
            "app/db/database_portable.py",
            "app/db/models_portable.py",
        ]
        
        for db_file in portable_db_files:
            db_path = self.base_dir / db_file
            if db_path.exists():
                data_files.append((str(db_path), db_file))
        
        return data_files
    
    def get_binary_excludes(self) -> List[str]:
        """Get list of binaries to exclude to reduce size."""
        excludes = [
            'tcl',
            'tk',
            'libX11',
            'libXau',
            'libXdmcp',
            'libdrm',
            'libxcb',
            'libGL',
            'libGLX',
            'libglapi',
            'libEGL',
            'libwayland',
        ]
        
        # Exclude large AI libraries if not using GPU
        if not os.getenv("USE_GPU", "false").lower() == "true":
            excludes.extend([
                'libcuda',
                'libcudnn',
                'libcublas',
                'libcufft',
                'libcurand',
                'libcusparse',
                'libcusolver',
                'libnvToolsExt',
            ])
        
        return excludes
    
    def create_pyinstaller_spec(self):
        """Create PyInstaller spec file."""
        logger.info("Creating PyInstaller spec file...")
        
        hidden_imports = self.get_hidden_imports()
        data_files = self.get_data_files()
        binary_excludes = self.get_binary_excludes()
        
        # Get application version
        try:
            from app.core.config import settings
            version = getattr(settings, 'VERSION', '1.0.0')
        except:
            version = '1.0.0'
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Personal AI Agent Backend
Generated automatically by build_executable.py
"""

import sys
from pathlib import Path

# Build configuration
block_cipher = None
debug = {self.debug}
include_models = {self.include_models}

# Application info
app_name = "PersonalAIAgent"
app_version = "{version}"
app_description = "Personal AI Agent - Privacy-first AI assistant with local processing"

# Source files
source_dir = Path.cwd()
main_script = source_dir / "startup_enhanced.py"

# Hidden imports
hiddenimports = {hidden_imports!r}

# Data files
datas = {data_files!r}

# Binary excludes
excludes = {binary_excludes!r}

# Analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(source_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(source_dir / "hooks")],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove excluded binaries
a.binaries = TOC([x for x in a.binaries if not any(exclude in x[0] for exclude in excludes)])

# PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable configuration
exe_kwargs = {{
    'name': app_name,
    'debug': debug,
    'bootloader_ignore_signals': False,
    'strip': not debug,
    'upx': True and not debug,
    'upx_exclude': [],
    'runtime_tmpdir': None,
    'console': True,  # Keep console for now
    'disable_windowed_traceback': False,
    'target_arch': None,
    'codesign_identity': None,
    'entitlements_file': None,
}}

# Platform-specific configuration
if sys.platform == "darwin":
    # macOS configuration
    exe_kwargs.update({{
        'icon': None,  # Add icon path if available
    }})
elif sys.platform == "win32":
    # Windows configuration
    exe_kwargs.update({{
        'icon': None,  # Add icon path if available
        'version_file': None,  # Add version file if available
    }})
elif sys.platform.startswith("linux"):
    # Linux configuration
    exe_kwargs.update({{
        'icon': None,  # Add icon path if available
    }})

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    **exe_kwargs
)

# macOS App Bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name='Personal AI Agent.app',
        icon=None,
        bundle_identifier='com.personalaiagent.backend',
        version=app_version,
        info_plist={{
            'CFBundleDisplayName': 'Personal AI Agent',
            'CFBundleName': 'Personal AI Agent',
            'CFBundleIdentifier': 'com.personalaiagent.backend',
            'CFBundleVersion': app_version,
            'CFBundleShortVersionString': app_version,
            'CFBundleExecutable': app_name,
            'CFBundleIconFile': 'app_icon',
            'CFBundleInfoDictionaryVersion': '6.0',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'PAIA',
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.productivity',
            'LSMinimumSystemVersion': '10.14.0',
            'NSRequiresAquaSystemAppearance': False,
            'NSSupportsAutomaticTermination': True,
            'NSSupportsSuddenTermination': True,
            'NSHumanReadableCopyright': '© 2024 Personal AI Agent. All rights reserved.',
            'LSEnvironment': {{
                'PORTABLE_MODE': 'true',
                'PYTHONHOME': '',
                'PYTHONPATH': ''
            }},
            'NSAppTransportSecurity': {{
                'NSAllowsArbitraryLoads': False,
                'NSExceptionDomains': {{
                    'localhost': {{
                        'NSExceptionAllowsInsecureHTTPLoads': True,
                        'NSExceptionMinimumTLSVersion': '1.0'
                    }}
                }}
            }}
        }},
    )
'''
        
        with open(self.spec_file, 'w') as f:
            f.write(spec_content)
        
        logger.info(f"Created spec file: {self.spec_file}")
    
    def install_pyinstaller(self):
        """Install PyInstaller if not available."""
        try:
            import PyInstaller
            logger.info(f"PyInstaller already installed: {PyInstaller.__version__}")
            return True
        except ImportError:
            logger.info("Installing PyInstaller...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                logger.info("PyInstaller installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install PyInstaller: {e}")
                return False
    
    def build_executable(self):
        """Build the executable using PyInstaller."""
        logger.info("Building executable with PyInstaller...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(self.spec_file),
            "--noconfirm",
            "--clean",
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                logger.info("Executable built successfully!")
                logger.info(f"Build output:\n{result.stdout}")
                return True
            else:
                logger.error(f"Build failed with return code {result.returncode}")
                logger.error(f"Build error:\n{result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def create_installer_script(self):
        """Create installer script for the executable."""
        logger.info("Creating installer script...")
        
        installer_script = f'''#!/usr/bin/env python3
"""
Personal AI Agent Backend Installer

This script helps users set up the Personal AI Agent backend executable.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {{sys.version}}")
    return True

def create_data_directories():
    """Create necessary data directories."""
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
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {{directory}}")

def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")
    
    if not env_file.exists():
        # Create basic .env for portable mode
        env_content = """# Personal AI Agent - Portable Configuration
PORTABLE_MODE=true
DATABASE_URL=sqlite:///data/personal_ai_agent_portable.db
HOST=localhost
PORT=8000
DEBUG=false
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
API_V1_STR=/api
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
LLM_MODEL_PATH=models/phi-2-instruct-Q4_K_M.gguf
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Gmail OAuth (optional - configure for email features)
GMAIL_CLIENT_ID=your-gmail-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info("Created .env file for portable mode")
    else:
        logger.info(".env file already exists")

def download_models():
    """Download required AI models."""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_file = models_dir / "phi-2-instruct-Q4_K_M.gguf"
    
    if not model_file.exists():
        logger.info("Downloading Phi-2 model (this may take several minutes)...")
        # In a real implementation, this would download the model
        # For now, just create a placeholder
        logger.warning("Model download not implemented in this installer")
        logger.info("Please run 'python download_model.py' separately to download models")
    else:
        logger.info("Phi-2 model already exists")

def setup_database():
    """Set up SQLite database for portable mode."""
    logger.info("Setting up portable SQLite database...")
    
    # Set environment for portable mode
    os.environ['PORTABLE_MODE'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///data/personal_ai_agent_portable.db'
    
    try:
        # This would initialize the database
        logger.info("Database setup would be implemented here")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {{e}}")
        return False

def main():
    """Main installer function."""
    logger.info("🚀 Personal AI Agent Backend Installer")
    logger.info("=" * 50)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    # Setup
    create_data_directories()
    setup_environment()
    download_models()
    setup_database()
    
    logger.info("🎉 Installation completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Configure Gmail OAuth in .env (optional)")
    logger.info("2. Download models: python download_model.py")
    logger.info("3. Run the application: ./PersonalAIAgent")
    logger.info("")
    logger.info("The application will be available at: http://localhost:8000")

if __name__ == "__main__":
    main()
'''
        
        installer_path = self.dist_dir / "install.py"
        with open(installer_path, 'w') as f:
            f.write(installer_script)
        
        logger.info(f"Created installer script: {installer_path}")
    
    def create_readme(self):
        """Create README for the executable distribution."""
        readme_content = f'''# Personal AI Agent Backend Executable

A privacy-first AI assistant with local processing capabilities.

## Quick Start

1. **Extract**: Extract all files to a directory of your choice
2. **Install**: Run the installer to set up the environment
   ```bash
   python install.py
   ```
3. **Configure**: Edit `.env` file for Gmail OAuth (optional)
4. **Download Models**: Download required AI models
   ```bash
   python download_model.py
   ```
5. **Run**: Start the application
   ```bash
   ./PersonalAIAgent          # macOS/Linux
   PersonalAIAgent.exe        # Windows
   ```

## Features

- 🔒 **Privacy-First**: All AI processing happens locally
- 📄 **PDF Processing**: Upload and query PDF documents
- 📧 **Gmail Integration**: Search and query your emails
- 🤖 **Local AI**: Phi-2 model for intelligent responses
- 🔍 **Vector Search**: Semantic search across documents and emails
- 🌐 **Web Interface**: Built-in web interface at http://localhost:8000

## System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space (for models and data)
- **Python**: 3.8+ (for installer and model download)

## Configuration

### Basic Configuration
The application uses `.env` file for configuration. Key settings:

```bash
# Database (SQLite for portable mode)
PORTABLE_MODE=true
DATABASE_URL=sqlite:///data/personal_ai_agent_portable.db

# Server settings
HOST=localhost
PORT=8000

# Model configuration
LLM_MODEL_PATH=models/phi-2-instruct-Q4_K_M.gguf
USE_METAL=true  # Enable on macOS for better performance
```

### Gmail Integration (Optional)
To enable Gmail features:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Gmail API
3. Create OAuth2 credentials
4. Update `.env` with your credentials:
   ```bash
   GMAIL_CLIENT_ID=your-client-id.googleusercontent.com
   GMAIL_CLIENT_SECRET=your-client-secret
   ```

## Troubleshooting

### Application Won't Start
- Check that all files were extracted properly
- Verify Python 3.8+ is installed for the installer
- Run `python install.py` to set up the environment
- Check logs in `logs/` directory

### Models Not Found
- Run `python download_model.py` to download required models
- Check that `models/` directory contains the GGUF files
- Verify `LLM_MODEL_PATH` in `.env` points to correct file

### Database Issues
- Delete `data/personal_ai_agent_portable.db` and restart
- Check that `data/` directory exists and is writable
- Verify `PORTABLE_MODE=true` in `.env`

### Port Already in Use
- Change `PORT=8000` to another port in `.env`
- Check that no other applications are using port 8000

## Support

For issues and support:
- Check the logs in `logs/app.log`
- Verify all configuration in `.env`
- Ensure models are downloaded and accessible

## Privacy

This application processes all data locally:
- No data sent to external AI services
- Local Phi-2 model for AI processing
- SQLite database stored locally
- Gmail data cached locally when synced

Built with: FastAPI, SQLAlchemy, LangChain, FAISS, llama-cpp-python
Platform: {self.target_platform}
Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
        
        readme_path = self.dist_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"Created README: {readme_path}")
    
    def create_macos_app_bundle(self):
        """Create proper macOS app bundle structure with enhanced configuration."""
        if self.target_platform != 'darwin':
            return True
            
        logger.info("Creating enhanced macOS .app bundle...")
        
        app_name = "Personal AI Agent"
        app_bundle_name = f"{app_name}.app"
        app_path = self.dist_dir / app_bundle_name
        
        # Check if PyInstaller already created a bundle
        if app_path.exists():
            logger.info(f"Using existing app bundle: {app_path}")
        else:
            # Create app bundle structure manually if needed
            logger.info("Creating app bundle structure...")
            contents_dir = app_path / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            # Create directories
            for directory in [contents_dir, macos_dir, resources_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Move executable to MacOS directory
            exe_path = self.dist_dir / "PersonalAIAgent"
            if exe_path.exists():
                shutil.move(str(exe_path), str(macos_dir / "PersonalAIAgent"))
                # Make executable
                os.chmod(macos_dir / "PersonalAIAgent", 0o755)
        
        # Enhance Info.plist with comprehensive metadata
        contents_dir = app_path / "Contents"
        info_plist_path = contents_dir / "Info.plist"
        
        try:
            from app.core.config import settings
            version = getattr(settings, 'VERSION', '1.0.0')
        except:
            version = '1.0.0'
        
        # Enhanced Info.plist configuration
        info_plist = {
            'CFBundleDisplayName': app_name,
            'CFBundleName': app_name,
            'CFBundleIdentifier': 'com.personalaiagent.backend',
            'CFBundleVersion': version,
            'CFBundleShortVersionString': version,
            'CFBundleExecutable': 'PersonalAIAgent',
            'CFBundleIconFile': 'app_icon',
            'CFBundleInfoDictionaryVersion': '6.0',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'PAIA',
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.productivity',
            'LSMinimumSystemVersion': '10.14.0',
            'NSRequiresAquaSystemAppearance': False,  # Dark mode support
            'NSSupportsAutomaticTermination': True,
            'NSSupportsSuddenTermination': True,
            'NSHumanReadableCopyright': f'© 2024 Personal AI Agent. All rights reserved.',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeExtensions': ['pdf'],
                    'CFBundleTypeName': 'PDF Document',
                    'CFBundleTypeRole': 'Viewer',
                    'LSHandlerRank': 'Alternate'
                }
            ],
            'LSEnvironment': {
                'PORTABLE_MODE': 'true',
                'PYTHONHOME': '',
                'PYTHONPATH': ''
            },
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': False,
                'NSExceptionDomains': {
                    'localhost': {
                        'NSExceptionAllowsInsecureHTTPLoads': True,
                        'NSExceptionMinimumTLSVersion': '1.0'
                    }
                }
            }
        }
        
        # Write enhanced Info.plist
        with open(info_plist_path, 'wb') as f:
            plistlib.dump(info_plist, f)
        
        logger.info(f"Enhanced macOS app bundle created: {app_path}")
        return True
    
    def create_dmg_resources(self):
        """Create resources for professional DMG creation."""
        if self.target_platform != 'darwin':
            return True
            
        logger.info("Creating DMG resources...")
        
        # Create resources directory
        resources_dir = self.base_dir / "dmg_resources"
        resources_dir.mkdir(exist_ok=True)
        
        # Create DMG background (placeholder - would need actual design)
        background_script = '''#!/bin/bash
# Create a simple gradient background for DMG
# In production, this would be a professionally designed PNG
convert -size 800x400 gradient:#1a1a1a-#2d2d2d "dmg_background.png" 2>/dev/null || {
    # Fallback: create a simple colored background
    python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Create background image
img = Image.new('RGB', (800, 400), '#1a1a1a')
draw = ImageDraw.Draw(img)

# Add gradient effect (simple)
for y in range(400):
    color_value = int(26 + (45-26) * (y/400))  # Gradient from #1a1a1a to #2d2d2d
    color = f'#{color_value:02x}{color_value:02x}{color_value:02x}'
    draw.line([(0, y), (800, y)], fill=color)

# Add title text
try:
    # Try to use a nice font
    font = ImageFont.truetype('/System/Library/Fonts/SF-Pro-Display-Bold.otf', 36)
except:
    # Fallback to default
    font = ImageFont.load_default()

text = 'Personal AI Agent'
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (800 - text_width) // 2
text_y = 50

draw.text((text_x, text_y), text, fill='#ffffff', font=font)

# Add subtitle
try:
    subtitle_font = ImageFont.truetype('/System/Library/Fonts/SF-Pro-Display-Regular.otf', 18)
except:
    subtitle_font = ImageFont.load_default()

subtitle = 'Privacy-first AI assistant with local processing'
bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
subtitle_width = bbox[2] - bbox[0]
subtitle_x = (800 - subtitle_width) // 2
subtitle_y = text_y + text_height + 10

draw.text((subtitle_x, subtitle_y), subtitle, fill='#cccccc', font=subtitle_font)

# Add installation instructions
instruction = 'Drag the app to Applications folder to install'
bbox = draw.textbbox((0, 0), instruction, font=subtitle_font)
inst_width = bbox[2] - bbox[0]
inst_x = (800 - inst_width) // 2
inst_y = 320

draw.text((inst_x, inst_y), instruction, fill='#888888', font=subtitle_font)

img.save('dmg_background.png')
print('Created DMG background image')
" || echo "Could not create background image - will use default"
}'''
        
        background_script_path = resources_dir / "create_background.sh"
        with open(background_script_path, 'w') as f:
            f.write(background_script)
        os.chmod(background_script_path, 0o755)
        
        # Run background creation
        try:
            subprocess.run(['bash', str(background_script_path)], cwd=resources_dir, check=False)
        except Exception as e:
            logger.warning(f"Could not create background: {e}")
        
        # Create Quick Start Guide
        quick_start = f'''# Personal AI Agent - Quick Start Guide

## Welcome!

Thank you for downloading Personal AI Agent, your privacy-first AI assistant.

## Installation

1. **Drag and Drop**: Drag "Personal AI Agent.app" to your Applications folder
2. **First Launch**: Double-click the app in Applications
3. **Model Download**: The app will download the Phi-2 AI model (~1.7GB) on first run
4. **Browser Access**: Once ready, visit http://localhost:8000

## Features

- 🔒 **Complete Privacy**: All AI processing happens locally on your Mac
- 📄 **PDF Analysis**: Upload and query PDF documents
- 📧 **Gmail Integration**: Search and analyze your emails (optional)
- 🤖 **Local AI**: Phi-2 model for intelligent responses
- 🔍 **Smart Search**: Semantic search across all your content

## System Requirements

- macOS 10.14 or later (Intel or Apple Silicon)
- 8GB RAM (16GB recommended)
- 15GB free disk space (for models and data)

## Getting Started

1. **Launch the app** from Applications
2. **Wait for setup** (first launch takes a few minutes)
3. **Open browser** to http://localhost:8000
4. **Create account** and start uploading documents
5. **Optional**: Configure Gmail integration in settings

## Support

- App logs: ~/Library/Logs/PersonalAIAgent/
- Data location: ~/Library/Application Support/PersonalAIAgent/
- GitHub: https://github.com/gitKnowsMe/PersonalAIAgent_backend

## Privacy

- All data stays on your Mac
- No external AI services used
- Your documents and emails remain private
- Local processing with Phi-2 model

Enjoy your private AI assistant!
'''
        
        quick_start_path = resources_dir / "Quick Start Guide.md"
        with open(quick_start_path, 'w') as f:
            f.write(quick_start)
        
        logger.info(f"Created DMG resources in: {resources_dir}")
        return True
    
    def create_professional_dmg(self):
        """Create professional DMG using native macOS hdiutil."""
        if self.target_platform != 'darwin':
            return True
            
        logger.info("Creating professional DMG installer...")
        
        app_name = "Personal AI Agent"
        app_bundle = f"{app_name}.app"
        dmg_name = f"{app_name} Installer.dmg"
        
        # Ensure app bundle exists
        app_path = self.dist_dir / app_bundle
        if not app_path.exists():
            logger.error(f"App bundle not found: {app_path}")
            return False
        
        # Create temporary DMG staging directory
        dmg_staging = self.dist_dir / "dmg_staging"
        if dmg_staging.exists():
            shutil.rmtree(dmg_staging)
        dmg_staging.mkdir()
        
        # Copy app bundle to staging
        shutil.copytree(app_path, dmg_staging / app_bundle)
        
        # Copy additional resources
        resources_dir = self.base_dir / "dmg_resources"
        if resources_dir.exists():
            quick_start = resources_dir / "Quick Start Guide.md"
            if quick_start.exists():
                shutil.copy2(quick_start, dmg_staging / "Quick Start Guide.md")
        
        # Create DMG using native hdiutil
        dmg_path = self.dist_dir / dmg_name
        if dmg_path.exists():
            dmg_path.unlink()
        
        logger.info(f"Creating DMG with hdiutil: {dmg_path}")
        
        try:
            # Create DMG using hdiutil
            cmd = [
                'hdiutil', 'create',
                '-volname', f'{app_name} Installer',
                '-srcfolder', str(dmg_staging),
                '-ov',  # Overwrite existing
                '-format', 'UDZO',  # Compressed
                str(dmg_path)
            ]
            
            logger.info(f"Running hdiutil command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and dmg_path.exists():
                logger.info(f"DMG created successfully: {dmg_path}")
                
                # Get DMG size for reporting
                dmg_size = dmg_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"DMG size: {dmg_size:.1f} MB")
                
                # Clean up staging directory
                shutil.rmtree(dmg_staging)
                
                return True
            else:
                logger.error(f"DMG creation failed. Return code: {result.returncode}")
                logger.error(f"Output: {result.stdout}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("DMG creation timed out")
            return False
        except Exception as e:
            logger.error(f"Error creating DMG: {e}")
            return False
    
    def package_distribution(self):
        """Package the distribution for release."""
        logger.info("Packaging distribution...")
        
        # Determine executable name based on platform
        if self.target_platform == "windows":
            exe_name = "PersonalAIAgent.exe"
            archive_format = "zip"
        elif self.target_platform == "darwin":
            exe_name = "PersonalAIAgent.app" if (self.dist_dir / "PersonalAIAgent.app").exists() else "PersonalAIAgent"
            archive_format = "zip"  # Could also create DMG
        else:  # Linux
            exe_name = "PersonalAIAgent"
            archive_format = "tar.gz"
        
        exe_path = self.dist_dir / exe_name
        if not exe_path.exists():
            # Fallback to just executable name
            exe_path = self.dist_dir / "PersonalAIAgent"
        
        if not exe_path.exists():
            logger.error(f"Executable not found: {exe_path}")
            return False
        
        # Create distribution info
        dist_info = {
            "name": "Personal AI Agent Backend",
            "version": "1.0.0",
            "platform": self.target_platform,
            "executable": exe_name,
            "includes_models": self.include_models,
            "build_date": __import__('datetime').datetime.now().isoformat(),
            "requirements": {
                "python": "3.8+",
                "ram": "8GB+",
                "storage": "10GB+",
            }
        }
        
        dist_info_path = self.dist_dir / "distribution_info.json"
        with open(dist_info_path, 'w') as f:
            json.dump(dist_info, f, indent=2)
        
        logger.info("Distribution packaged successfully!")
        logger.info(f"Executable: {exe_path}")
        logger.info(f"Platform: {self.target_platform}")
        logger.info(f"Includes models: {self.include_models}")
        
        return True
    
    def build(self):
        """Main build process."""
        logger.info(f"🏗️  Building Personal AI Agent executable for {self.target_platform}")
        logger.info("=" * 60)
        
        try:
            # Clean previous builds
            self.clean_build_directories()
            
            # Install PyInstaller
            if not self.install_pyinstaller():
                return False
            
            # Create spec file
            self.create_pyinstaller_spec()
            
            # Build executable
            if not self.build_executable():
                return False
            
            # Enhanced macOS app bundle creation
            if not self.create_macos_app_bundle():
                return False
            
            # Create DMG resources and professional DMG for macOS
            if self.target_platform == 'darwin' and self.create_dmg:
                if not self.create_dmg_resources():
                    return False
                if not self.create_professional_dmg():
                    logger.warning("DMG creation failed, but app bundle is available")
            
            # Create additional files
            self.create_installer_script()
            self.create_readme()
            
            # Package distribution
            if not self.package_distribution():
                return False
            
            logger.info("🎉 Build completed successfully!")
            logger.info(f"Distribution available in: {self.dist_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build Personal AI Agent backend executable"
    )
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Include AI models in executable (increases size significantly)"
    )
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="Target platform (default: current platform)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Build debug version with additional logging"
    )
    parser.add_argument(
        "--dmg",
        action="store_true",
        help="Create DMG installer for macOS (only works on macOS)"
    )
    
    args = parser.parse_args()
    
    builder = ExecutableBuilder(
        include_models=args.include_models,
        target_platform=args.platform,
        debug=args.debug,
        create_dmg=args.dmg
    )
    
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()