#!/usr/bin/env python3
"""
Script to set up the PostgreSQL database for the Personal AI Agent.
"""

import os
import sys
import subprocess
import getpass

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_postgres_running():
    """Check if PostgreSQL is running"""
    # This command works on most systems
    result = run_command("pg_isready")
    if result and "accepting connections" in result:
        return True
    return False

def create_database(db_name, username):
    """Create a PostgreSQL database"""
    print(f"Creating database '{db_name}'...")
    
    # Check if database already exists
    check_cmd = f"psql -lqt | cut -d \\| -f 1 | grep -qw {db_name}"
    if os.system(check_cmd) == 0:
        print(f"Database '{db_name}' already exists.")
        return True
    
    # Create the database
    create_cmd = f"createdb -U {username} {db_name}"
    if os.system(create_cmd) == 0:
        print(f"Database '{db_name}' created successfully.")
        return True
    else:
        print(f"Failed to create database '{db_name}'.")
        return False

def update_env_file(db_name, username):
    """Update the .env file with database connection info"""
    env_file = ".env"
    env_example = ".env.example"
    
    # Create .env from .env.example if it doesn't exist
    if not os.path.exists(env_file) and os.path.exists(env_example):
        with open(env_example, 'r') as f_example:
            content = f_example.read()
        
        # Replace the database URL
        content = content.replace(
            "DATABASE_URL=postgresql://singularity@localhost:5432/personal_ai_agent",
            f"DATABASE_URL=postgresql://{username}@localhost:5432/{db_name}"
        )
        
        # Generate a random secret key
        import secrets
        secret_key = secrets.token_hex(32)
        content = content.replace(
            "SECRET_KEY=your-secret-key-change-in-production",
            f"SECRET_KEY={secret_key}"
        )
        
        with open(env_file, 'w') as f_env:
            f_env.write(content)
        
        print(f"Created .env file with database configuration.")
    elif not os.path.exists(env_file):
        print("Warning: .env.example not found. Please create .env file manually.")

def main():
    """Main function"""
    print("Setting up PostgreSQL database for Personal AI Agent")
    
    # Check if PostgreSQL is running
    if not check_postgres_running():
        print("Error: PostgreSQL is not running. Please start PostgreSQL and try again.")
        sys.exit(1)
    
    # Get database name and username
    db_name = input("Enter database name (default: personal_ai_agent): ") or "personal_ai_agent"
    username = input("Enter PostgreSQL username (default: current user): ") or getpass.getuser()
    
    # Create the database
    if not create_database(db_name, username):
        sys.exit(1)
    
    # Update .env file
    update_env_file(db_name, username)
    
    print("\nDatabase setup complete!")
    print("You can now run the application with: python main.py")

if __name__ == "__main__":
    main() 