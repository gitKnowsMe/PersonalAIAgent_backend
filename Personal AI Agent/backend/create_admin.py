#!/usr/bin/env python3
"""
Script to create an admin user for the Personal AI Agent.
"""

import os
import sys
import getpass
import secrets
import string
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.db.database import SessionLocal, engine, Base
from app.db.models import User
from app.core.constants import USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH, PASSWORD_MIN_LENGTH, EMAIL_MAX_LENGTH

def validate_email(email):
    """Basic email validation"""
    return '@' in email and len(email) <= EMAIL_MAX_LENGTH and '.' in email.split('@')[1]

def validate_username(username):
    """Validate username according to constraints"""
    return USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH and username.isalnum()

def validate_password(password):
    """Validate password strength"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
    
    # Check for complexity
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numeric characters"
    
    return True, "Password is valid"

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def get_credentials_from_env():
    """Get credentials from environment variables"""
    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD') 
    email = os.getenv('ADMIN_EMAIL')
    
    if username and password and email:
        print("Using credentials from environment variables")
        return username, password, email
    
    return None, None, None

def get_credentials_interactive():
    """Get credentials interactively from user"""
    print("\n=== Creating Admin User ===")
    print("Enter admin user details (or press Ctrl+C to cancel)")
    
    # Get username
    while True:
        username = input(f"Username (length: {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH}, alphanumeric): ").strip()
        if not username:
            print("Username cannot be empty")
            continue
        if validate_username(username):
            break
        print(f"Invalid username. Must be {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH} alphanumeric characters")
    
    # Get email
    while True:
        email = input("Email address: ").strip()
        if not email:
            print("Email cannot be empty")
            continue
        if validate_email(email):
            break
        print("Invalid email format")
    
    # Get password
    print(f"\nPassword requirements:")
    print(f"- Minimum {PASSWORD_MIN_LENGTH} characters")
    print(f"- Must contain uppercase, lowercase, and numeric characters")
    print(f"- Special characters recommended: !@#$%^&*()")
    
    use_generated = input("\nGenerate secure password automatically? (y/n): ").lower().startswith('y')
    
    if use_generated:
        password = generate_secure_password()
        print(f"\n🔑 Generated secure password: {password}")
        print("⚠️  IMPORTANT: Save this password securely - it won't be shown again!")
        input("Press Enter to continue after saving the password...")
    else:
        while True:
            password = getpass.getpass("Enter password: ")
            if not password:
                print("Password cannot be empty")
                continue
                
            valid, message = validate_password(password)
            if valid:
                # Confirm password
                confirm = getpass.getpass("Confirm password: ")
                if password == confirm:
                    break
                else:
                    print("Passwords do not match")
            else:
                print(f"Invalid password: {message}")
    
    return username, password, email

def create_admin_user(username, password, email):
    """Create an admin user"""
    db = SessionLocal()
    try:
        # Validate inputs
        if not validate_username(username):
            print(f"❌ Invalid username: must be {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH} alphanumeric characters")
            return False
            
        if not validate_email(email):
            print("❌ Invalid email format")
            return False
            
        valid_password, msg = validate_password(password)
        if not valid_password:
            print(f"❌ Invalid password: {msg}")
            return False
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                print(f"❌ User with username '{username}' already exists")
            else:
                print(f"❌ User with email '{email}' already exists")
            return False
        
        # Create new user with admin privileges
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Admin: Yes")
        print(f"   Active: Yes")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function to create admin user"""
    print("🔐 Personal AI Agent - Admin User Creation")
    print("=========================================")
    
    try:
        # Ensure the database tables exist
        print("📋 Initializing database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
        
        # Try to get credentials from environment first
        username, password, email = get_credentials_from_env()
        
        # If not found in environment, get interactively
        if not all([username, password, email]):
            print("\n🔧 Environment variables not found (ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL)")
            print("Switching to interactive mode...")
            username, password, email = get_credentials_interactive()
        
        # Create the admin user
        print(f"\n🚀 Creating admin user...")
        success = create_admin_user(username, password, email)
        
        if success:
            print("\n🎉 Admin user creation completed successfully!")
            print("\n📝 You can now use these credentials to log in:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print("\n🔐 For security:")
            print("   - Change the password after first login")
            print("   - Use environment variables for production deployments")
            print("   - Consider enabling two-factor authentication")
        else:
            print("\n❌ Admin user creation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 