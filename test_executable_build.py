#!/usr/bin/env python3
"""
Test script for validating the executable build process.

This script runs various checks to ensure the build will succeed.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version < (3, 8):
        logger.error(f"Python {version.major}.{version.minor} not supported. Requires 3.8+")
        return False
    logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pydantic_settings',
        'langchain',
        'faiss',
        'sentence_transformers',
        'llama_cpp',
        'bcrypt',
        'passlib',
        'python_jose',
        'python_multipart',
        'aiofiles',
        'httpx',
        'google_auth_oauthlib',
        'googleapiclient',
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            logger.info(f"✅ {package}")
        except ImportError:
            logger.error(f"❌ {package} - not installed")
            missing.append(package)
    
    if missing:
        logger.error(f"Missing packages: {', '.join(missing)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_pyinstaller():
    """Check if PyInstaller is available."""
    try:
        import PyInstaller
        logger.info(f"✅ PyInstaller {PyInstaller.__version__}")
        return True
    except ImportError:
        logger.warning("❌ PyInstaller not installed")
        logger.info("Will be installed automatically during build")
        return True

def check_app_structure():
    """Check if the application structure is valid."""
    base_dir = Path(__file__).parent
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/db/models.py",
        "app/db/database_portable.py",
        "app/db/models_portable.py",
        "startup_portable.py",
        "requirements.txt",
    ]
    
    missing = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path}")
        else:
            logger.error(f"❌ {file_path} - missing")
            missing.append(file_path)
    
    if missing:
        logger.error(f"Missing files: {', '.join(missing)}")
        return False
    
    return True

def check_static_files():
    """Check if static frontend files exist."""
    base_dir = Path(__file__).parent
    static_dir = base_dir / "static"
    
    if not static_dir.exists():
        logger.warning("❌ static/ directory not found")
        logger.warning("Frontend will not be included in executable")
        return False
    
    required_static = [
        "index.html",
        "js/app.js",
        "css/style.css",
    ]
    
    missing = []
    for file_path in required_static:
        full_path = static_dir / file_path
        if full_path.exists():
            logger.info(f"✅ static/{file_path}")
        else:
            logger.warning(f"⚠️  static/{file_path} - missing")
            missing.append(file_path)
    
    if missing:
        logger.warning("Some static files missing - frontend may not work properly")
    
    return True

def check_models():
    """Check if AI models are available."""
    base_dir = Path(__file__).parent
    models_dir = base_dir / "models"
    
    if not models_dir.exists():
        logger.warning("❌ models/ directory not found")
        logger.warning("AI models will need to be downloaded separately")
        return False
    
    model_files = list(models_dir.glob("*.gguf"))
    if not model_files:
        logger.warning("❌ No .gguf model files found")
        logger.warning("Run: python download_model.py")
        return False
    
    for model_file in model_files:
        size_mb = model_file.stat().st_size / (1024 * 1024)
        logger.info(f"✅ {model_file.name} ({size_mb:.1f} MB)")
    
    return True

def test_imports():
    """Test critical imports that might fail in executable."""
    critical_imports = [
        'app.main',
        'app.core.config',
        'app.db.database_portable',
        'app.db.models_portable',
        'startup_portable',
    ]
    
    failed = []
    for module_name in critical_imports:
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ Import {module_name}")
        except Exception as e:
            logger.error(f"❌ Import {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        logger.error(f"Failed imports: {', '.join(failed)}")
        return False
    
    return True

def test_database_portable():
    """Test portable database configuration."""
    try:
        # Set portable mode
        os.environ['PORTABLE_MODE'] = 'true'
        os.environ['DATABASE_URL'] = 'sqlite:///test_portable.db'
        
        from app.db.database_portable import get_database_config, get_database_info
        
        config = get_database_config()
        info = get_database_info()
        
        logger.info(f"✅ Database type: {info['type']}")
        logger.info(f"✅ Portable mode: {info['portable_mode']}")
        
        # Clean up test db
        test_db = Path("test_portable.db")
        if test_db.exists():
            test_db.unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Portable database test failed: {e}")
        return False

def check_disk_space():
    """Check available disk space for build."""
    try:
        import shutil
        free_bytes = shutil.disk_usage('.').free
        free_gb = free_bytes / (1024**3)
        
        if free_gb < 5:
            logger.error(f"❌ Only {free_gb:.1f}GB free space. Need at least 5GB for build")
            return False
        
        logger.info(f"✅ Available space: {free_gb:.1f}GB")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Could not check disk space: {e}")
        return True

def main():
    """Run all validation checks."""
    logger.info("🔍 Personal AI Agent - Executable Build Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("PyInstaller", check_pyinstaller),
        ("App Structure", check_app_structure),
        ("Static Files", check_static_files),
        ("AI Models", check_models),
        ("Critical Imports", test_imports),
        ("Portable Database", test_database_portable),
        ("Disk Space", check_disk_space),
    ]
    
    results = []
    for check_name, check_func in checks:
        logger.info(f"\n🔍 Checking {check_name}...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    logger.info("\n" + "=" * 60)
    logger.info("📋 VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:<8} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 60)
    logger.info(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All checks passed! Ready to build executable")
        return 0
    elif failed <= 2:
        logger.warning("⚠️  Some checks failed but build may still succeed")
        return 0
    else:
        logger.error("❌ Too many checks failed. Fix issues before building")
        return 1

if __name__ == "__main__":
    sys.exit(main())