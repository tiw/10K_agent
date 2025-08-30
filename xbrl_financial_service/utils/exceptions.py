"""
Custom exceptions for XBRL Financial Service
"""

from typing import Optional, Dict, Any, List


class XBRLServiceError(Exception):
    """Base exception for all XBRL service errors"""
    
    def __init__(
        self,
        message: str,
        error_type: str = "service_error",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization"""
        return {
            "error_type": self.error_type,
            "message": str(self),
            "details": self.details,
            "suggestions": self.suggestions
        }


class XBRLParsingError(XBRLServiceError):
    """Raised when XBRL file parsing fails"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if file_path:
            details["file_path"] = file_path
        if line_number:
            details["line_number"] = line_number
            
        super().__init__(
            message,
            error_type="parsing_error",
            details=details,
            suggestions=kwargs.get("suggestions", [
                "Check XBRL file format and structure",
                "Validate XML syntax",
                "Ensure all required files are present"
            ])
        )


class DataValidationError(XBRLServiceError):
    """Raised when data validation fails"""
    
    def __init__(
        self,
        message: str,
        validation_type: str = "general",
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["validation_type"] = validation_type
        
        super().__init__(
            message,
            error_type="validation_error",
            details=details,
            suggestions=kwargs.get("suggestions", [
                "Check data format and types",
                "Verify required fields are present",
                "Review data consistency"
            ])
        )


class CalculationError(XBRLServiceError):
    """Raised when financial calculations fail or are inconsistent"""
    
    def __init__(
        self,
        message: str,
        calculation_type: str = "general",
        expected_value: Optional[float] = None,
        actual_value: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["calculation_type"] = calculation_type
        if expected_value is not None:
            details["expected_value"] = expected_value
        if actual_value is not None:
            details["actual_value"] = actual_value
            
        super().__init__(
            message,
            error_type="calculation_error",
            details=details,
            suggestions=kwargs.get("suggestions", [
                "Review calculation relationships",
                "Check for missing or incorrect values",
                "Verify calculation weights and formulas"
            ])
        )


class QueryError(XBRLServiceError):
    """Raised when data queries fail"""
    
    def __init__(
        self,
        message: str,
        query_type: str = "general",
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["query_type"] = query_type
        
        super().__init__(
            message,
            error_type="query_error",
            details=details,
            suggestions=kwargs.get("suggestions", [
                "Check query parameters and syntax",
                "Verify data availability for requested period",
                "Review filter criteria"
            ])
        )


class MCPError(XBRLServiceError):
    """Raised when MCP protocol operations fail"""
    
    def __init__(
        self,
        message: str,
        mcp_operation: str = "general",
        **kwargs
    ):
        details = kwargs.get("details", {})
        details["mcp_operation"] = mcp_operation
        
        super().__init__(
            message,
            error_type="mcp_error",
            details=details,
            suggestions=kwargs.get("suggestions", [
                "Check MCP client connection",
                "Verify tool parameters",
                "Review MCP protocol compliance"
            ])
        )