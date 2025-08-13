"""
Logging Middleware for FastAPI - Request/Response logging with performance tracking
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging_config import get_request_logger

logger = logging.getLogger("personal_ai_agent")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.excluded_paths = {'/api/health-check', '/docs', '/openapi.json', '/favicon.ico'}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Get user ID if available (from JWT or session)
        user_id = None
        try:
            # Try to extract user ID from request state (set by auth middleware)
            user_id = getattr(request.state, 'user_id', None)
        except:
            pass
        
        # Create request logger
        request_logger = get_request_logger(request_id, user_id)
        
        # Log request start
        if self.log_requests:
            await self._log_request_start(request, request_logger)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log successful response
            if self.log_responses:
                execution_time = (time.time() - start_time) * 1000
                await self._log_request_end(request, response, request_logger, execution_time)
            
            return response
            
        except Exception as e:
            # Log error response
            execution_time = (time.time() - start_time) * 1000
            await self._log_request_error(request, request_logger, execution_time, e)
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id}
            )
    
    async def _log_request_start(self, request: Request, request_logger):
        """Log request start details"""
        # Get request body for POST/PUT requests (be careful with large payloads)
        body_preview = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Only log first 200 chars of body to avoid huge logs
                if len(body) > 0:
                    body_str = body.decode('utf-8', errors='ignore')
                    body_preview = body_str[:200] + "..." if len(body_str) > 200 else body_str
            except:
                body_preview = "[Could not read body]"
        
        request_logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'endpoint': request.url.path,
                'query_params': str(request.query_params),
                'headers': dict(request.headers),
                'body_preview': body_preview,
                'client_ip': request.client.host if request.client else None
            }
        )
    
    async def _log_request_end(self, request: Request, response: Response, request_logger, execution_time: float):
        """Log successful request completion"""
        request_logger.info(
            f"Response: {response.status_code} - {execution_time:.2f}ms",
            extra={
                'status_code': response.status_code,
                'execution_time': execution_time,
                'endpoint': request.url.path,
                'method': request.method
            }
        )
        
        # Log slow requests as warnings
        if execution_time > 1000:  # > 1 second
            request_logger.warning(
                f"Slow request detected: {execution_time:.2f}ms",
                extra={
                    'slow_request': True,
                    'execution_time': execution_time,
                    'endpoint': request.url.path
                }
            )
    
    async def _log_request_error(self, request: Request, request_logger, execution_time: float, error: Exception):
        """Log request error"""
        request_logger.error(
            f"Request failed: {str(error)} - {execution_time:.2f}ms",
            extra={
                'error': str(error),
                'error_type': type(error).__name__,
                'execution_time': execution_time,
                'endpoint': request.url.path,
                'method': request.method
            },
            exc_info=True
        )


class QueryLoggingMixin:
    """Mixin for enhanced query logging in endpoints"""
    
    @staticmethod
    def log_query_processing(query: str, user_id: int, request_id: str = None):
        """Log query processing details"""
        query_logger = get_request_logger(request_id or "unknown", user_id)
        query_logger.info(
            f"Processing query: {query[:100]}{'...' if len(query) > 100 else ''}",
            extra={
                'query_length': len(query),
                'user_id': user_id,
                'operation': 'query_processing'
            }
        )
    
    @staticmethod
    def log_vector_search(chunks_found: int, search_time_ms: float, request_id: str = None):
        """Log vector search results"""
        search_logger = get_request_logger(request_id or "unknown")
        search_logger.info(
            f"Vector search completed: {chunks_found} chunks found",
            extra={
                'chunks_found': chunks_found,
                'search_time_ms': search_time_ms,
                'operation': 'vector_search'
            }
        )
    
    @staticmethod
    def log_llm_generation(response_length: int, generation_time_ms: float, from_cache: bool, request_id: str = None):
        """Log LLM response generation"""
        llm_logger = get_request_logger(request_id or "unknown")
        llm_logger.info(
            f"LLM generation: {response_length} chars, cached: {from_cache}",
            extra={
                'response_length': response_length,
                'generation_time_ms': generation_time_ms,
                'from_cache': from_cache,
                'operation': 'llm_generation'
            }
        )