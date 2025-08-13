#!/usr/bin/env python3
"""
Progressive Model Download Configuration

This module provides configuration and utilities for downloading AI models
progressively, allowing the executable to start without bundling large models.
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger("personal_ai_agent")

# Model configurations
MODEL_CONFIGS = {
    "mistral-7b-instruct-v0.1": {
        "filename": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        "sha256": "61e88e884bb7b8b82b67d73af0c69b23da50c6a1348cbb12947ddcd0b32fc1a9",
        "size_bytes": 4368439808,  # ~4.1GB
        "description": "Mistral 7B Instruct model (4-bit quantized)",
        "required": True,
        "priority": 1,
    },
    "all-MiniLM-L6-v2": {
        "filename": "sentence-transformers-all-MiniLM-L6-v2",
        "url": "sentence-transformers/all-MiniLM-L6-v2",  # Downloaded via sentence-transformers
        "size_bytes": 90000000,  # ~90MB
        "description": "Sentence embeddings model",
        "required": True,
        "priority": 2,
        "download_method": "sentence_transformers",
    }
}

class ModelDownloader:
    """Handles progressive model downloading."""
    
    def __init__(self, models_dir: Path = None, progress_callback=None):
        self.models_dir = models_dir or Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.progress_callback = progress_callback
        
    def check_model_exists(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        config = MODEL_CONFIGS.get(model_name)
        if not config:
            return False
            
        model_path = self.models_dir / config["filename"]
        return model_path.exists()
    
    def verify_model_integrity(self, model_name: str) -> bool:
        """Verify model file integrity using SHA256."""
        config = MODEL_CONFIGS.get(model_name)
        if not config or "sha256" not in config:
            logger.warning(f"No SHA256 hash available for {model_name}")
            return True  # Assume OK if no hash available
            
        model_path = self.models_dir / config["filename"]
        if not model_path.exists():
            return False
            
        logger.info(f"Verifying {model_name} integrity...")
        try:
            sha256_hash = hashlib.sha256()
            with open(model_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_hash = sha256_hash.hexdigest()
            expected_hash = config["sha256"]
            
            if calculated_hash == expected_hash:
                logger.info(f"✅ {model_name} integrity verified")
                return True
            else:
                logger.error(f"❌ {model_name} integrity check failed")
                logger.error(f"Expected: {expected_hash}")
                logger.error(f"Got:      {calculated_hash}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying {model_name}: {e}")
            return False
    
    def download_with_progress(self, url: str, filepath: Path, model_name: str):
        """Download file with progress reporting."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            logger.info(f"Downloading {model_name} ({total_size // 1024 // 1024}MB)...")
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if self.progress_callback:
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            self.progress_callback(model_name, progress, downloaded, total_size)
                        
                        # Log progress every 100MB
                        if downloaded % (100 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            logger.info(f"Downloaded {downloaded // 1024 // 1024}MB ({progress:.1f}%)")
            
            logger.info(f"✅ Downloaded {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            if filepath.exists():
                filepath.unlink()  # Remove partial download
            return False
    
    def download_sentence_transformers_model(self, model_name: str):
        """Download model using sentence-transformers library."""
        try:
            from sentence_transformers import SentenceTransformer
            
            config = MODEL_CONFIGS[model_name]
            model_id = config["url"]
            
            logger.info(f"Downloading {model_name} via sentence-transformers...")
            
            # This will download to the default cache directory
            model = SentenceTransformer(model_id)
            
            logger.info(f"✅ Downloaded {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            return False
    
    def download_model(self, model_name: str) -> bool:
        """Download a specific model."""
        config = MODEL_CONFIGS.get(model_name)
        if not config:
            logger.error(f"Unknown model: {model_name}")
            return False
            
        # Check if already exists and verified
        if self.check_model_exists(model_name):
            if self.verify_model_integrity(model_name):
                logger.info(f"✅ {model_name} already exists and verified")
                return True
            else:
                logger.warning(f"Re-downloading {model_name} due to integrity failure")
        
        # Download based on method
        download_method = config.get("download_method", "direct")
        
        if download_method == "sentence_transformers":
            return self.download_sentence_transformers_model(model_name)
        else:
            # Direct download
            filepath = self.models_dir / config["filename"]
            return self.download_with_progress(config["url"], filepath, model_name)
    
    def download_required_models(self, parallel: bool = True) -> bool:
        """Download all required models."""
        required_models = [
            name for name, config in MODEL_CONFIGS.items() 
            if config.get("required", False)
        ]
        
        # Sort by priority
        required_models.sort(key=lambda x: MODEL_CONFIGS[x].get("priority", 999))
        
        logger.info(f"Downloading {len(required_models)} required models...")
        
        if parallel and len(required_models) > 1:
            # Download multiple models in parallel (for small models)
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for model_name in required_models:
                    # Only parallelize small models
                    if MODEL_CONFIGS[model_name]["size_bytes"] < 500 * 1024 * 1024:  # < 500MB
                        futures.append(executor.submit(self.download_model, model_name))
                    else:
                        # Download large models sequentially
                        if not self.download_model(model_name):
                            return False
                
                # Wait for parallel downloads
                for future in futures:
                    if not future.result():
                        return False
        else:
            # Sequential download
            for model_name in required_models:
                if not self.download_model(model_name):
                    return False
        
        logger.info("✅ All required models downloaded")
        return True
    
    def get_download_status(self) -> Dict[str, Dict]:
        """Get download status for all models."""
        status = {}
        
        for model_name, config in MODEL_CONFIGS.items():
            exists = self.check_model_exists(model_name)
            verified = self.verify_model_integrity(model_name) if exists else False
            
            status[model_name] = {
                "exists": exists,
                "verified": verified,
                "required": config.get("required", False),
                "size_mb": config["size_bytes"] // 1024 // 1024,
                "description": config["description"],
            }
        
        return status
    
    def get_total_download_size(self) -> int:
        """Get total size of all required models in bytes."""
        total = 0
        for model_name, config in MODEL_CONFIGS.items():
            if config.get("required", False) and not self.check_model_exists(model_name):
                total += config["size_bytes"]
        return total

def create_download_script():
    """Create standalone download script for users."""
    script_content = '''#!/usr/bin/env python3
"""
Personal AI Agent - Model Downloader

This script downloads the required AI models for the Personal AI Agent.
Run this script after installing the executable to enable AI features.
"""

import sys
from pathlib import Path

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from model_download_config import ModelDownloader, MODEL_CONFIGS
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    def progress_callback(model_name, progress, downloaded, total):
        """Progress callback for downloads."""
        mb_downloaded = downloaded // 1024 // 1024
        mb_total = total // 1024 // 1024
        print(f"\\r{model_name}: {progress:.1f}% ({mb_downloaded}MB/{mb_total}MB)", end="", flush=True)
    
    def main():
        print("🤖 Personal AI Agent - Model Downloader")
        print("=" * 50)
        
        downloader = ModelDownloader(progress_callback=progress_callback)
        
        # Show download status
        status = downloader.get_download_status()
        total_size_mb = downloader.get_total_download_size() // 1024 // 1024
        
        print("📋 Model Status:")
        for model_name, info in status.items():
            if info["required"]:
                status_icon = "✅" if info["exists"] and info["verified"] else "❌"
                print(f"  {status_icon} {model_name} ({info['size_mb']}MB) - {info['description']}")
        
        if total_size_mb > 0:
            print(f"\\n📥 Total download size: {total_size_mb}MB")
            
            response = input("\\nProceed with download? (y/N): ")
            if response.lower() != 'y':
                print("Download cancelled")
                return 1
            
            print("\\n🔽 Starting downloads...")
            if downloader.download_required_models():
                print("\\n🎉 All models downloaded successfully!")
                print("You can now run the Personal AI Agent with full AI capabilities.")
                return 0
            else:
                print("\\n❌ Download failed. Please check your internet connection and try again.")
                return 1
        else:
            print("\\n✅ All required models are already downloaded!")
            return 0
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"Error: {e}")
    print("Please ensure you're running this script from the Personal AI Agent directory.")
    sys.exit(1)
'''
    
    return script_content

def main():
    """Test the model download system."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    downloader = ModelDownloader()
    status = downloader.get_download_status()
    
    print("📋 Model Download Status:")
    print("=" * 50)
    
    for model_name, info in status.items():
        status_icon = "✅" if info["exists"] and info["verified"] else "❌"
        required_text = " (REQUIRED)" if info["required"] else ""
        print(f"{status_icon} {model_name}{required_text}")
        print(f"    Size: {info['size_mb']}MB")
        print(f"    Description: {info['description']}")
        print()

if __name__ == "__main__":
    main()