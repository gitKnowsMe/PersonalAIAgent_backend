"""
Audit logging utilities for Personal AI Agent.

Provides comprehensive audit logging for security-sensitive operations,
admin actions, and user activities.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path

from app.core.config import settings

# Create dedicated audit logger
audit_logger = logging.getLogger("personal_ai_agent.audit")


class AuditEventType(str, Enum):
    """Types of events to audit"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    REGISTRATION = "registration"
    PASSWORD_CHANGE = "password_change"
    
    # Admin actions
    ADMIN_USER_CREATE = "admin_user_create"
    ADMIN_USER_DELETE = "admin_user_delete"
    ADMIN_USER_MODIFY = "admin_user_modify"
    ADMIN_SYSTEM_CONFIG = "admin_system_config"
    
    # Document operations
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_ACCESS = "document_access"
    
    # Email operations
    GMAIL_AUTH = "gmail_auth"
    GMAIL_SYNC = "gmail_sync"
    EMAIL_ACCESS = "email_access"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    DATABASE_ERROR = "database_error"


class AuditLogger:
    """
    Centralized audit logging system.
    
    Logs security-sensitive events with structured data for compliance and monitoring.
    """
    
    def __init__(self):
        self.setup_audit_logging()
    
    def setup_audit_logging(self):
        """Setup audit logging configuration"""
        # Create audit log directory
        audit_log_dir = Path("logs/audit")
        audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure audit logger with separate handler
        audit_handler = logging.FileHandler(audit_log_dir / "audit.log")
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        
        # Prevent propagation to avoid duplicate logs
        audit_logger.propagate = False
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log an audit event with structured data.
        
        Args:
            event_type: Type of event being logged
            user_id: ID of the user performing the action
            username: Username of the user
            ip_address: IP address of the request
            user_agent: User agent string
            details: Additional event-specific details
            success: Whether the action was successful
            error_message: Error message if action failed
        """
        audit_data = {
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "details": details or {},
            "error_message": error_message
        }
        
        # Log as structured JSON
        audit_logger.info(json.dumps(audit_data))
        
        # Also log to main logger for immediate visibility
        main_logger = logging.getLogger("personal_ai_agent")
        if success:
            main_logger.info(f"AUDIT: {event_type.value} by {username or 'unknown'} from {ip_address or 'unknown'}")
        else:
            main_logger.warning(f"AUDIT: {event_type.value} FAILED by {username or 'unknown'} from {ip_address or 'unknown'}: {error_message}")
    
    def log_login_attempt(self, username: str, ip_address: str, success: bool, error_message: str = None):
        """Log a login attempt"""
        self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            username=username,
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
    
    def log_admin_action(self, admin_user_id: str, admin_username: str, action: str, target_user: str = None, details: Dict[str, Any] = None, ip_address: str = None):
        """Log an admin action"""
        event_details = {"action": action}
        if target_user:
            event_details["target_user"] = target_user
        if details:
            event_details.update(details)
        
        self.log_event(
            event_type=AuditEventType.ADMIN_USER_MODIFY,
            user_id=admin_user_id,
            username=admin_username,
            ip_address=ip_address,
            details=event_details
        )
    
    def log_document_operation(self, user_id: str, username: str, operation: str, document_name: str, ip_address: str = None):
        """Log a document operation"""
        event_type = AuditEventType.DOCUMENT_UPLOAD if operation == "upload" else AuditEventType.DOCUMENT_ACCESS
        
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"operation": operation, "document": document_name}
        )
    
    def log_gmail_operation(self, user_id: str, username: str, operation: str, email_count: int = None, ip_address: str = None):
        """Log a Gmail operation"""
        event_type = AuditEventType.GMAIL_AUTH if operation == "auth" else AuditEventType.GMAIL_SYNC
        
        details = {"operation": operation}
        if email_count is not None:
            details["email_count"] = email_count
        
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details
        )
    
    def log_security_event(self, event_type: AuditEventType, ip_address: str, details: Dict[str, Any] = None, user_id: str = None):
        """Log a security event"""
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=False
        )
    
    def log_system_event(self, event_type: AuditEventType, details: Dict[str, Any] = None):
        """Log a system event"""
        self.log_event(
            event_type=event_type,
            details=details
        )


# Global audit logger instance
audit = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    return audit


# Convenience functions for common audit operations
def audit_login(username: str, ip_address: str, success: bool, error_message: str = None):
    """Audit a login attempt"""
    audit.log_login_attempt(username, ip_address, success, error_message)


def audit_admin_action(admin_user_id: str, admin_username: str, action: str, target_user: str = None, details: Dict[str, Any] = None, ip_address: str = None):
    """Audit an admin action"""
    audit.log_admin_action(admin_user_id, admin_username, action, target_user, details, ip_address)


def audit_document_upload(user_id: str, username: str, document_name: str, ip_address: str = None):
    """Audit a document upload"""
    audit.log_document_operation(user_id, username, "upload", document_name, ip_address)


def audit_gmail_sync(user_id: str, username: str, email_count: int, ip_address: str = None):
    """Audit a Gmail sync operation"""
    audit.log_gmail_operation(user_id, username, "sync", email_count, ip_address)


def audit_security_violation(event_type: AuditEventType, ip_address: str, details: Dict[str, Any] = None):
    """Audit a security violation"""
    audit.log_security_event(event_type, ip_address, details)