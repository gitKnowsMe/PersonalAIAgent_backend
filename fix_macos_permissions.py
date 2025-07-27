#!/usr/bin/env python3
"""
macOS Permissions Fix for Personal AI Agent
Comprehensive solution for Finder permission dialogs and security issues
"""

import os
import subprocess
import sys
from pathlib import Path

def fix_quarantine_attributes():
    """Remove quarantine attributes that cause security prompts."""
    print("🔓 Removing quarantine attributes...")
    
    # Find all files in current directory
    current_dir = Path.cwd()
    
    for item in current_dir.rglob("*"):
        if item.is_file() or item.suffix == ".app":
            try:
                # Remove quarantine attribute
                subprocess.run(
                    ["xattr", "-d", "com.apple.quarantine", str(item)], 
                    capture_output=True, 
                    check=False  # Don't fail if attribute doesn't exist
                )
                print(f"   ✓ {item.name}")
            except Exception as e:
                pass  # Ignore if attribute doesn't exist
    
    print("✅ Quarantine attributes removed")

def fix_app_permissions():
    """Fix executable permissions on app bundle."""
    print("🔧 Fixing app bundle permissions...")
    
    app_paths = list(Path.cwd().glob("*.app"))
    
    for app_path in app_paths:
        # Fix executable permissions
        macos_dir = app_path / "Contents" / "MacOS"
        if macos_dir.exists():
            for executable in macos_dir.iterdir():
                executable.chmod(0o755)
                print(f"   ✓ Made executable: {executable.name}")
        
        # Fix app bundle permissions
        subprocess.run(["chmod", "-R", "755", str(app_path)], check=False)
        print(f"   ✓ Fixed bundle: {app_path.name}")
    
    print("✅ App permissions fixed")

def create_launch_script():
    """Create a launch script that bypasses permission issues."""
    print("📝 Creating launch script...")
    
    launch_script = """#!/bin/bash
# Personal AI Agent Launcher
# Bypasses macOS permission issues

set -e

echo "🚀 Personal AI Agent Launcher"
echo "=============================="

# Remove quarantine attributes
echo "🔓 Removing security restrictions..."
find . -name "*.app" -exec xattr -d com.apple.quarantine {} \\; 2>/dev/null || true
find . -type f -exec xattr -d com.apple.quarantine {} \\; 2>/dev/null || true

# Fix permissions
echo "🔧 Fixing permissions..."
find . -name "*.app" -exec chmod -R 755 {} \\;

# Find the app bundle
APP_BUNDLE=$(find . -name "*.app" -type d | head -1)

if [ -z "$APP_BUNDLE" ]; then
    echo "❌ No .app bundle found"
    exit 1
fi

echo "📱 Found app: $APP_BUNDLE"

# Launch the app
echo "🎯 Launching Personal AI Agent..."
open "$APP_BUNDLE"

echo "✅ Launch initiated!"
echo ""
echo "If this is the first run:"
echo "• Phi-2 model (~1.7GB) will download automatically"
echo "• Browser will open to http://localhost:8000"
echo "• All AI processing happens locally for privacy"
"""

    script_path = Path("launch.sh")
    with open(script_path, 'w') as f:
        f.write(launch_script)
    
    script_path.chmod(0o755)
    print(f"   ✓ Created: {script_path}")
    print("✅ Launch script ready")

def show_manual_instructions():
    """Show manual fix instructions for persistent issues."""
    print("\n" + "="*50)
    print("📋 MANUAL FIX INSTRUCTIONS")
    print("="*50)
    print()
    print("If permission dialogs persist, try these manual fixes:")
    print()
    print("🔧 Method 1: Terminal Commands")
    print("   sudo xattr -r -d com.apple.quarantine .")
    print("   sudo chmod -R 755 *.app")
    print("   ./launch.sh")
    print()
    print("🔧 Method 2: System Settings")
    print("   1. System Settings > Privacy & Security")
    print("   2. Scroll to 'Files and Folders'")
    print("   3. Enable permissions for relevant apps")
    print()
    print("🔧 Method 3: Developer Override")
    print("   sudo spctl --master-disable")
    print("   (Re-enable with: sudo spctl --master-enable)")
    print()
    print("🔧 Method 4: Right-Click Launch")
    print("   1. Right-click on 'Personal AI Agent.app'")
    print("   2. Select 'Open'")
    print("   3. Click 'Open' in security dialog")
    print()
    print("✅ One of these methods should resolve the issue!")

def main():
    """Run comprehensive macOS permission fix."""
    print("🍎 Personal AI Agent - macOS Permission Fix")
    print("=" * 45)
    print()
    
    try:
        fix_quarantine_attributes()
        print()
        fix_app_permissions()
        print()
        create_launch_script()
        print()
        
        print("🎉 PERMISSION FIX COMPLETE!")
        print()
        print("🚀 Try launching with: ./launch.sh")
        
        show_manual_instructions()
        
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        show_manual_instructions()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())