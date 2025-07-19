"""
Rate limiting middleware for API endpoints.

Provides configurable rate limiting to prevent abuse and ensure system stability.
Uses slowapi (FastAPI-compatible implementation of Flask-Limiter).
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings

logger = logging.getLogger("personal_ai_agent")


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    
    Uses IP address as primary identifier, with fallback to user agent.
    In future, could be enhanced to use authenticated user ID.
    """
    # Primary: Use IP address
    client_ip = get_remote_address(request)
    
    # For authenticated endpoints, we could use user ID
    # This would require extracting user from JWT token
    if hasattr(request.state, 'user_id'):
        return f"user_{request.state.user_id}"
    
    return client_ip


# Configure rate limiter with different limits for different endpoints
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["100/hour", "20/minute"]  # Conservative defaults
)


# Endpoint-specific rate limits
RATE_LIMITS = {
    # Authentication endpoints - more restrictive
    "/api/login": "10/minute",
    "/api/register": "5/minute",
    
    # Document upload - moderate limits
    "/api/documents/upload": "20/hour",
    "/api/documents": "100/hour",
    
    # Query endpoints - balanced limits
    "/api/queries": "50/hour",
    "/api/queries/ask": "50/hour",
    
    # Gmail endpoints - API-aware limits
    "/api/gmail/sync": "10/hour",  # Gmail API has its own limits
    "/api/gmail/auth": "5/minute",
    "/api/gmail/callback": "10/minute",
    
    # Email endpoints - moderate limits
    "/api/emails": "100/hour",
    "/api/emails/search": "100/hour",
    
    # Health checks and status - more permissive
    "/api/health-check": "1000/hour",
    "/api/backend-status": "1000/hour",
    "/api/": "1000/hour",
}


def apply_rate_limits(app):
    """Apply rate limiting to FastAPI app"""
    
    # Add the rate limiter to the app state
    app.state.limiter = limiter
    
    # Add the middleware
    app.add_middleware(SlowAPIMiddleware)
    
    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    logger.info("Rate limiting middleware configured")


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    
    Provides helpful error messages and includes retry information.
    """
    client_id = get_client_identifier(request)
    endpoint = request.url.path
    
    logger.warning(
        f"Rate limit exceeded for client {client_id} on endpoint {endpoint}. "
        f"Limit: {exc.detail}"
    )
    
    # Parse retry time from the exception
    retry_after = getattr(exc, 'retry_after', 60)  # Default 60 seconds
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests to {endpoint}",
            "retry_after": retry_after,
            "limit_info": exc.detail,
            "help": "Please wait before making more requests",
            "timestamp": datetime.now().isoformat()
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail),
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


def get_rate_limit_for_endpoint(endpoint: str) -> str:
    """Get rate limit configuration for specific endpoint"""
    return RATE_LIMITS.get(endpoint, "100/hour")


# Rate limiting decorators for different endpoint types
def auth_rate_limit(func):
    """Rate limiting decorator for authentication endpoints"""
    return limiter.limit("10/minute")(func)


def upload_rate_limit(func):
    """Rate limiting decorator for upload endpoints"""
    return limiter.limit("20/hour")(func)


def query_rate_limit(func):
    """Rate limiting decorator for query endpoints"""
    return limiter.limit("50/hour")(func)


def gmail_rate_limit(func):
    """Rate limiting decorator for Gmail endpoints"""
    return limiter.limit("10/hour")(func)


def general_rate_limit(func):
    """Rate limiting decorator for general endpoints"""
    return limiter.limit("100/hour")(func)