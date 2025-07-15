"""
Custom exception classes for the Personal AI Agent application.

Provides specific exception types for better error handling and debugging
throughout the email processing and API integration systems.
"""

from typing import Optional, Dict, Any


class PersonalAIAgentError(Exception):
    """Base exception class for all Personal AI Agent errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# === EMAIL PROCESSING EXCEPTIONS ===

class EmailProcessingError(PersonalAIAgentError):
    """Raised when email processing operations fail."""
    pass


class EmailParsingError(EmailProcessingError):
    """Raised when email content parsing fails."""
    pass


class EmailStorageError(EmailProcessingError):
    """Raised when email storage operations fail."""
    pass


class EmailClassificationError(EmailProcessingError):
    """Raised when email classification fails."""
    pass


# === GMAIL API EXCEPTIONS ===

class GmailApiError(PersonalAIAgentError):
    """Base class for Gmail API related errors."""
    pass


class GmailAuthenticationError(GmailApiError):
    """Raised when Gmail authentication fails."""
    pass


class GmailTokenError(GmailAuthenticationError):
    """Raised when Gmail token operations fail."""
    pass


class GmailTokenExpiredError(GmailTokenError):
    """Raised when Gmail access token has expired."""
    pass


class GmailTokenRefreshError(GmailTokenError):
    """Raised when Gmail token refresh fails."""
    pass


class GmailQuotaExceededError(GmailApiError):
    """Raised when Gmail API quota is exceeded."""
    pass


class GmailRateLimitError(GmailApiError):
    """Raised when Gmail API rate limit is hit."""
    pass


class GmailSyncError(GmailApiError):
    """Raised when Gmail synchronization fails."""
    pass


class GmailMessageError(GmailApiError):
    """Raised when Gmail message operations fail."""
    pass


# === NETWORK AND CONNECTION EXCEPTIONS ===

class NetworkError(PersonalAIAgentError):
    """Raised when network operations fail."""
    pass


class ConnectionTimeoutError(NetworkError):
    """Raised when connection times out."""
    pass


class APIConnectionError(NetworkError):
    """Raised when API connections fail."""
    pass


# === VECTOR STORAGE EXCEPTIONS ===

class VectorStorageError(PersonalAIAgentError):
    """Raised when vector storage operations fail."""
    pass


class EmbeddingError(VectorStorageError):
    """Raised when embedding generation fails."""
    pass


class IndexError(VectorStorageError):
    """Raised when vector index operations fail."""
    pass


# === DATABASE EXCEPTIONS ===

class DatabaseError(PersonalAIAgentError):
    """Raised when database operations fail."""
    pass


class UserNotFoundError(DatabaseError):
    """Raised when user is not found in database."""
    pass


class EmailAccountNotFoundError(DatabaseError):
    """Raised when email account is not found."""
    pass


# === VALIDATION EXCEPTIONS ===

class ValidationError(PersonalAIAgentError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(PersonalAIAgentError):
    """Raised when configuration is invalid."""
    pass


# === ERROR HANDLING UTILITIES ===

def handle_gmail_api_error(error: Exception) -> GmailApiError:
    """
    Convert generic API errors to specific Gmail API errors.
    
    Args:
        error: The original exception
        
    Returns:
        Specific GmailApiError subclass
    """
    error_message = str(error).lower()
    
    # Token related errors
    if any(token_term in error_message for token_term in ['token', 'credential', 'unauthorized', '401']):
        if 'expired' in error_message:
            return GmailTokenExpiredError(f"Gmail token expired: {str(error)}")
        elif 'refresh' in error_message:
            return GmailTokenRefreshError(f"Gmail token refresh failed: {str(error)}")
        else:
            return GmailAuthenticationError(f"Gmail authentication failed: {str(error)}")
    
    # Quota and rate limiting
    if any(quota_term in error_message for quota_term in ['quota', 'limit', '429', 'too many']):
        if 'quota' in error_message:
            return GmailQuotaExceededError(f"Gmail API quota exceeded: {str(error)}")
        else:
            return GmailRateLimitError(f"Gmail API rate limit hit: {str(error)}")
    
    # Network related errors
    if any(network_term in error_message for network_term in ['network', 'connection', 'timeout', 'dns']):
        return APIConnectionError(f"Gmail API connection failed: {str(error)}")
    
    # Generic Gmail API error
    return GmailApiError(f"Gmail API error: {str(error)}")


def handle_email_processing_error(error: Exception, context: str = "") -> EmailProcessingError:
    """
    Convert generic errors to specific email processing errors.
    
    Args:
        error: The original exception
        context: Additional context about the operation
        
    Returns:
        Specific EmailProcessingError subclass
    """
    error_message = str(error).lower()
    full_context = f"{context}: " if context else ""
    
    # Parsing related errors
    if any(parse_term in error_message for parse_term in ['parse', 'decode', 'format', 'invalid']):
        return EmailParsingError(f"{full_context}Email parsing failed: {str(error)}")
    
    # Storage related errors
    if any(storage_term in error_message for storage_term in ['storage', 'save', 'write', 'file', 'disk']):
        return EmailStorageError(f"{full_context}Email storage failed: {str(error)}")
    
    # Classification related errors
    if any(class_term in error_message for class_term in ['classification', 'category', 'classify']):
        return EmailClassificationError(f"{full_context}Email classification failed: {str(error)}")
    
    # Generic email processing error
    return EmailProcessingError(f"{full_context}Email processing failed: {str(error)}")


def handle_network_error(error: Exception) -> NetworkError:
    """
    Convert generic network errors to specific network errors.
    
    Args:
        error: The original exception
        
    Returns:
        Specific NetworkError subclass
    """
    error_message = str(error).lower()
    
    if any(timeout_term in error_message for timeout_term in ['timeout', 'timed out']):
        return ConnectionTimeoutError(f"Connection timed out: {str(error)}")
    
    return NetworkError(f"Network error: {str(error)}")