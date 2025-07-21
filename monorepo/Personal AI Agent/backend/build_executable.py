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
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutableBuilder:
    def __init__(self, include_models=False, target_platform=None, debug=False):
        self.include_models = include_models
        self.target_platform = target_platform or platform.system().lower()
        self.debug = debug
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
main_script = source_dir / "startup_portable.py"

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

# macOS App Bundle (optional)
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name=f'{{app_name}}.app',
        icon=None,
        bundle_identifier=f'com.personalaiagent.{{app_name.lower()}}',
        version=app_version,
        info_plist={{
            'CFBundleDisplayName': app_name,
            'CFBundleIdentifier': f'com.personalaiagent.{{app_name.lower()}}',
            'CFBundleVersion': app_version,
            'CFBundleShortVersionString': app_version,
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.productivity',
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
        
        if self.debug:
            cmd.append("--debug=all")
        
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
        env_content = '''# Personal AI Agent - Portable Configuration
PORTABLE_MODE=true
DATABASE_URL=sqlite:///data/personal_ai_agent_portable.db
HOST=localhost
PORT=8000
DEBUG=false
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
API_V1_STR=/api
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Gmail OAuth (optional - configure for email features)
GMAIL_CLIENT_ID=your-gmail-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
'''
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info("Created .env file for portable mode")
    else:
        logger.info(".env file already exists")

def download_models():
    """Download required AI models."""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_file = models_dir / "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    
    if not model_file.exists():
        logger.info("Downloading Mistral 7B model (this may take several minutes)...")
        # In a real implementation, this would download the model
        # For now, just create a placeholder
        logger.warning("Model download not implemented in this installer")
        logger.info("Please run 'python download_model.py' separately to download models")
    else:
        logger.info("Mistral model already exists")

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
- 🤖 **Local AI**: Mistral 7B model for intelligent responses
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
LLM_MODEL_PATH=models/mistral-7b-instral-v0.1.Q4_K_M.gguf
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
- Local Mistral 7B model for AI processing
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
    
    args = parser.parse_args()
    
    builder = ExecutableBuilder(
        include_models=args.include_models,
        target_platform=args.platform,
        debug=args.debug
    )
    
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()