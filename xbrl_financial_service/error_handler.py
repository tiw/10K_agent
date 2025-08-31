"""
Comprehensive error handling system
Provides structured error responses, logging, and user-friendly messages
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

from .utils.exceptions import (
    XBRLServiceError, XBRLParsingError, DataValidationError,
    CalculationError, QueryError, MCPError, CacheError
)


logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling and response formatting"""
    
    def __init__(self, log_level: str = "INFO", enable_detailed_logging: bool = True):
        """
        Initialize error handler
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_detailed_logging: Whether to log detailed error information
        """
        self.log_level = log_level
        self.enable_detailed_logging = enable_detailed_logging
        self.error_counts = {
            'parsing_errors': 0,
            'validation_errors': 0,
            'calculation_errors': 0,
            'query_errors': 0,
            'mcp_errors': 0,
            'cache_errors': 0,
            'system_errors': 0
        }
        
        # Configure logging
        self._setup_logging()
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_friendly: bool = True
    ) -> Dict[str, Any]:
        """
        Handle any error and return structured response
        
        Args:
            error: The exception to handle
            context: Additional context information
            user_friendly: Whether to return user-friendly messages
            
        Returns:
            Dict: Structured error response
        """
        context = context or {}
        
        # Log the error
        self._log_error(error, context)
        
        # Update error counts
        self._update_error_counts(error)
        
        # Create structured response
        if isinstance(error, XBRLServiceError):
            response = self._handle_service_error(error, context, user_friendly)
        else:
            response = self._handle_system_error(error, context, user_friendly)
        
        # Add metadata
        response['metadata'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_id': self._generate_error_id(),
            'context': context,
            'traceable': self.enable_detailed_logging
        }
        
        return response
    
    def create_error_response(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        severity: str = "error"
    ) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            error_type: Type of error
            message: Error message
            details: Additional error details
            suggestions: Suggested solutions
            severity: Error severity (info, warning, error, critical)
            
        Returns:
            Dict: Structured error response
        """
        return {
            'success': False,
            'error': {
                'type': error_type,
                'message': message,
                'severity': severity,
                'details': details or {},
                'suggestions': suggestions or [],
                'timestamp': datetime.utcnow().isoformat(),
                'error_id': self._generate_error_id()
            }
        }
    
    def create_success_response(
        self,
        data: Any,
        message: Optional[str] = None,
        warnings: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized success response
        
        Args:
            data: Response data
            message: Success message
            warnings: Any warnings to include
            
        Returns:
            Dict: Structured success response
        """
        response = {
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if message:
            response['message'] = message
        
        if warnings:
            response['warnings'] = warnings
        
        return response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics and health metrics
        
        Returns:
            Dict: Error statistics
        """
        total_errors = sum(self.error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_breakdown': self.error_counts.copy(),
            'error_rates': {
                error_type: count / max(total_errors, 1)
                for error_type, count in self.error_counts.items()
            },
            'health_status': self._assess_health_status(),
            'recommendations': self._get_health_recommendations()
        }
    
    def reset_error_counts(self) -> None:
        """Reset error counters"""
        for key in self.error_counts:
            self.error_counts[key] = 0
    
    def _handle_service_error(
        self,
        error: XBRLServiceError,
        context: Dict[str, Any],
        user_friendly: bool
    ) -> Dict[str, Any]:
        """Handle XBRL service specific errors"""
        response = {
            'success': False,
            'error': error.to_dict()
        }
        
        if user_friendly:
            response['error']['message'] = self._make_user_friendly(error.error_type, str(error))
            
            # Add context-specific suggestions
            if error.error_type == 'parsing_error' and 'file_path' in context:
                response['error']['suggestions'].extend([
                    f"Check file: {context['file_path']}",
                    "Verify file is not corrupted or truncated"
                ])
            elif error.error_type == 'validation_error':
                response['error']['suggestions'].extend([
                    "Review data quality report for specific issues",
                    "Check source filing for accuracy"
                ])
        
        return response
    
    def _handle_system_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        user_friendly: bool
    ) -> Dict[str, Any]:
        """Handle system/unexpected errors"""
        error_type = type(error).__name__
        
        response = {
            'success': False,
            'error': {
                'type': 'system_error',
                'message': str(error) if not user_friendly else "An unexpected error occurred",
                'system_error_type': error_type,
                'details': {
                    'error_class': error_type,
                    'error_module': getattr(error, '__module__', 'unknown')
                },
                'suggestions': [
                    "Please try again",
                    "If the problem persists, contact support",
                    "Check system logs for more details"
                ]
            }
        }
        
        # Add traceback for debugging (only if detailed logging is enabled)
        if self.enable_detailed_logging:
            response['error']['details']['traceback'] = traceback.format_exc()
        
        return response
    
    def _log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with appropriate level and detail"""
        error_type = type(error).__name__
        
        # Determine log level based on error type
        if isinstance(error, (XBRLParsingError, DataValidationError)):
            log_level = logging.WARNING
        elif isinstance(error, (CalculationError, QueryError)):
            log_level = logging.ERROR
        elif isinstance(error, (MCPError, CacheError)):
            log_level = logging.ERROR
        else:
            log_level = logging.ERROR
        
        # Create log message
        log_message = f"{error_type}: {str(error)}"
        
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_message += f" | Context: {context_str}"
        
        # Log with appropriate level
        logger.log(log_level, log_message)
        
        # Log traceback for system errors
        if not isinstance(error, XBRLServiceError) and self.enable_detailed_logging:
            logger.debug("Traceback:", exc_info=True)
    
    def _update_error_counts(self, error: Exception) -> None:
        """Update error counters based on error type"""
        if isinstance(error, XBRLParsingError):
            self.error_counts['parsing_errors'] += 1
        elif isinstance(error, DataValidationError):
            self.error_counts['validation_errors'] += 1
        elif isinstance(error, CalculationError):
            self.error_counts['calculation_errors'] += 1
        elif isinstance(error, QueryError):
            self.error_counts['query_errors'] += 1
        elif isinstance(error, MCPError):
            self.error_counts['mcp_errors'] += 1
        elif isinstance(error, CacheError):
            self.error_counts['cache_errors'] += 1
        else:
            self.error_counts['system_errors'] += 1
    
    def _make_user_friendly(self, error_type: str, message: str) -> str:
        """Convert technical error messages to user-friendly ones"""
        user_friendly_messages = {
            'parsing_error': "There was a problem reading the XBRL file. The file may be corrupted or in an unexpected format.",
            'validation_error': "The financial data doesn't meet quality standards. Some information may be missing or inconsistent.",
            'calculation_error': "There are inconsistencies in the financial calculations. The numbers don't add up as expected.",
            'query_error': "Unable to find the requested financial information. The data may not be available for the specified period.",
            'mcp_error': "There was a communication problem with the financial data service.",
            'cache_error': "There was a problem accessing stored data. Please try again.",
            'system_error': "An unexpected technical problem occurred. Please try again or contact support."
        }
        
        return user_friendly_messages.get(error_type, message)
    
    def _assess_health_status(self) -> str:
        """Assess system health based on error patterns"""
        total_errors = sum(self.error_counts.values())
        
        if total_errors == 0:
            return "healthy"
        elif total_errors < 5:
            return "warning"
        elif total_errors < 20:
            return "degraded"
        else:
            return "critical"
    
    def _get_health_recommendations(self) -> List[str]:
        """Get recommendations based on error patterns"""
        recommendations = []
        total_errors = sum(self.error_counts.values())
        
        if total_errors == 0:
            return ["System is operating normally"]
        
        # Check for high parsing errors
        if self.error_counts['parsing_errors'] > 3:
            recommendations.append("High number of parsing errors - check XBRL file quality")
        
        # Check for high validation errors
        if self.error_counts['validation_errors'] > 5:
            recommendations.append("Data quality issues detected - review source filings")
        
        # Check for high calculation errors
        if self.error_counts['calculation_errors'] > 2:
            recommendations.append("Calculation inconsistencies found - verify linkbase relationships")
        
        # Check for system errors
        if self.error_counts['system_errors'] > 1:
            recommendations.append("System errors detected - check logs and system resources")
        
        if not recommendations:
            recommendations.append("Monitor error patterns and check system logs")
        
        return recommendations
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # This would typically be configured at application startup
        # Here we just ensure the logger is properly configured
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, self.log_level.upper()))


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(
    return_response: bool = True,
    log_errors: bool = True,
    user_friendly: bool = True
):
    """
    Decorator for automatic error handling
    
    Args:
        return_response: Whether to return structured error response
        log_errors: Whether to log errors
        user_friendly: Whether to use user-friendly messages
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If function returns a dict, wrap in success response
                if return_response and isinstance(result, dict) and 'success' not in result:
                    return error_handler.create_success_response(result)
                
                return result
                
            except Exception as e:
                if log_errors:
                    context = {
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                    
                    if return_response:
                        return error_handler.handle_error(e, context, user_friendly)
                    else:
                        error_handler._log_error(e, context)
                        raise
                else:
                    raise
        
        return wrapper
    return decorator


@contextmanager
def error_context(context_info: Dict[str, Any]):
    """
    Context manager for adding context to errors
    
    Args:
        context_info: Context information to add to errors
    """
    try:
        yield
    except Exception as e:
        # Re-raise with additional context
        if isinstance(e, XBRLServiceError):
            e.details.update(context_info)
        raise


def validate_and_handle_errors(validation_func, data, error_message: str = "Validation failed"):
    """
    Helper function to validate data and handle errors
    
    Args:
        validation_func: Function to validate data
        data: Data to validate
        error_message: Error message if validation fails
        
    Returns:
        Validation result
        
    Raises:
        DataValidationError: If validation fails
    """
    try:
        return validation_func(data)
    except Exception as e:
        if isinstance(e, XBRLServiceError):
            raise
        else:
            raise DataValidationError(
                f"{error_message}: {str(e)}",
                validation_type="data_validation",
                details={"original_error": str(e), "data_type": type(data).__name__}
            )