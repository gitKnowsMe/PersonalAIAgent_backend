#!/usr/bin/env python3
"""
Complete macOS DMG Build Script for Personal AI Agent

This script demonstrates the full Enhanced DMG with Progressive Setup workflow:
- Creates proper macOS .app bundle
- Generates DMG background and resources
- Creates professional DMG installer
- Implements first-run experience

Usage:
    python build_macos_dmg.py [--include-models] [--debug]
"""

import sys
import logging
from pathlib import Path
from build_executable import ExecutableBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main build process for macOS DMG."""
    logger.info("🚀 Personal AI Agent - Enhanced DMG Build System")
    logger.info("=" * 60)
    
    # Parse simple arguments
    include_models = '--include-models' in sys.argv
    debug = '--debug' in sys.argv
    
    if include_models:
        logger.info("⚠️  Building with models included (will be very large ~4GB)")
    else:
        logger.info("📦 Building with progressive model download (recommended)")
    
    if debug:
        logger.info("🐛 Debug mode enabled")
    
    # Create builder with DMG creation enabled
    builder = ExecutableBuilder(
        include_models=include_models,
        target_platform='darwin',
        debug=debug,
        create_dmg=True
    )
    
    try:
        logger.info("📋 Build Configuration:")
        logger.info(f"   • Platform: macOS")
        logger.info(f"   • Include Models: {include_models}")
        logger.info(f"   • Debug Mode: {debug}")
        logger.info(f"   • DMG Creation: Enabled")
        logger.info(f"   • First-run Experience: Enhanced")
        logger.info("")
        
        # Start the build process
        success = builder.build()
        
        if success:
            logger.info("🎉 Build completed successfully!")
            logger.info("")
            logger.info("📁 Build Artifacts:")
            
            dist_dir = Path(__file__).parent / "dist"
            
            # Check for app bundle
            app_bundle = dist_dir / "Personal AI Agent.app"
            if app_bundle.exists():
                logger.info(f"   ✅ macOS App Bundle: {app_bundle}")
            
            # Check for DMG
            dmg_files = list(dist_dir.glob("*.dmg"))
            if dmg_files:
                for dmg_file in dmg_files:
                    size_mb = dmg_file.stat().st_size / (1024 * 1024)
                    logger.info(f"   ✅ DMG Installer: {dmg_file} ({size_mb:.1f} MB)")
            
            # Check for other files
            readme_file = dist_dir / "README.md"
            if readme_file.exists():
                logger.info(f"   ✅ Documentation: {readme_file}")
            
            installer_file = dist_dir / "install.py"
            if installer_file.exists():
                logger.info(f"   ✅ Setup Script: {installer_file}")
            
            logger.info("")
            logger.info("🎯 Next Steps:")
            logger.info("   1. Test the DMG installer by double-clicking it")
            logger.info("   2. Drag the app to Applications folder")
            logger.info("   3. Launch the app - it will handle first-run setup")
            logger.info("   4. Browser will open to http://localhost:8000")
            logger.info("")
            logger.info("📋 Features Implemented:")
            logger.info("   • Enhanced macOS .app bundle with proper Info.plist")
            logger.info("   • Professional DMG with drag-and-drop interface")
            logger.info("   • First-run experience with guided setup")
            logger.info("   • Progressive Phi-2 model download (~1.7GB)")
            logger.info("   • Automatic browser opening after setup")
            logger.info("   • Native macOS integration and permissions")
            logger.info("")
            
        else:
            logger.error("❌ Build failed!")
            return 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Build cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Build failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())