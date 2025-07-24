"""
Update management endpoints for Personal AI Agent backend.

Provides API endpoints for checking, downloading, and installing updates.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
from pathlib import Path
import sys
import os

# Add parent directory to path to import auto_updater
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from auto_updater import AutoUpdater

from app.core.config import settings
from app.core.security import get_current_user
from app.db.models import User

router = APIRouter(prefix="/updates", tags=["updates"])
logger = logging.getLogger("personal_ai_agent.api.updates")

# Global updater instance
updater = None

def get_updater() -> AutoUpdater:
    """Get or create the auto-updater instance."""
    global updater
    if updater is None:
        # Try to get version from package info
        current_version = "1.0.0"
        try:
            package_info_path = Path.cwd() / "package_info.json"
            if package_info_path.exists():
                import json
                with open(package_info_path, 'r') as f:
                    package_info = json.load(f)
                    current_version = package_info.get("version", "1.0.0")
        except Exception as e:
            logger.warning(f"Could not read package info: {e}")
        
        # Get GitHub repo from environment or use default
        github_repo = os.getenv("GITHUB_REPO", "your-username/personal-ai-agent")
        
        updater = AutoUpdater(
            current_version=current_version,
            github_repo=github_repo,
            auto_update=False  # Manual updates only via API
        )
    
    return updater

class UpdateCheckResponse(BaseModel):
    """Response for update check."""
    update_available: bool
    current_version: str
    latest_version: Optional[str] = None
    release_notes: Optional[str] = None
    download_size: Optional[int] = None
    published_at: Optional[str] = None
    is_prerelease: bool = False

class UpdateStatusResponse(BaseModel):
    """Response for update status."""
    current_version: str
    auto_check: bool
    auto_update: bool
    last_check: Optional[str] = None
    update_channel: str
    skip_versions: list

class UpdateDownloadResponse(BaseModel):
    """Response for update download."""
    success: bool
    message: str
    download_path: Optional[str] = None

class UpdateInstallResponse(BaseModel):
    """Response for update installation."""
    success: bool
    message: str
    requires_restart: bool = True

@router.get("/status", response_model=UpdateStatusResponse)
async def get_update_status(current_user: User = Depends(get_current_user)):
    """
    Get current update status and configuration.
    
    Requires authentication.
    """
    try:
        updater = get_updater()
        status = updater.get_update_status()
        
        return UpdateStatusResponse(
            current_version=status["current_version"],
            auto_check=status["auto_check"],
            auto_update=status["auto_update"],
            last_check=status["last_check"],
            update_channel=status["update_channel"],
            skip_versions=status["skip_versions"]
        )
    except Exception as e:
        logger.error(f"Failed to get update status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get update status")

@router.post("/check", response_model=UpdateCheckResponse)
async def check_for_updates(current_user: User = Depends(get_current_user)):
    """
    Check for available updates.
    
    Requires authentication.
    """
    try:
        updater = get_updater()
        
        # Run update check in background thread to avoid blocking
        loop = asyncio.get_event_loop()
        update_info = await loop.run_in_executor(None, updater.check_for_updates)
        
        if update_info:
            return UpdateCheckResponse(
                update_available=True,
                current_version=updater.current_version,
                latest_version=update_info["version"],
                release_notes=update_info["release_notes"],
                download_size=update_info["download_size"],
                published_at=update_info["published_at"],
                is_prerelease=update_info["is_prerelease"]
            )
        else:
            return UpdateCheckResponse(
                update_available=False,
                current_version=updater.current_version
            )
            
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        raise HTTPException(status_code=500, detail="Failed to check for updates")

@router.post("/download", response_model=UpdateDownloadResponse)
async def download_update(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Download available update.
    
    Requires authentication. Download happens in background.
    """
    try:
        updater = get_updater()
        
        # First check if update is available
        update_info = await asyncio.get_event_loop().run_in_executor(
            None, updater.check_for_updates
        )
        
        if not update_info:
            return UpdateDownloadResponse(
                success=False,
                message="No updates available"
            )
        
        # Start download in background
        def download_task():
            try:
                download_path = updater.download_update(update_info)
                if download_path:
                    logger.info(f"Update downloaded successfully: {download_path}")
                    # Verify integrity
                    if updater.verify_update_integrity(download_path, update_info):
                        logger.info("Update integrity verified")
                    else:
                        logger.error("Update integrity verification failed")
                else:
                    logger.error("Update download failed")
            except Exception as e:
                logger.error(f"Background download failed: {e}")
        
        background_tasks.add_task(download_task)
        
        return UpdateDownloadResponse(
            success=True,
            message=f"Downloading update {update_info['version']} in background",
            download_path=None  # Don't expose internal paths
        )
        
    except Exception as e:
        logger.error(f"Failed to start update download: {e}")
        raise HTTPException(status_code=500, detail="Failed to start update download")

@router.post("/install", response_model=UpdateInstallResponse)
async def install_update(current_user: User = Depends(get_current_user)):
    """
    Install downloaded update.
    
    Requires authentication. This will restart the application.
    """
    try:
        updater = get_updater()
        
        # Check if update is available
        update_info = await asyncio.get_event_loop().run_in_executor(
            None, updater.check_for_updates
        )
        
        if not update_info:
            return UpdateInstallResponse(
                success=False,
                message="No updates available",
                requires_restart=False
            )
        
        # Check if update is already downloaded
        platform_name, archive_format = updater.get_platform_info()
        asset_name = f"PersonalAIAgent-{platform_name}-no-models.{archive_format}"
        download_path = updater.temp_dir / asset_name
        
        if not download_path.exists():
            return UpdateInstallResponse(
                success=False,
                message="Update not downloaded. Please download first.",
                requires_restart=False
            )
        
        # Install update in background (app will restart)
        def install_task():
            try:
                # Create backup
                backup_path = updater.create_backup()
                if not backup_path:
                    logger.error("Failed to create backup")
                    return
                
                # Extract update
                extract_dir = updater.extract_update(download_path)
                if not extract_dir:
                    logger.error("Failed to extract update")
                    return
                
                # Install update
                if updater.install_update(extract_dir, backup_path):
                    logger.info("Update installed successfully")
                    
                    # Schedule application restart
                    import threading
                    import time
                    
                    def restart_app():
                        time.sleep(3)  # Give time for response to be sent
                        logger.info("Restarting application after update...")
                        os._exit(0)  # Force exit - supervisor should restart
                    
                    restart_thread = threading.Thread(target=restart_app)
                    restart_thread.daemon = True
                    restart_thread.start()
                else:
                    logger.error("Update installation failed")
                    
            except Exception as e:
                logger.error(f"Update installation failed: {e}")
        
        # Start installation in background
        import threading
        install_thread = threading.Thread(target=install_task)
        install_thread.daemon = True
        install_thread.start()
        
        return UpdateInstallResponse(
            success=True,
            message=f"Installing update {update_info['version']}. Application will restart.",
            requires_restart=True
        )
        
    except Exception as e:
        logger.error(f"Failed to install update: {e}")
        raise HTTPException(status_code=500, detail="Failed to install update")

@router.post("/skip-version")
async def skip_version(
    version: str,
    current_user: User = Depends(get_current_user)
):
    """
    Skip a specific version.
    
    Requires authentication.
    """
    try:
        updater = get_updater()
        updater.skip_version(version)
        
        return {"success": True, "message": f"Version {version} will be skipped"}
        
    except Exception as e:
        logger.error(f"Failed to skip version: {e}")
        raise HTTPException(status_code=500, detail="Failed to skip version")

@router.post("/configure")
async def configure_updates(
    auto_check: Optional[bool] = None,
    update_channel: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Configure update settings.
    
    Requires authentication.
    """
    try:
        updater = get_updater()
        
        if auto_check is not None:
            updater.config["auto_check"] = auto_check
        
        if update_channel is not None:
            if update_channel not in ["stable", "beta", "dev"]:
                raise HTTPException(status_code=400, detail="Invalid update channel")
            updater.config["update_channel"] = update_channel
        
        updater.save_config()
        
        return {"success": True, "message": "Update configuration saved"}
        
    except Exception as e:
        logger.error(f"Failed to configure updates: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure updates")

@router.get("/changelog")
async def get_changelog(version: Optional[str] = None):
    """
    Get changelog for specific version or latest.
    
    Does not require authentication (public endpoint).
    """
    try:
        updater = get_updater()
        
        if version:
            # Get specific version changelog
            url = f"https://api.github.com/repos/{updater.github_repo}/releases/tags/v{version}"
        else:
            # Get latest release changelog
            url = f"https://api.github.com/repos/{updater.github_repo}/releases/latest"
        
        import requests
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Version not found")
        
        response.raise_for_status()
        release_data = response.json()
        
        return {
            "version": release_data["tag_name"].lstrip('v'),
            "name": release_data["name"],
            "body": release_data["body"],
            "published_at": release_data["published_at"],
            "is_prerelease": release_data["prerelease"]
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch changelog: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch changelog")
    except Exception as e:
        logger.error(f"Failed to get changelog: {e}")
        raise HTTPException(status_code=500, detail="Failed to get changelog")