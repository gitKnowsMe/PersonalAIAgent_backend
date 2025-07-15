"""
Email service exceptions module.
"""

from .email_exceptions import (
    EmailServiceError,
    AuthenticationError,
    AuthorizationError,
    TokenRefreshError,
    GmailApiError,
    RateLimitError,
    QuotaExceededError,
    EmailNotFoundError,
    EmailProcessingError,
    VectorStoreError,
    DatabaseError,
    NetworkError,
    EmailClassificationError,
    EmailSyncError,
    handle_gmail_api_error,
    handle_network_error,
    handle_database_error
)

# Create aliases for the new exception names to maintain compatibility
GmailAuthenticationError = AuthenticationError
GmailTokenError = AuthenticationError
GmailTokenExpiredError = AuthenticationError
GmailTokenRefreshError = TokenRefreshError
GmailQuotaExceededError = QuotaExceededError
GmailRateLimitError = RateLimitError
GmailSyncError = EmailSyncError
GmailMessageError = EmailProcessingError
ConnectionTimeoutError = NetworkError
APIConnectionError = NetworkError

__all__ = [
    "EmailServiceError",
    "AuthenticationError", 
    "AuthorizationError",
    "TokenRefreshError",
    "GmailApiError",
    "RateLimitError",
    "QuotaExceededError",
    "EmailNotFoundError",
    "EmailProcessingError",
    "VectorStoreError",
    "DatabaseError",
    "NetworkError",
    "EmailClassificationError",
    "EmailSyncError",
    "handle_gmail_api_error",
    "handle_network_error",
    "handle_database_error",
    # New aliases
    "GmailAuthenticationError",
    "GmailTokenError",
    "GmailTokenExpiredError",
    "GmailTokenRefreshError",
    "GmailQuotaExceededError",
    "GmailRateLimitError",
    "GmailSyncError",
    "GmailMessageError",
    "ConnectionTimeoutError",
    "APIConnectionError"
]