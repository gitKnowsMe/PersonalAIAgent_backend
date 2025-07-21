#!/usr/bin/env python3
"""
Auto-Updater for Personal AI Agent Backend

This module handles automatic updates of the Personal AI Agent backend executable,
ensuring users always have the latest features and security updates.
"""

import os
import sys
import json
import requests
import hashlib
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from packaging import version
import time
from datetime import datetime, timedelta

logger = logging.getLogger("personal_ai_agent.updater")

class AutoUpdater:
    def __init__(self, 
                 current_version: str = "1.0.0",
                 github_repo: str = "your-username/your-repo",
                 update_check_interval: int = 86400,  # 24 hours
                 auto_update: bool = False):
        """
        Initialize the auto-updater.
        
        Args:
            current_version: Current version of the application
            github_repo: GitHub repository in format "owner/repo"
            update_check_interval: How often to check for updates (seconds)
            auto_update: Whether to automatically download and install updates
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.update_check_interval = update_check_interval
        self.auto_update = auto_update
        
        # Paths
        self.app_dir = Path.cwd()
        self.temp_dir = Path(tempfile.gettempdir()) / "personal_ai_agent_updates"
        self.config_file = self.app_dir / "update_config.json"
        self.backup_dir = self.app_dir / "backups" / "updates"
        
        # Create directories
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load update configuration."""
        default_config = {
            "auto_check": True,
            "auto_download": False,
            "auto_install": False,
            "last_check": None,
            "update_channel": "stable",  # stable, beta, dev
            "skip_versions": [],
            "backup_count": 5,
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                default_config.update(config)
                return default_config
            except Exception as e:
                logger.warning(f"Failed to load update config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save update configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save update config: {e}")
    
    def get_platform_info(self) -> Tuple[str, str]:
        """Get current platform information."""
        import platform
        
        system = platform.system().lower()
        if system == "darwin":
            return "macos", "zip"
        elif system == "windows":
            return "windows", "zip"
        elif system == "linux":
            return "linux", "tar.gz"
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check for available updates.
        
        Returns:
            Dict with update information or None if no updates available
        """
        try:
            logger.info("Checking for updates...")
            
            # Get latest release info from GitHub
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip('v')
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                # Check if version is in skip list
                if latest_version in self.config.get("skip_versions", []):
                    logger.info(f"Update {latest_version} is available but skipped by user")
                    return None
                
                platform_name, archive_format = self.get_platform_info()
                
                # Find appropriate download asset
                download_asset = None
                for asset in release_data["assets"]:
                    asset_name = asset["name"].lower()
                    if (platform_name in asset_name and 
                        "no-models" in asset_name and 
                        asset_name.endswith(archive_format)):
                        download_asset = asset
                        break
                
                if not download_asset:
                    logger.warning(f"No compatible download found for {platform_name}")
                    return None
                
                update_info = {
                    "version": latest_version,
                    "current_version": self.current_version,
                    "release_notes": release_data.get("body", ""),
                    "download_url": download_asset["browser_download_url"],
                    "download_size": download_asset["size"],
                    "published_at": release_data["published_at"],
                    "is_prerelease": release_data["prerelease"],
                    "asset_name": download_asset["name"],
                }
                
                logger.info(f"Update available: {self.current_version} -> {latest_version}")
                return update_info
            else:
                logger.info(f"No updates available (current: {self.current_version}, latest: {latest_version})")
                return None
                
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None
        finally:
            # Update last check time
            self.config["last_check"] = datetime.now().isoformat()
            self.save_config()
    
    def download_update(self, update_info: Dict) -> Optional[Path]:
        """
        Download update package.
        
        Args:
            update_info: Update information from check_for_updates()
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            download_url = update_info["download_url"]
            asset_name = update_info["asset_name"]
            download_path = self.temp_dir / asset_name
            
            logger.info(f"Downloading update: {asset_name}")
            logger.info(f"Size: {update_info['download_size'] / 1024 / 1024:.1f} MB")
            
            # Download with progress
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10MB
                        if downloaded % (10 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            logger.info(f"Download progress: {downloaded / 1024 / 1024:.1f}MB ({progress:.1f}%)")
            
            # Verify download size
            if total_size > 0 and download_path.stat().st_size != total_size:
                logger.error("Download size mismatch")
                download_path.unlink()
                return None
            
            logger.info(f"Download completed: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Failed to download update: {e}")
            return None
    
    def verify_update_integrity(self, download_path: Path, update_info: Dict) -> bool:
        """
        Verify the integrity of downloaded update.
        
        Args:
            download_path: Path to downloaded file
            update_info: Update information
            
        Returns:
            True if verification successful
        """
        try:
            # For now, just verify the file exists and has reasonable size
            if not download_path.exists():
                logger.error("Downloaded file does not exist")
                return False
            
            file_size = download_path.stat().st_size
            expected_size = update_info.get("download_size", 0)
            
            if expected_size > 0 and abs(file_size - expected_size) > 1024:  # Allow 1KB difference
                logger.error(f"File size mismatch: expected {expected_size}, got {file_size}")
                return False
            
            # TODO: Add SHA256 checksum verification when available in release assets
            
            logger.info("Update integrity verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify update integrity: {e}")
            return False
    
    def create_backup(self) -> Optional[Path]:
        """
        Create backup of current installation.
        
        Returns:
            Path to backup or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"personal_ai_agent_backup_{self.current_version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            logger.info(f"Creating backup: {backup_path}")
            
            # Files to backup
            backup_items = [
                "PersonalAIAgent.exe",
                "PersonalAIAgent.app", 
                "PersonalAIAgent",
                ".env",
                "package_info.json",
            ]
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            for item in backup_items:
                source_path = self.app_dir / item
                if source_path.exists():
                    dest_path = backup_path / item
                    if source_path.is_dir():
                        shutil.copytree(source_path, dest_path)
                    else:
                        shutil.copy2(source_path, dest_path)
                    logger.info(f"Backed up: {item}")
            
            # Clean old backups
            self.cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def cleanup_old_backups(self):
        """Remove old backup directories."""
        try:
            backup_count = self.config.get("backup_count", 5)
            if backup_count <= 0:
                return
            
            # Get all backup directories
            backup_dirs = [
                d for d in self.backup_dir.iterdir() 
                if d.is_dir() and d.name.startswith("personal_ai_agent_backup_")
            ]
            
            # Sort by modification time (newest first)
            backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_dirs[backup_count:]:
                shutil.rmtree(old_backup)
                logger.info(f"Removed old backup: {old_backup.name}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def extract_update(self, download_path: Path) -> Optional[Path]:
        """
        Extract update package.
        
        Args:
            download_path: Path to downloaded archive
            
        Returns:
            Path to extracted directory or None if failed
        """
        try:
            extract_dir = self.temp_dir / "extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)
            
            logger.info(f"Extracting update: {download_path}")
            
            if download_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif download_path.suffix == '.gz':
                import tarfile
                with tarfile.open(download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                logger.error(f"Unsupported archive format: {download_path.suffix}")
                return None
            
            logger.info(f"Update extracted to: {extract_dir}")
            return extract_dir
            
        except Exception as e:
            logger.error(f"Failed to extract update: {e}")
            return None
    
    def install_update(self, extract_dir: Path, backup_path: Path) -> bool:
        """
        Install the extracted update.
        
        Args:
            extract_dir: Path to extracted update files
            backup_path: Path to backup (for rollback if needed)
            
        Returns:
            True if installation successful
        """
        try:
            logger.info("Installing update...")
            
            # Find the executable in extracted files
            platform_name, _ = self.get_platform_info()
            
            if platform_name == "windows":
                executable_name = "PersonalAIAgent.exe"
            elif platform_name == "macos":
                executable_name = "PersonalAIAgent.app"
            else:
                executable_name = "PersonalAIAgent"
            
            # Find the executable in extracted directory
            executable_path = None
            for root, dirs, files in os.walk(extract_dir):
                if executable_name in files:
                    executable_path = Path(root) / executable_name
                    break
                elif executable_name in dirs:
                    executable_path = Path(root) / executable_name
                    break
            
            if not executable_path or not executable_path.exists():
                logger.error(f"Could not find {executable_name} in extracted files")
                return False
            
            # Install new executable
            dest_path = self.app_dir / executable_name
            
            # Remove old executable
            if dest_path.exists():
                if dest_path.is_dir():
                    shutil.rmtree(dest_path)
                else:
                    dest_path.unlink()
            
            # Copy new executable
            if executable_path.is_dir():
                shutil.copytree(executable_path, dest_path)
            else:
                shutil.copy2(executable_path, dest_path)
                # Ensure executable permissions on Unix systems
                if platform_name in ["macos", "linux"]:
                    os.chmod(dest_path, 0o755)
            
            # Copy other updated files
            update_files = [
                "install.py",
                "download_models.py", 
                "model_download_config.py",
                "uninstall.py",
                "README.md",
                "package_info.json",
            ]
            
            for file_name in update_files:
                source_file = None
                for root, dirs, files in os.walk(extract_dir):
                    if file_name in files:
                        source_file = Path(root) / file_name
                        break
                
                if source_file and source_file.exists():
                    dest_file = self.app_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"Updated: {file_name}")
            
            logger.info("Update installation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            # TODO: Implement rollback from backup
            return False
    
    def should_check_for_updates(self) -> bool:
        """Check if it's time to check for updates."""
        if not self.config.get("auto_check", True):
            return False
        
        last_check = self.config.get("last_check")
        if not last_check:
            return True
        
        try:
            last_check_time = datetime.fromisoformat(last_check)
            time_since_check = datetime.now() - last_check_time
            return time_since_check.total_seconds() >= self.update_check_interval
        except Exception:
            return True
    
    def perform_update_check(self) -> Optional[Dict]:
        """Perform automatic update check if enabled and due."""
        if not self.should_check_for_updates():
            return None
        
        return self.check_for_updates()
    
    def perform_automatic_update(self, update_info: Dict) -> bool:
        """
        Perform automatic update if enabled.
        
        Args:
            update_info: Update information from check_for_updates()
            
        Returns:
            True if update was successful
        """
        if not self.auto_update:
            logger.info("Automatic updates disabled")
            return False
        
        try:
            # Download update
            download_path = self.download_update(update_info)
            if not download_path:
                return False
            
            # Verify integrity
            if not self.verify_update_integrity(download_path, update_info):
                return False
            
            # Create backup
            backup_path = self.create_backup()
            if not backup_path:
                logger.warning("Failed to create backup, proceeding anyway")
            
            # Extract update
            extract_dir = self.extract_update(download_path)
            if not extract_dir:
                return False
            
            # Install update
            if not self.install_update(extract_dir, backup_path):
                return False
            
            # Cleanup
            try:
                download_path.unlink()
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {e}")
            
            logger.info(f"Successfully updated to version {update_info['version']}")
            return True
            
        except Exception as e:
            logger.error(f"Automatic update failed: {e}")
            return False
    
    def skip_version(self, version_to_skip: str):
        """Add version to skip list."""
        skip_versions = self.config.get("skip_versions", [])
        if version_to_skip not in skip_versions:
            skip_versions.append(version_to_skip)
            self.config["skip_versions"] = skip_versions
            self.save_config()
            logger.info(f"Version {version_to_skip} added to skip list")
    
    def get_update_status(self) -> Dict:
        """Get current update status information."""
        return {
            "current_version": self.current_version,
            "auto_check": self.config.get("auto_check", True),
            "auto_update": self.auto_update,
            "last_check": self.config.get("last_check"),
            "update_channel": self.config.get("update_channel", "stable"),
            "skip_versions": self.config.get("skip_versions", []),
        }

def main():
    """Test the auto-updater functionality."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    updater = AutoUpdater(
        current_version="1.0.0",
        github_repo="your-username/personal-ai-agent",
        auto_update=False
    )
    
    print("🔄 Personal AI Agent Auto-Updater")
    print("=" * 40)
    
    # Check for updates
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"📦 Update available: {update_info['version']}")
        print(f"📏 Download size: {update_info['download_size'] / 1024 / 1024:.1f} MB")
        print(f"📅 Released: {update_info['published_at']}")
        print("\n📝 Release notes:")
        print(update_info['release_notes'][:500] + ("..." if len(update_info['release_notes']) > 500 else ""))
    else:
        print("✅ No updates available")
    
    # Show current status
    status = updater.get_update_status()
    print(f"\n📊 Current status:")
    print(f"  Version: {status['current_version']}")
    print(f"  Auto-check: {status['auto_check']}")
    print(f"  Last check: {status['last_check']}")

if __name__ == "__main__":
    main()