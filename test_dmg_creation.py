#!/usr/bin/env python3
"""
Test script for DMG creation functionality
"""

import sys
from pathlib import Path
from build_executable import ExecutableBuilder

def create_test_app_bundle():
    """Create a minimal test app bundle for DMG creation."""
    dist_dir = Path(__file__).parent / "dist"
    app_path = dist_dir / "Personal AI Agent.app"
    
    # Create minimal app bundle structure
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Create directories
    for directory in [contents_dir, macos_dir, resources_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create a dummy executable
    exe_path = macos_dir / "PersonalAIAgent"
    exe_path.write_text("#!/bin/bash\necho 'Test app'\n")
    exe_path.chmod(0o755)
    
    # Create basic Info.plist
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Personal AI Agent</string>
    <key>CFBundleExecutable</key>
    <string>PersonalAIAgent</string>
    <key>CFBundleIdentifier</key>
    <string>com.personalaiagent.backend</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
</dict>
</plist>"""
    
    plist_path = contents_dir / "Info.plist"
    plist_path.write_text(plist_content)
    
    print(f"Created test app bundle: {app_path}")
    return True

def test_dmg_creation():
    """Test the DMG creation functionality."""
    print("Testing DMG creation...")
    
    # Create test app bundle
    if not create_test_app_bundle():
        print("Failed to create test app bundle")
        return False
    
    # Create builder instance
    builder = ExecutableBuilder(target_platform='darwin', create_dmg=True)
    
    try:
        # Test DMG resource creation
        print("Creating DMG resources...")
        if not builder.create_dmg_resources():
            print("Failed to create DMG resources")
            return False
        
        # Test professional DMG creation
        print("Creating professional DMG...")
        if not builder.create_professional_dmg():
            print("Failed to create professional DMG")
            return False
        
        print("✅ DMG creation test completed successfully!")
        
        # Show results
        dist_dir = Path(__file__).parent / "dist"
        dmg_files = list(dist_dir.glob("*.dmg"))
        if dmg_files:
            print(f"Created DMG files: {dmg_files}")
        else:
            print("No DMG files found")
        
        return True
        
    except Exception as e:
        print(f"❌ DMG creation test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dmg_creation()
    sys.exit(0 if success else 1)