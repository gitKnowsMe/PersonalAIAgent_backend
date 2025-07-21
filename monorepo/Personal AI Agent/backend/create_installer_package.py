#!/usr/bin/env python3
"""
Complete Installer Package Creator for Personal AI Agent

This script creates a comprehensive installer package that includes:
- The executable backend
- Progressive model downloader
- Database setup automation
- Configuration templates
- User documentation
"""

import os
import sys
import shutil
import subprocess
import json
import platform
from pathlib import Path
from datetime import datetime
import logging
import zipfile
import tarfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstallerPackageCreator:
    def __init__(self, platform_target=None, include_models=False):
        self.platform_target = platform_target or platform.system().lower()
        self.include_models = include_models
        self.base_dir = Path(__file__).parent
        self.package_dir = self.base_dir / "installer_package"
        self.dist_dir = self.base_dir / "dist"
        
    def clean_package_directory(self):
        """Clean the package directory."""
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
        self.package_dir.mkdir(parents=True)
        logger.info(f"Created clean package directory: {self.package_dir}")
    
    def copy_executable(self):
        """Copy the built executable to package directory."""
        logger.info("Copying executable...")
        
        # Determine executable name
        if self.platform_target == "windows":
            exe_name = "PersonalAIAgent.exe"
        elif self.platform_target == "darwin":
            exe_name = "PersonalAIAgent.app" if (self.dist_dir / "PersonalAIAgent.app").exists() else "PersonalAIAgent"
        else:
            exe_name = "PersonalAIAgent"
        
        exe_path = self.dist_dir / exe_name
        if not exe_path.exists():
            logger.error(f"Executable not found: {exe_path}")
            return False
        
        if exe_path.is_dir():
            # Copy directory (like .app bundle)
            shutil.copytree(exe_path, self.package_dir / exe_name)
        else:
            # Copy file
            shutil.copy2(exe_path, self.package_dir / exe_name)
        
        logger.info(f"Copied executable: {exe_name}")
        return True
    
    def create_model_downloader(self):
        """Create the model downloader script."""
        logger.info("Creating model downloader...")
        
        from model_download_config import create_download_script
        
        download_script = create_download_script()
        
        download_path = self.package_dir / "download_models.py"
        with open(download_path, 'w') as f:
            f.write(download_script)
        
        # Copy the config file
        config_path = self.base_dir / "model_download_config.py"
        if config_path.exists():
            shutil.copy2(config_path, self.package_dir / "model_download_config.py")
        
        logger.info("Created model downloader script")
    
    def create_installer_script(self):
        """Create the main installer script."""
        logger.info("Creating installer script...")
        
        installer_content = f'''#!/usr/bin/env python3
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
import json
import time

# Setup logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "install.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("installer")

logger = setup_logging()

def check_system_requirements():
    """Check if system meets requirements."""
    logger.info("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required for setup")
        logger.error("The executable will work without Python, but setup requires it")
        return False
    
    # Check available disk space
    try:
        import shutil
        free_bytes = shutil.disk_usage('.').free
        free_gb = free_bytes / (1024**3)
        
        required_gb = 15 if {str(self.include_models).lower()} else 5
        
        if free_gb < required_gb:
            logger.error(f"Insufficient disk space. Need {{required_gb}}GB, have {{free_gb:.1f}}GB")
            return False
        
        logger.info(f"Available disk space: {{free_gb:.1f}}GB")
    except Exception as e:
        logger.warning(f"Could not check disk space: {{e}}")
    
    return True

def create_directories():
    """Create necessary directories."""
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
        "backups",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {{directory}}")

def create_environment_config():
    """Create environment configuration."""
    env_file = Path(".env")
    
    if env_file.exists():
        logger.info(".env file already exists, keeping existing configuration")
        return
    
    # Generate secure secret key
    import secrets
    secret_key = secrets.token_hex(32)
    
    env_content = f'''# Personal AI Agent Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Portable Mode Configuration
PORTABLE_MODE=true
DATABASE_URL=sqlite:///data/personal_ai_agent_portable.db

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=false
SECRET_KEY={{secret_key}}
API_V1_STR=/api

# CORS Configuration (for frontend access)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8080

# AI Model Configuration
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL={"true" if self.platform_target == "darwin" else "false"}
METAL_N_GPU_LAYERS=1

# File Upload Configuration
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,txt,docx,xlsx

# Gmail OAuth Configuration (Optional - configure for email features)
# Get these from https://console.cloud.google.com/
GMAIL_CLIENT_ID=your-gmail-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
GMAIL_MAX_EMAILS_PER_SYNC=1000
GMAIL_DEFAULT_SYNC_LIMIT=100

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/personal_ai_agent.log
'''
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info("Created .env configuration file")

def setup_database():
    """Initialize the SQLite database."""
    logger.info("Setting up database...")
    
    # Set environment variables for portable mode
    os.environ['PORTABLE_MODE'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///data/personal_ai_agent_portable.db'
    
    try:
        # The executable will handle database initialization
        logger.info("Database will be initialized on first run")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {{e}}")
        return False

def create_shortcuts():
    """Create platform-specific shortcuts."""
    logger.info("Creating shortcuts...")
    
    system = platform.system().lower()
    
    if system == "windows":
        create_windows_shortcuts()
    elif system == "darwin":
        create_macos_shortcuts()
    elif system == "linux":
        create_linux_shortcuts()

def create_windows_shortcuts():
    """Create Windows shortcuts and start menu entry."""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        start_menu = winshell.start_menu()
        
        # Desktop shortcut
        shortcut = Dispatch('WScript.Shell').CreateShortCut(
            os.path.join(desktop, "Personal AI Agent.lnk")
        )
        shortcut.Targetpath = str(Path.cwd() / "PersonalAIAgent.exe")
        shortcut.WorkingDirectory = str(Path.cwd())
        shortcut.IconLocation = shortcut.Targetpath
        shortcut.save()
        
        logger.info("Created Windows shortcuts")
    except Exception as e:
        logger.warning(f"Could not create Windows shortcuts: {{e}}")

def create_macos_shortcuts():
    """Create macOS shortcuts and app registration."""
    logger.info("macOS shortcuts created with .app bundle")

def create_linux_shortcuts():
    """Create Linux desktop entry."""
    try:
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_entry = f'''[Desktop Entry]
Name=Personal AI Agent
Comment=Privacy-first AI assistant with local processing
Exec={Path.cwd() / "PersonalAIAgent"}
Icon={Path.cwd() / "icon.png"}
Terminal=false
Type=Application
Categories=Office;Productivity;
'''
        
        desktop_file = desktop_dir / "personal-ai-agent.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
        
        # Make executable
        os.chmod(desktop_file, 0o755)
        
        logger.info("Created Linux desktop entry")
    except Exception as e:
        logger.warning(f"Could not create Linux desktop entry: {{e}}")

def test_installation():
    """Test the installation."""
    logger.info("Testing installation...")
    
    # Check if executable exists
    system = platform.system().lower()
    if system == "windows":
        exe_name = "PersonalAIAgent.exe"
    elif system == "darwin":
        exe_name = "PersonalAIAgent.app"
        if not Path(exe_name).exists():
            exe_name = "PersonalAIAgent"
    else:
        exe_name = "PersonalAIAgent"
    
    exe_path = Path(exe_name)
    if not exe_path.exists():
        logger.error(f"Executable not found: {{exe_name}}")
        return False
    
    # Check configuration
    if not Path(".env").exists():
        logger.error(".env file not found")
        return False
    
    # Check directories
    required_dirs = ["data", "logs", "models"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.error(f"Required directory missing: {{dir_name}}")
            return False
    
    logger.info("✅ Installation test passed")
    return True

def main():
    """Main installer function."""
    print("🚀 Personal AI Agent Installer")
    print("=" * 50)
    print(f"Platform: {{platform.system()}} {{platform.machine()}}")
    print(f"Python: {{sys.version.split()[0]}}")
    print()
    
    if not check_system_requirements():
        print("❌ System requirements not met")
        return 1
    
    print("📁 Creating directories...")
    create_directories()
    
    print("⚙️  Setting up configuration...")
    create_environment_config()
    
    print("🗄️ Setting up database...")
    setup_database()
    
    print("🔗 Creating shortcuts...")
    create_shortcuts()
    
    print("🧪 Testing installation...")
    if not test_installation():
        print("❌ Installation test failed")
        return 1
    
    print()
    print("🎉 Installation completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Configure Gmail OAuth in .env (optional for email features)")
    print("2. Download AI models: python download_models.py")
    
    # Determine how to run the executable
    system = platform.system().lower()
    if system == "windows":
        run_command = ".\\\\PersonalAIAgent.exe"
    elif system == "darwin":
        if Path("PersonalAIAgent.app").exists():
            run_command = "open PersonalAIAgent.app"
        else:
            run_command = "./PersonalAIAgent"
    else:
        run_command = "./PersonalAIAgent"
    
    print(f"3. Start the application: {{run_command}}")
    print()
    print("🌐 The web interface will be available at: http://localhost:8000")
    print()
    print("📖 For help and documentation, see README.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        installer_path = self.package_dir / "install.py"
        with open(installer_path, 'w') as f:
            f.write(installer_content)
        
        # Make executable on Unix systems
        if self.platform_target != "windows":
            os.chmod(installer_path, 0o755)
        
        logger.info("Created installer script")
    
    def create_readme(self):
        """Create comprehensive README."""
        logger.info("Creating README...")
        
        readme_content = f'''# Personal AI Agent - Portable Installation

Welcome to Personal AI Agent, a privacy-first AI assistant that processes everything locally on your computer.

## 🚀 Quick Start

### 1. Install
Run the installer to set up the application:

```bash
python install.py
```

### 2. Download Models
Download the required AI models (this will download ~4GB):

```bash
python download_models.py
```

### 3. Run
Start the application:

**Windows:**
```cmd
PersonalAIAgent.exe
```

**macOS:**
```bash
open PersonalAIAgent.app
# OR (if no .app bundle)
./PersonalAIAgent
```

**Linux:**
```bash
./PersonalAIAgent
```

### 4. Access
Open your browser and go to: http://localhost:8000

## 📋 Features

- 🔒 **Complete Privacy**: All AI processing happens locally, no data sent to external services
- 📄 **PDF Intelligence**: Upload and query PDF documents with smart categorization
- 📧 **Gmail Integration**: Search and analyze your emails with AI assistance
- 🤖 **Local AI**: Mistral 7B model provides intelligent responses
- 🔍 **Semantic Search**: Vector-based search across all your documents and emails
- 🌐 **Web Interface**: Clean, responsive web interface for all interactions
- ⚡ **Fast Setup**: Single executable with progressive model downloading

## 🔧 System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (64-bit)
- **RAM**: 8GB minimum, 16GB recommended for optimal performance
- **Storage**: 15GB free space (10GB for models, 5GB for application and data)
- **Internet**: Required for initial model download and Gmail integration
- **Python**: 3.8+ required for installer and model downloader only

## ⚙️ Configuration

### Basic Configuration
Edit the `.env` file to customize settings:

```bash
# Server settings
PORT=8000                    # Change port if needed
HOST=localhost              # Change to 0.0.0.0 for network access

# Model settings
USE_METAL=true              # Enable Metal acceleration on macOS
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf

# Upload limits
MAX_FILE_SIZE=10485760      # 10MB default
```

### Gmail Integration (Optional)
To enable Gmail features:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download the credentials and update `.env`:

```bash
GMAIL_CLIENT_ID=your-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
```

## 📂 Directory Structure

```
PersonalAIAgent/
├── PersonalAIAgent.exe         # Main executable (Windows)
├── PersonalAIAgent.app/        # App bundle (macOS)
├── PersonalAIAgent             # Executable (Linux/macOS)
├── install.py                  # Installer script
├── download_models.py          # Model downloader
├── .env                        # Configuration file
├── README.md                   # This file
├── data/                       # Application data
│   ├── uploads/               # Uploaded PDF files
│   ├── vector_db/             # Vector search indices
│   ├── emails/                # Gmail cache
│   └── personal_ai_agent_portable.db  # SQLite database
├── models/                     # AI models
│   └── mistral-7b-instruct-v0.1.Q4_K_M.gguf
├── logs/                       # Application logs
└── backups/                    # Data backups
```

## 🔍 Usage Examples

### PDF Document Processing
1. Click "Upload Document" in the web interface
2. Select a PDF file (financial statements, research papers, contracts, etc.)
3. The system will automatically categorize and process the document
4. Ask questions about the document content

### Gmail Integration
1. Configure Gmail OAuth credentials in `.env`
2. Click "Connect Gmail" in the web interface
3. Authorize access to your Gmail account
4. Sync emails and ask questions about your email content

### Combined Queries
Ask questions that span both your documents and emails:
- "Show me expenses from my bank statements and related receipts in my emails"
- "Find project updates in my emails and related documents"

## 🔧 Troubleshooting

### Application Won't Start
- **Check logs**: Look in `logs/personal_ai_agent.log` for error messages
- **Verify installation**: Run `python install.py` again
- **Check port**: Ensure port 8000 is not in use by another application
- **Permissions**: Ensure the executable has proper permissions

### Models Not Working
- **Download models**: Run `python download_models.py`
- **Check path**: Verify `LLM_MODEL_PATH` in `.env` points to the correct file
- **File integrity**: Re-download models if they appear corrupted
- **Memory**: Ensure you have enough RAM (8GB minimum)

### Gmail Integration Issues
- **OAuth setup**: Verify credentials in Google Cloud Console
- **Redirect URI**: Ensure it matches exactly in both Google Console and `.env`
- **Network**: Check firewall settings allow local server access
- **Scope permissions**: Re-authorize if Gmail sync fails

### Performance Issues
- **Memory**: Close other applications to free up RAM
- **Metal acceleration**: Enable `USE_METAL=true` on macOS for better performance
- **Storage**: Ensure sufficient disk space for vector indices
- **CPU**: Consider reducing concurrent operations for slower systems

### Database Issues
- **Backup first**: Copy `data/personal_ai_agent_portable.db` before troubleshooting
- **Reset database**: Delete the database file and restart the application
- **Permissions**: Ensure write access to the `data/` directory
- **Corruption**: Check logs for SQLite error messages

## 🔒 Privacy & Security

This application is designed with privacy as the top priority:

- **Local Processing**: All AI processing happens on your computer
- **No External APIs**: No data sent to OpenAI, Google AI, or other cloud services
- **Local Storage**: All documents and emails are stored locally in SQLite
- **Optional Gmail**: Gmail integration is optional and only caches data locally
- **No Telemetry**: No usage data or analytics are collected or transmitted

## 📊 Performance Notes

- **Initial Startup**: First run may take 30-60 seconds to load models
- **Model Loading**: Mistral 7B requires ~4GB RAM when loaded
- **Processing Speed**: Document processing time depends on file size and complexity
- **Vector Search**: Search performance improves with Metal/GPU acceleration
- **Concurrent Users**: Single-user application, not designed for multiple concurrent users

## 🔄 Updates

To update the application:
1. Download the new version
2. Backup your `data/` directory
3. Replace the executable with the new version
4. Run `python install.py` to update configuration if needed
5. Restore your `data/` directory

## 📞 Support

### Self-Help Resources
- **Logs**: Check `logs/personal_ai_agent.log` for detailed error information
- **Configuration**: Review `.env` file for proper settings
- **Models**: Ensure models are downloaded and accessible
- **System Resources**: Monitor RAM and disk space usage

### Common Issues
- **Port conflicts**: Change `PORT` in `.env` if 8000 is in use
- **Model download failures**: Check internet connection and disk space
- **Gmail authentication**: Verify OAuth credentials in Google Cloud Console
- **Performance issues**: Ensure adequate system resources

### Data Recovery
- **Database**: SQLite file at `data/personal_ai_agent_portable.db`
- **Documents**: PDF files in `data/uploads/`
- **Vector indices**: Search data in `data/vector_db/`
- **Configuration**: Settings in `.env` file

## 📄 License & Credits

Personal AI Agent is built with these excellent open-source projects:
- **FastAPI**: Web framework
- **Mistral 7B**: Local language model
- **SQLAlchemy**: Database toolkit
- **FAISS**: Vector similarity search
- **LangChain**: LLM integration framework
- **sentence-transformers**: Text embeddings

---

**Built on**: {datetime.now().strftime('%Y-%m-%d')}  
**Platform**: {self.platform_target}  
**Includes Models**: {'Yes' if self.include_models else 'No'}  
**Version**: 1.0.0

For the latest updates and documentation, visit the project repository.
'''
        
        readme_path = self.package_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info("Created comprehensive README")
    
    def create_uninstaller(self):
        """Create uninstaller script."""
        logger.info("Creating uninstaller...")
        
        uninstaller_content = '''#!/usr/bin/env python3
"""
Personal AI Agent Uninstaller

This script removes the Personal AI Agent from your system.
"""

import os
import sys
import shutil
from pathlib import Path
import platform

def main():
    print("🗑️  Personal AI Agent Uninstaller")
    print("=" * 40)
    
    current_dir = Path.cwd()
    
    print("This will remove:")
    print(f"  • Application files in: {current_dir}")
    print(f"  • All data in data/ directory")
    print(f"  • All models in models/ directory")
    print(f"  • Configuration files")
    print(f"  • Logs")
    print()
    print("⚠️  WARNING: This will permanently delete all your documents,")
    print("   email cache, and settings. This cannot be undone!")
    print()
    
    # Confirm deletion
    response = input("Are you sure you want to uninstall? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Uninstall cancelled.")
        return 0
    
    # Final confirmation
    response = input("Last chance! Type 'DELETE EVERYTHING' to confirm: ")
    if response != 'DELETE EVERYTHING':
        print("Uninstall cancelled.")
        return 0
    
    print("\\n🗑️  Removing Personal AI Agent...")
    
    # Remove directories
    dirs_to_remove = ['data', 'models', 'logs', 'backups']
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  ✅ Removed {dir_name}/")
    
    # Remove files
    files_to_remove = [
        '.env',
        'download_models.py',
        'model_download_config.py',
        'install.py',
        'README.md',
    ]
    
    for file_name in files_to_remove:
        file_path = Path(file_name)
        if file_path.exists():
            file_path.unlink()
            print(f"  ✅ Removed {file_name}")
    
    # Remove executable
    system = platform.system().lower()
    if system == "windows":
        exe_names = ["PersonalAIAgent.exe"]
    elif system == "darwin":
        exe_names = ["PersonalAIAgent.app", "PersonalAIAgent"]
    else:
        exe_names = ["PersonalAIAgent"]
    
    for exe_name in exe_names:
        exe_path = Path(exe_name)
        if exe_path.exists():
            if exe_path.is_dir():
                shutil.rmtree(exe_path)
            else:
                exe_path.unlink()
            print(f"  ✅ Removed {exe_name}")
    
    # Remove shortcuts (best effort)
    try:
        if system == "windows":
            import winshell
            desktop = winshell.desktop()
            shortcut_path = Path(desktop) / "Personal AI Agent.lnk"
            if shortcut_path.exists():
                shortcut_path.unlink()
                print("  ✅ Removed desktop shortcut")
        elif system == "linux":
            desktop_file = Path.home() / ".local" / "share" / "applications" / "personal-ai-agent.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
                print("  ✅ Removed desktop entry")
    except Exception:
        pass  # Ignore errors removing shortcuts
    
    print("\\n🎉 Personal AI Agent has been completely removed.")
    print("This directory now only contains the uninstaller script.")
    print("You can safely delete this entire directory.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        uninstaller_path = self.package_dir / "uninstall.py"
        with open(uninstaller_path, 'w') as f:
            f.write(uninstaller_content)
        
        # Make executable on Unix systems
        if self.platform_target != "windows":
            os.chmod(uninstaller_path, 0o755)
        
        logger.info("Created uninstaller script")
    
    def copy_models_if_included(self):
        """Copy models if they should be included."""
        if not self.include_models:
            logger.info("Skipping model inclusion (--include-models not specified)")
            return
        
        logger.info("Including AI models in package...")
        
        models_dir = self.base_dir / "models"
        if not models_dir.exists():
            logger.warning("Models directory not found - models will need to be downloaded")
            return
        
        package_models_dir = self.package_dir / "models"
        package_models_dir.mkdir(exist_ok=True)
        
        model_files = list(models_dir.glob("*.gguf"))
        if not model_files:
            logger.warning("No .gguf model files found")
            return
        
        total_size = 0
        for model_file in model_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            shutil.copy2(model_file, package_models_dir / model_file.name)
            logger.info(f"Included model: {model_file.name} ({size_mb:.1f}MB)")
        
        logger.info(f"Total models size: {total_size:.1f}MB")
    
    def create_package_info(self):
        """Create package information file."""
        logger.info("Creating package info...")
        
        package_info = {
            "name": "Personal AI Agent",
            "version": "1.0.0",
            "platform": self.platform_target,
            "includes_models": self.include_models,
            "build_date": datetime.now().isoformat(),
            "build_system": {
                "platform": platform.platform(),
                "python": sys.version,
                "machine": platform.machine(),
            },
            "contents": {
                "executable": True,
                "installer": True,
                "model_downloader": True,
                "documentation": True,
                "uninstaller": True,
                "models": self.include_models,
            },
            "requirements": {
                "python": "3.8+ (for installer only)",
                "ram": "8GB minimum",
                "storage": "15GB (10GB for models)",
                "os": f"{self.platform_target} 64-bit",
            }
        }
        
        info_path = self.package_dir / "package_info.json"
        with open(info_path, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        logger.info("Created package info file")
    
    def create_archive(self):
        """Create final distribution archive."""
        logger.info("Creating distribution archive...")
        
        # Determine archive format and name
        if self.platform_target == "windows":
            archive_format = "zip"
            archive_ext = "zip"
        else:
            archive_format = "gztar"
            archive_ext = "tar.gz"
        
        archive_name = f"PersonalAIAgent-{self.platform_target}-{'with-models' if self.include_models else 'no-models'}"
        archive_path = self.base_dir / f"{archive_name}.{archive_ext}"
        
        # Remove existing archive
        if archive_path.exists():
            archive_path.unlink()
        
        # Create archive
        if archive_format == "zip":
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in self.package_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.package_dir)
                        zf.write(file_path, arcname)
        else:
            with tarfile.open(archive_path, 'w:gz') as tf:
                tf.add(self.package_dir, arcname=archive_name)
        
        # Get archive size
        archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"Created archive: {archive_path.name}")
        logger.info(f"Archive size: {archive_size_mb:.1f}MB")
        
        return archive_path
    
    def create_installer_package(self):
        """Create the complete installer package."""
        logger.info("🏗️  Creating Personal AI Agent installer package")
        logger.info("=" * 60)
        
        try:
            # Clean and prepare
            self.clean_package_directory()
            
            # Copy executable
            if not self.copy_executable():
                return False
            
            # Create installation components
            self.create_model_downloader()
            self.create_installer_script()
            self.create_readme()
            self.create_uninstaller()
            
            # Copy models if requested
            self.copy_models_if_included()
            
            # Create package metadata
            self.create_package_info()
            
            # Create final archive
            archive_path = self.create_archive()
            
            logger.info("🎉 Installer package created successfully!")
            logger.info(f"📦 Package: {archive_path}")
            logger.info(f"📁 Contents: {self.package_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create installer package: {e}")
            return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create installer package for Personal AI Agent"
    )
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="Target platform (default: current platform)"
    )
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Include AI models in package (increases size significantly)"
    )
    
    args = parser.parse_args()
    
    creator = InstallerPackageCreator(
        platform_target=args.platform,
        include_models=args.include_models
    )
    
    success = creator.create_installer_package()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()