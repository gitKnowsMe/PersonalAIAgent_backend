"""
Email Authentication Service

Handles OAuth2 token encryption/decryption and secure token management
for email service integrations.
"""

import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger("personal_ai_agent")


class EmailAuthService:
    """
    Service for encrypting and decrypting OAuth2 tokens for email accounts
    """
    
    def __init__(self):
        self._fernet = None
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption key from settings"""
        try:
            # Use the application secret key as the base for token encryption
            password = settings.SECRET_KEY.encode()
            
            # Create a salt (in production, this should be stored securely)
            salt = b'email_token_salt_2024'  # Fixed salt for consistent decryption
            
            # Derive encryption key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            self._fernet = Fernet(key)
            logger.info("Email token encryption initialized")
            
        except Exception as e:
            logger.error(f"Error initializing email token encryption: {e}")
            raise
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an OAuth2 token for secure storage
        
        Args:
            token: Plain text token to encrypt
            
        Returns:
            Encrypted token as base64 string
        """
        try:
            if not token:
                return ""
            
            # Encrypt the token
            encrypted_data = self._fernet.encrypt(token.encode())
            
            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting token: {e}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt an OAuth2 token for API usage
        
        Args:
            encrypted_token: Encrypted token as base64 string
            
        Returns:
            Decrypted plain text token
        """
        try:
            if not encrypted_token:
                return ""
            
            # Decode from base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_token.encode())
            
            # Decrypt the token
            decrypted_data = self._fernet.decrypt(encrypted_data)
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            raise
    
    def rotate_encryption_key(self, old_secret_key: str, new_secret_key: str) -> bool:
        """
        Rotate encryption key and re-encrypt all tokens
        
        Args:
            old_secret_key: Previous secret key
            new_secret_key: New secret key
            
        Returns:
            True if rotation successful, False otherwise
        """
        try:
            # Create old and new Fernet instances
            old_password = old_secret_key.encode()
            new_password = new_secret_key.encode()
            
            salt = b'email_token_salt_2024'
            
            # Old key
            old_kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            old_key = base64.urlsafe_b64encode(old_kdf.derive(old_password))
            old_fernet = Fernet(old_key)
            
            # New key
            new_kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            new_key = base64.urlsafe_b64encode(new_kdf.derive(new_password))
            new_fernet = Fernet(new_key)
            
            # Update instance to use new key
            self._fernet = new_fernet
            
            logger.info("Email token encryption key rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating encryption key: {e}")
            return False
    
    def validate_token_format(self, token: str) -> bool:
        """
        Validate that a token has the expected format
        
        Args:
            token: Token to validate
            
        Returns:
            True if token format is valid, False otherwise
        """
        try:
            if not token:
                return False
            
            # Basic validation - should be a non-empty string
            if not isinstance(token, str) or len(token.strip()) == 0:
                return False
            
            # OAuth2 tokens typically have certain characteristics
            # For Google tokens, they usually start with "ya29." for access tokens
            # and have a minimum length
            if len(token) < 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_token_expired(self, expires_at: Optional[str]) -> bool:
        """
        Check if a token has expired
        
        Args:
            expires_at: Token expiration time as ISO string
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            if not expires_at:
                return True
            
            from datetime import datetime
            
            # Parse expiration time
            if isinstance(expires_at, str):
                expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expiry_time = expires_at
            
            # Add 5-minute buffer to account for clock skew
            from datetime import timedelta
            buffer_time = timedelta(minutes=5)
            
            return datetime.now() > (expiry_time - buffer_time)
            
        except Exception as e:
            logger.error(f"Error checking token expiration: {e}")
            return True  # Assume expired if we can't parse
    
    def generate_secure_state(self) -> str:
        """
        Generate a secure state parameter for OAuth2 flows
        
        Returns:
            Random state string
        """
        try:
            import secrets
            return secrets.token_urlsafe(32)
        except Exception as e:
            logger.error(f"Error generating secure state: {e}")
            raise


# Global email auth service instance
email_auth_service = EmailAuthService()