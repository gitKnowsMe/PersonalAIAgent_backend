"""
Error monitoring and structured logging utilities for email services.

Provides centralized error tracking, alerting, and structured logging
to improve debugging and system monitoring capabilities.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict

from app.exceptions import EmailServiceError


class ErrorSeverity(Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization and filtering."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    API_LIMIT = "api_limit"
    DATA_PROCESSING = "data_processing"
    STORAGE = "storage"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Structured error event for logging and monitoring."""
    timestamp: str
    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    service: str
    user_id: Optional[int] = None
    email_account: Optional[str] = None
    operation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error event to dictionary for JSON logging."""
        data = asdict(self)
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        return data
    
    def to_json(self) -> str:
        """Convert error event to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class EmailErrorMonitor:
    """Centralized error monitoring for email services."""
    
    def __init__(self):
        self.logger = logging.getLogger("email_error_monitor")
        self.error_counts = {}
        self.severity_mapping = {
            "AUTHENTICATION_ERROR": ErrorSeverity.HIGH,
            "AUTHORIZATION_ERROR": ErrorSeverity.HIGH,
            "TOKEN_REFRESH_ERROR": ErrorSeverity.MEDIUM,
            "GMAIL_API_ERROR": ErrorSeverity.MEDIUM,
            "RATE_LIMIT_ERROR": ErrorSeverity.LOW,
            "QUOTA_EXCEEDED_ERROR": ErrorSeverity.MEDIUM,
            "EMAIL_NOT_FOUND": ErrorSeverity.LOW,
            "EMAIL_PROCESSING_ERROR": ErrorSeverity.MEDIUM,
            "VECTOR_STORE_ERROR": ErrorSeverity.MEDIUM,
            "DATABASE_ERROR": ErrorSeverity.HIGH,
            "NETWORK_ERROR": ErrorSeverity.MEDIUM,
            "EMAIL_CLASSIFICATION_ERROR": ErrorSeverity.LOW,
            "EMAIL_SYNC_ERROR": ErrorSeverity.MEDIUM,
        }
        
        self.category_mapping = {
            "AUTHENTICATION_ERROR": ErrorCategory.AUTHENTICATION,
            "AUTHORIZATION_ERROR": ErrorCategory.AUTHORIZATION,
            "TOKEN_REFRESH_ERROR": ErrorCategory.AUTHENTICATION,
            "GMAIL_API_ERROR": ErrorCategory.API_LIMIT,
            "RATE_LIMIT_ERROR": ErrorCategory.API_LIMIT,
            "QUOTA_EXCEEDED_ERROR": ErrorCategory.API_LIMIT,
            "EMAIL_NOT_FOUND": ErrorCategory.DATA_PROCESSING,
            "EMAIL_PROCESSING_ERROR": ErrorCategory.DATA_PROCESSING,
            "VECTOR_STORE_ERROR": ErrorCategory.STORAGE,
            "DATABASE_ERROR": ErrorCategory.STORAGE,
            "NETWORK_ERROR": ErrorCategory.NETWORK,
            "EMAIL_CLASSIFICATION_ERROR": ErrorCategory.DATA_PROCESSING,
            "EMAIL_SYNC_ERROR": ErrorCategory.DATA_PROCESSING,
        }
    
    def log_error(
        self,
        error: Exception,
        service: str,
        operation: str = None,
        user_id: int = None,
        email_account: str = None,
        additional_details: Dict[str, Any] = None
    ):
        """
        Log a structured error event.
        
        Args:
            error: The exception that occurred
            service: Name of the service where error occurred
            operation: Specific operation being performed
            user_id: User ID if applicable
            email_account: Email account if applicable
            additional_details: Additional context details
        """
        # Determine error properties
        if isinstance(error, EmailServiceError):
            error_code = error.error_code
            message = error.message
            details = error.details.copy() if error.details else {}
        else:
            error_code = "UNKNOWN_ERROR"
            message = str(error)
            details = {}
        
        # Add additional details
        if additional_details:
            details.update(additional_details)
        
        # Determine severity and category
        severity = self.severity_mapping.get(error_code, ErrorSeverity.MEDIUM)
        category = self.category_mapping.get(error_code, ErrorCategory.UNKNOWN)
        
        # Create error event
        error_event = ErrorEvent(
            timestamp=datetime.utcnow().isoformat(),
            error_code=error_code,
            message=message,
            category=category,
            severity=severity,
            service=service,
            user_id=user_id,
            email_account=email_account,
            operation=operation,
            details=details,
            stack_trace=self._get_stack_trace(error) if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        )
        
        # Log the structured error
        self._log_structured_error(error_event)
        
        # Update error counts for monitoring
        self._update_error_counts(error_code, category, severity)
        
        # Check if alerting is needed
        self._check_alert_conditions(error_event)
    
    def _log_structured_error(self, error_event: ErrorEvent):
        """Log the error event with appropriate log level."""
        log_data = error_event.to_dict()
        
        if error_event.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error_event.message}", extra={"error_data": log_data})
        elif error_event.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY: {error_event.message}", extra={"error_data": log_data})
        elif error_event.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY: {error_event.message}", extra={"error_data": log_data})
        else:
            self.logger.info(f"LOW SEVERITY: {error_event.message}", extra={"error_data": log_data})
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get stack trace for high severity errors."""
        import traceback
        return traceback.format_exc()
    
    def _update_error_counts(self, error_code: str, category: ErrorCategory, severity: ErrorSeverity):
        """Update error counts for monitoring dashboards."""
        current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        
        # Initialize counters if needed
        if current_hour not in self.error_counts:
            self.error_counts[current_hour] = {
                "total": 0,
                "by_code": {},
                "by_category": {},
                "by_severity": {}
            }
        
        hour_counts = self.error_counts[current_hour]
        
        # Update counts
        hour_counts["total"] += 1
        hour_counts["by_code"][error_code] = hour_counts["by_code"].get(error_code, 0) + 1
        hour_counts["by_category"][category.value] = hour_counts["by_category"].get(category.value, 0) + 1
        hour_counts["by_severity"][severity.value] = hour_counts["by_severity"].get(severity.value, 0) + 1
        
        # Clean up old counts (keep last 24 hours)
        self._cleanup_old_counts()
    
    def _cleanup_old_counts(self):
        """Remove error counts older than 24 hours."""
        current_hour = datetime.utcnow()
        hours_to_keep = []
        
        for i in range(24):
            hour_key = (current_hour - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            hours_to_keep.append(hour_key)
        
        # Remove old entries
        self.error_counts = {k: v for k, v in self.error_counts.items() if k in hours_to_keep}
    
    def _check_alert_conditions(self, error_event: ErrorEvent):
        """Check if error conditions warrant alerting."""
        current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        
        if current_hour not in self.error_counts:
            return
        
        hour_counts = self.error_counts[current_hour]
        
        # Alert conditions
        alert_conditions = [
            # High number of total errors
            hour_counts["total"] > 50,
            
            # High number of critical/high severity errors
            hour_counts["by_severity"].get("critical", 0) > 5,
            hour_counts["by_severity"].get("high", 0) > 10,
            
            # High number of authentication/authorization errors
            hour_counts["by_category"].get("authentication", 0) > 10,
            hour_counts["by_category"].get("authorization", 0) > 10,
            
            # High number of network errors (potential outage)
            hour_counts["by_category"].get("network", 0) > 20,
        ]
        
        if any(alert_conditions):
            self._send_alert(error_event, hour_counts)
    
    def _send_alert(self, error_event: ErrorEvent, hour_counts: Dict[str, Any]):
        """Send alert for critical error conditions."""
        alert_message = f"""
        EMAIL SERVICE ALERT
        
        Time: {error_event.timestamp}
        Trigger: {error_event.message}
        Service: {error_event.service}
        
        Hourly Error Counts:
        - Total: {hour_counts['total']}
        - Critical: {hour_counts['by_severity'].get('critical', 0)}
        - High: {hour_counts['by_severity'].get('high', 0)}
        - Authentication: {hour_counts['by_category'].get('authentication', 0)}
        - Network: {hour_counts['by_category'].get('network', 0)}
        """
        
        # Log the alert (in production, this could send to Slack, email, etc.)
        self.logger.critical(f"EMAIL SERVICE ALERT: {alert_message}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        summary = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "by_code": {},
            "trending": {}
        }
        
        current_time = datetime.utcnow()
        
        for i in range(hours):
            hour_key = (current_time - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            if hour_key in self.error_counts:
                hour_data = self.error_counts[hour_key]
                summary["total_errors"] += hour_data["total"]
                
                # Aggregate by category
                for category, count in hour_data["by_category"].items():
                    summary["by_category"][category] = summary["by_category"].get(category, 0) + count
                
                # Aggregate by severity
                for severity, count in hour_data["by_severity"].items():
                    summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + count
                
                # Aggregate by code
                for code, count in hour_data["by_code"].items():
                    summary["by_code"][code] = summary["by_code"].get(code, 0) + count
        
        return summary


# Global error monitor instance
email_error_monitor = EmailErrorMonitor()


def log_email_error(
    error: Exception,
    service: str,
    operation: str = None,
    user_id: int = None,
    email_account: str = None,
    **kwargs
):
    """
    Convenience function to log email service errors.
    
    Args:
        error: The exception that occurred
        service: Name of the service (e.g., 'gmail_service', 'email_store')
        operation: Specific operation (e.g., 'sync_emails', 'store_chunks')
        user_id: User ID if applicable
        email_account: Email account if applicable
        **kwargs: Additional details to include
    """
    email_error_monitor.log_error(
        error=error,
        service=service,
        operation=operation,
        user_id=user_id,
        email_account=email_account,
        additional_details=kwargs
    )