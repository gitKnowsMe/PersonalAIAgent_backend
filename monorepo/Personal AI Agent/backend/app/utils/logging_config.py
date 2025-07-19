"""
Enhanced Logging Configuration with Rotation, Structured Logging, and Request Tracking
"""

import logging
import logging.handlers
import json
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'execution_time'):
            log_entry['execution_time_ms'] = record.execution_time
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

class PerformanceFilter(logging.Filter):
    """Filter for performance-related logs"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Mark slow operations (>1000ms) as WARNING
        if hasattr(record, 'execution_time') and record.execution_time > 1000:
            record.levelno = logging.WARNING
            record.levelname = 'WARNING'
            record.msg = f"[SLOW OPERATION] {record.msg}"
        return True

class RequestLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request context to log records"""
    
    def __init__(self, logger: logging.Logger, request_id: str, user_id: Optional[int] = None):
        super().__init__(logger, {})
        self.request_id = request_id
        self.user_id = user_id
        self.start_time = time.time()
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Add request context to extra fields
        extra = kwargs.get('extra', {})
        extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
        kwargs['extra'] = extra
        return msg, kwargs
    
    def log_request_start(self, method: str, endpoint: str):
        """Log request start"""
        self.info(f"Request started: {method} {endpoint}", extra={
            'method': method,
            'endpoint': endpoint
        })
    
    def log_request_end(self, status_code: int, endpoint: str):
        """Log request completion with timing"""
        execution_time = (time.time() - self.start_time) * 1000
        self.info(f"Request completed: {status_code}", extra={
            'status_code': status_code,
            'execution_time': execution_time,
            'endpoint': endpoint
        })

def setup_enhanced_logging(
    log_level: str = "INFO",
    log_file: str = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_json_format: bool = False
) -> logging.Logger:
    """
    Setup enhanced logging with rotation, structured format, and performance tracking
    """
    
    # Create logs directory
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger("personal_ai_agent")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    if use_json_format:
        formatter = StructuredFormatter()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
        )
        console_formatter = formatter
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(PerformanceFilter())
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console in production
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log configuration
    logger.info(f"Enhanced logging configured: level={log_level}, file={log_file}, json={use_json_format}")
    
    return logger

def get_request_logger(request_id: str, user_id: Optional[int] = None) -> RequestLoggerAdapter:
    """Get a logger adapter with request context"""
    logger = logging.getLogger("personal_ai_agent")
    return RequestLoggerAdapter(logger, request_id, user_id)

# Performance tracking utilities
def log_performance(operation_name: str):
    """Decorator for logging operation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger("personal_ai_agent")
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                logger.info(f"{operation_name} completed", extra={
                    'execution_time': execution_time,
                    'operation': operation_name
                })
                
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"{operation_name} failed: {str(e)}", extra={
                    'execution_time': execution_time,
                    'operation': operation_name,
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator