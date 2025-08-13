"""
Custom exception classes for email services.

Provides specific exception types for different email-related errors
to improve error handling, debugging, and user experience.
"""

class EmailServiceError(Exception):
    """Base exception for all email service errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "EMAIL_SERVICE_ERROR"
        self.details = details or {}
    
    def to_dict(self):
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class AuthenticationError(EmailServiceError):
    """Authentication-related errors (invalid tokens, expired credentials, etc.)."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message, 
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(EmailServiceError):
    """Authorization-related errors (insufficient permissions, scope issues, etc.)."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message, 
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class TokenRefreshError(AuthenticationError):
    """Token refresh-specific errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)
        self.error_code = "TOKEN_REFRESH_ERROR"


class GmailApiError(EmailServiceError):
    """Gmail API-specific errors."""
    
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        super().__init__(
            message, 
            error_code="GMAIL_API_ERROR",
            details=details or {}
        )
        self.status_code = status_code
        if status_code:
            self.details["status_code"] = status_code


class RateLimitError(GmailApiError):
    """Rate limiting errors from Gmail API."""
    
    def __init__(self, message: str = "Gmail API rate limit exceeded", retry_after: int = None, details: dict = None):
        super().__init__(message, status_code=429, details=details or {})
        self.error_code = "RATE_LIMIT_ERROR"
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class QuotaExceededError(GmailApiError):
    """Gmail API quota exceeded errors."""
    
    def __init__(self, message: str = "Gmail API quota exceeded", details: dict = None):
        super().__init__(message, status_code=403, details=details)
        self.error_code = "QUOTA_EXCEEDED_ERROR"


class EmailNotFoundError(EmailServiceError):
    """Email or email account not found errors."""
    
    def __init__(self, message: str, email_id: str = None, details: dict = None):
        super().__init__(
            message, 
            error_code="EMAIL_NOT_FOUND",
            details=details or {}
        )
        self.email_id = email_id
        if email_id:
            self.details["email_id"] = email_id


class EmailProcessingError(EmailServiceError):
    """Email content processing errors."""
    
    def __init__(self, message: str, email_id: str = None, details: dict = None):
        super().__init__(
            message, 
            error_code="EMAIL_PROCESSING_ERROR",
            details=details or {}
        )
        self.email_id = email_id
        if email_id:
            self.details["email_id"] = email_id


class VectorStoreError(EmailServiceError):
    """Vector store operation errors."""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(
            message, 
            error_code="VECTOR_STORE_ERROR",
            details=details or {}
        )
        self.operation = operation
        if operation:
            self.details["operation"] = operation


class DatabaseError(EmailServiceError):
    """Database operation errors."""
    
    def __init__(self, message: str, table: str = None, details: dict = None):
        super().__init__(
            message, 
            error_code="DATABASE_ERROR",
            details=details or {}
        )
        self.table = table
        if table:
            self.details["table"] = table


class NetworkError(EmailServiceError):
    """Network connectivity errors."""
    
    def __init__(self, message: str, timeout: bool = False, details: dict = None):
        super().__init__(
            message, 
            error_code="NETWORK_ERROR",
            details=details or {}
        )
        self.timeout = timeout
        if timeout:
            self.details["timeout"] = True


class EmailClassificationError(EmailProcessingError):
    """Email classification-specific errors."""
    
    def __init__(self, message: str, email_id: str = None, details: dict = None):
        super().__init__(message, email_id, details)
        self.error_code = "EMAIL_CLASSIFICATION_ERROR"


class EmailSyncError(EmailServiceError):
    """Email synchronization errors."""
    
    def __init__(self, message: str, account_email: str = None, details: dict = None):
        super().__init__(
            message, 
            error_code="EMAIL_SYNC_ERROR",
            details=details or {}
        )
        self.account_email = account_email
        if account_email:
            self.details["account_email"] = account_email


# Utility functions for exception handling

def handle_gmail_api_error(e: Exception) -> EmailServiceError:
    """Convert Gmail API errors to appropriate custom exceptions."""
    from googleapiclient.errors import HttpError
    
    if isinstance(e, HttpError):
        status_code = e.resp.status
        error_details = {
            "status_code": status_code,
            "reason": e.resp.reason,
            "original_error": str(e)
        }
        
        if status_code == 401:
            return AuthenticationError(
                "Gmail authentication failed. Token may be expired or invalid.",
                details=error_details
            )
        elif status_code == 403:
            error_content = str(e)
            if "quota" in error_content.lower() or "limit" in error_content.lower():
                return QuotaExceededError(
                    "Gmail API quota or rate limit exceeded.",
                    details=error_details
                )
            else:
                return AuthorizationError(
                    "Insufficient permissions for Gmail API access.",
                    details=error_details
                )
        elif status_code == 429:
            return RateLimitError(
                "Gmail API rate limit exceeded.",
                details=error_details
            )
        else:
            return GmailApiError(
                f"Gmail API error: {e.resp.reason}",
                status_code=status_code,
                details=error_details
            )
    
    # For non-HttpError exceptions
    return EmailServiceError(f"Unexpected Gmail API error: {str(e)}")


def handle_network_error(e: Exception) -> NetworkError:
    """Convert network-related errors to NetworkError."""
    import socket
    from requests.exceptions import RequestException, Timeout, ConnectionError
    
    error_details = {"original_error": str(e)}
    
    if isinstance(e, (Timeout, socket.timeout)):
        return NetworkError(
            "Network request timed out",
            timeout=True,
            details=error_details
        )
    elif isinstance(e, (ConnectionError, socket.error)):
        return NetworkError(
            "Network connection failed",
            details=error_details
        )
    elif isinstance(e, RequestException):
        return NetworkError(
            f"Network request failed: {str(e)}",
            details=error_details
        )
    
    return NetworkError(f"Network error: {str(e)}", details=error_details)


def handle_database_error(e: Exception, table: str = None) -> DatabaseError:
    """Convert database errors to DatabaseError."""
    from sqlalchemy.exc import SQLAlchemyError
    
    error_details = {"original_error": str(e)}
    
    if isinstance(e, SQLAlchemyError):
        return DatabaseError(
            f"Database operation failed: {str(e)}",
            table=table,
            details=error_details
        )
    
    return DatabaseError(f"Database error: {str(e)}", table=table, details=error_details)