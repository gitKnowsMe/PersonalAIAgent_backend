"""
Error monitoring and alerting system for Personal AI Agent.

Provides comprehensive error tracking, alerting, and performance monitoring.
"""

import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("personal_ai_agent")


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    FILE_PROCESSING = "file_processing"
    EMAIL_SYNC = "email_sync"
    LLM_PROCESSING = "llm_processing"
    API = "api"
    SYSTEM = "system"
    SECURITY = "security"


class ErrorMonitor:
    """
    Comprehensive error monitoring system.
    
    Features:
    - Error tracking and categorization
    - Performance monitoring
    - Alert threshold management
    - Error trend analysis
    - Automated error recovery suggestions
    """
    
    def __init__(self):
        self.error_log: deque = deque(maxlen=1000)  # Keep last 1000 errors
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_trends: Dict[str, deque] = defaultdict(lambda: deque(maxlen=24))  # 24-hour trend
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alerts_sent: Dict[str, datetime] = {}
        self.setup_error_logging()
    
    def setup_error_logging(self):
        """Setup error logging configuration"""
        # Create error log directory
        error_log_dir = Path("logs/errors")
        error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure error logger with separate handler
        error_handler = logging.FileHandler(error_log_dir / "errors.log")
        error_formatter = logging.Formatter(
            '%(asctime)s - ERROR_MONITOR - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        # Create error-specific logger
        self.error_logger = logging.getLogger("personal_ai_agent.errors")
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.addHandler(error_handler)
        self.error_logger.propagate = False
    
    def log_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log an error with comprehensive context.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            user_id: ID of the affected user
            endpoint: API endpoint where error occurred
            request_id: Unique request identifier
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "severity": severity.value,
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user_id": user_id,
            "endpoint": endpoint,
            "request_id": request_id
        }
        
        # Add to error log
        self.error_log.append(error_data)
        
        # Update error counts
        error_key = f"{category.value}:{type(error).__name__}"
        self.error_counts[error_key] += 1
        
        # Update trends (hourly)
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_key = current_hour.isoformat()
        self.error_trends[category.value].append({
            "hour": hour_key,
            "count": 1,
            "severity": severity.value
        })
        
        # Log to file
        self.error_logger.error(json.dumps(error_data))
        
        # Check alert thresholds
        self._check_alert_thresholds(category, severity, error_data)
        
        # Log to main logger based on severity
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"{severity.value.upper()} {category.value} error: {str(error)}")
        else:
            logger.warning(f"{severity.value} {category.value} error: {str(error)}")
    
    def track_performance(self, operation: str, duration_seconds: float, success: bool = True):
        """Track performance metrics for operations"""
        metric_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration": duration_seconds,
            "success": success
        }
        
        self.performance_metrics[operation].append(metric_data)
        
        # Log slow operations
        if duration_seconds > 5.0:  # More than 5 seconds
            logger.warning(f"Slow operation: {operation} took {duration_seconds:.2f}s")
    
    def _check_alert_thresholds(self, category: ErrorCategory, severity: ErrorSeverity, error_data: Dict[str, Any]):
        """Check if error thresholds have been exceeded and send alerts"""
        alert_key = f"{category.value}_{severity.value}"
        current_time = datetime.now()
        
        # Define alert thresholds
        thresholds = {
            f"{ErrorCategory.CRITICAL.value}_critical": {"count": 1, "window_minutes": 1},
            f"{ErrorCategory.AUTHENTICATION.value}_high": {"count": 5, "window_minutes": 5},
            f"{ErrorCategory.DATABASE.value}_high": {"count": 3, "window_minutes": 5},
            f"{ErrorCategory.SECURITY.value}_medium": {"count": 3, "window_minutes": 10}
        }
        
        if alert_key in thresholds:
            threshold = thresholds[alert_key]
            
            # Check if we've already sent an alert recently
            if alert_key in self.alerts_sent:
                last_alert = self.alerts_sent[alert_key]
                if current_time - last_alert < timedelta(minutes=threshold["window_minutes"]):
                    return
            
            # Count recent errors of this type
            recent_errors = [
                err for err in self.error_log
                if err["category"] == category.value
                and err["severity"] == severity.value
                and datetime.fromisoformat(err["timestamp"]) > current_time - timedelta(minutes=threshold["window_minutes"])
            ]
            
            if len(recent_errors) >= threshold["count"]:
                self._send_alert(category, severity, len(recent_errors), error_data)
                self.alerts_sent[alert_key] = current_time
    
    def _send_alert(self, category: ErrorCategory, severity: ErrorSeverity, count: int, error_data: Dict[str, Any]):
        """Send alert for error threshold breach"""
        alert_message = {
            "alert_type": "error_threshold_exceeded",
            "category": category.value,
            "severity": severity.value,
            "error_count": count,
            "latest_error": error_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log alert (in production, this could send emails, Slack messages, etc.)
        logger.error(f"ALERT: {count} {severity.value} {category.value} errors detected")
        self.error_logger.error(f"ALERT: {json.dumps(alert_message)}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            err for err in self.error_log
            if datetime.fromisoformat(err["timestamp"]) > cutoff_time
        ]
        
        # Categorize errors
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        
        for error in recent_errors:
            by_category[error["category"]] += 1
            by_severity[error["severity"]] += 1
            by_type[error["error_type"]] += 1
        
        return {
            "total_errors": len(recent_errors),
            "time_period_hours": hours,
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "latest_errors": recent_errors[-10:] if recent_errors else []
        }
    
    def get_performance_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics summary"""
        if operation:
            metrics = list(self.performance_metrics.get(operation, []))
        else:
            metrics = []
            for op_metrics in self.performance_metrics.values():
                metrics.extend(op_metrics)
        
        if not metrics:
            return {"message": "No performance data available"}
        
        durations = [m["duration"] for m in metrics]
        success_rate = sum(1 for m in metrics if m["success"]) / len(metrics)
        
        return {
            "operation": operation or "all",
            "total_operations": len(metrics),
            "success_rate": success_rate,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "slow_operations_count": sum(1 for d in durations if d > 2.0)
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        recent_errors = self.get_error_summary(hours=1)
        performance = self.get_performance_summary()
        
        # Determine health status
        critical_errors = recent_errors.get("by_severity", {}).get("critical", 0)
        high_errors = recent_errors.get("by_severity", {}).get("high", 0)
        total_recent_errors = recent_errors.get("total_errors", 0)
        
        if critical_errors > 0:
            status = "critical"
        elif high_errors > 3:
            status = "degraded"
        elif total_recent_errors > 10:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "errors_last_hour": total_recent_errors,
            "critical_errors": critical_errors,
            "high_errors": high_errors,
            "performance_status": "good" if performance.get("success_rate", 0) > 0.95 else "degraded",
            "timestamp": datetime.now().isoformat()
        }


# Global error monitor instance
error_monitor = ErrorMonitor()


def log_error(
    error: Exception,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Dict[str, Any] = None,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None
):
    """Convenience function to log errors"""
    error_monitor.log_error(error, category, severity, context, user_id, endpoint)


def track_performance(operation: str, duration_seconds: float, success: bool = True):
    """Convenience function to track performance"""
    error_monitor.track_performance(operation, duration_seconds, success)


def get_error_monitor() -> ErrorMonitor:
    """Get the global error monitor instance"""
    return error_monitor


# Context manager for automatic error tracking
class monitor_operation:
    """Context manager for automatic operation monitoring"""
    
    def __init__(self, operation_name: str, category: ErrorCategory = ErrorCategory.SYSTEM):
        self.operation_name = operation_name
        self.category = category
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        success = exc_type is None
        
        track_performance(self.operation_name, duration, success)
        
        if exc_type is not None:
            severity = ErrorSeverity.HIGH if exc_type in [
                ConnectionError, TimeoutError, MemoryError
            ] else ErrorSeverity.MEDIUM
            
            log_error(exc_val, self.category, severity, {
                "operation": self.operation_name,
                "duration": duration
            })
        
        return False  # Don't suppress exceptions