#!/usr/bin/env python3
"""
Gmail API Setup Script

This script helps configure Gmail API credentials for the Personal AI Agent.
You need to create a Google Cloud Project and enable the Gmail API first.

Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing project
3. Enable the Gmail API
4. Create OAuth2 credentials (Desktop application type)
5. Download the credentials JSON file
6. Run this script to configure the application

Usage:
    python setup_gmail.py [path_to_credentials.json]
"""

import os
import json
import sys
from pathlib import Path


def setup_gmail_credentials(credentials_file_path: str = None):
    """
    Setup Gmail API credentials for the application
    
    Args:
        credentials_file_path: Path to the downloaded credentials JSON file
    """
    
    print("🔧 Gmail API Setup for Personal AI Agent")
    print("=" * 50)
    
    # Get project root directory
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    if credentials_file_path:
        # Load credentials from file
        try:
            with open(credentials_file_path, 'r') as f:
                credentials = json.load(f)
            
            # Extract OAuth2 credentials
            if 'web' in credentials:
                oauth_config = credentials['web']
            elif 'installed' in credentials:
                oauth_config = credentials['installed']
            else:
                print("❌ Invalid credentials file format")
                return False
            
            client_id = oauth_config.get('client_id')
            client_secret = oauth_config.get('client_secret')
            
        except Exception as e:
            print(f"❌ Error reading credentials file: {e}")
            return False
    else:
        # Interactive input
        print("\n📝 Please enter your Gmail API credentials:")
        print("   (You can find these in your Google Cloud Console)")
        
        client_id = input("Gmail Client ID: ").strip()
        client_secret = input("Gmail Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required")
        return False
    
    # Read existing .env file
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add Gmail credentials
    env_lines = env_content.split('\n') if env_content else []
    
    # Remove existing Gmail credentials
    env_lines = [line for line in env_lines if not line.startswith(('GMAIL_CLIENT_ID=', 'GMAIL_CLIENT_SECRET=', 'GMAIL_REDIRECT_URI='))]
    
    # Add new credentials
    env_lines.extend([
        f"GMAIL_CLIENT_ID={client_id}",
        f"GMAIL_CLIENT_SECRET={client_secret}",
        "GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback"
    ])
    
    # Write back to .env file
    try:
        with open(env_file, 'w') as f:
            f.write('\n'.join(line for line in env_lines if line.strip()))
            f.write('\n')
        
        print("✅ Gmail API credentials saved to .env file")
        print(f"📄 Configuration saved to: {env_file}")
        
    except Exception as e:
        print(f"❌ Error writing to .env file: {e}")
        return False
    
    # Create Gmail directories
    try:
        email_dir = project_root / "static" / "emails"
        email_vector_dir = project_root / "data" / "email_vectors"
        
        email_dir.mkdir(parents=True, exist_ok=True)
        email_vector_dir.mkdir(parents=True, exist_ok=True)
        
        print("✅ Created Gmail storage directories")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create directories: {e}")
    
    print("\n🎉 Gmail API setup completed!")
    print("\n📋 Next steps:")
    print("1. Install additional dependencies: pip install -r requirements.txt")
    print("2. Start the application: python main.py")
    print("3. Navigate to Gmail settings in the web interface")
    print("4. Connect your Gmail account using OAuth2")
    
    return True


def print_help():
    """Print help information"""
    print(__doc__)
    print("\nQuick Setup:")
    print("1. Download OAuth2 credentials JSON from Google Cloud Console")
    print("2. Run: python setup_gmail.py path/to/credentials.json")
    print("3. Or run interactively: python setup_gmail.py")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print_help()
        else:
            credentials_file = sys.argv[1]
            if os.path.exists(credentials_file):
                setup_gmail_credentials(credentials_file)
            else:
                print(f"❌ Credentials file not found: {credentials_file}")
                print("Run with --help for usage instructions")
    else:
        # Interactive mode
        setup_gmail_credentials()