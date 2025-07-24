#!/usr/bin/env python3
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
        print(f"\r{model_name}: {progress:.1f}% ({mb_downloaded}MB/{mb_total}MB)", end="", flush=True)
    
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
            print(f"\n📥 Total download size: {total_size_mb}MB")
            
            response = input("\nProceed with download? (y/N): ")
            if response.lower() != 'y':
                print("Download cancelled")
                return 1
            
            print("\n🔽 Starting downloads...")
            if downloader.download_required_models():
                print("\n🎉 All models downloaded successfully!")
                print("You can now run the Personal AI Agent with full AI capabilities.")
                return 0
            else:
                print("\n❌ Download failed. Please check your internet connection and try again.")
                return 1
        else:
            print("\n✅ All required models are already downloaded!")
            return 0
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"Error: {e}")
    print("Please ensure you're running this script from the Personal AI Agent directory.")
    sys.exit(1)
