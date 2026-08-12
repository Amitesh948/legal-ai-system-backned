"""
Legal AI System - Custom Exceptions
====================================
Centralized exception classes for consistent error handling.
"""

from typing import Any, Dict, List, Optional


class LegalAIException(Exception):
    """Base exception for the Legal AI System."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(self.message)


class BadRequestException(LegalAIException):
    """400 - Bad Request."""

    def __init__(self, message: str = "Bad request", errors: Optional[List] = None):
        super().__init__(message=message, status_code=400, errors=errors)


class UnauthorizedException(LegalAIException):
    """401 - Unauthorized."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(LegalAIException):
    """403 - Forbidden."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message=message, status_code=403)


class NotFoundException(LegalAIException):
    """404 - Not Found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ConflictException(LegalAIException):
    """409 - Conflict."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class ValidationException(LegalAIException):
    """422 - Validation Error."""

    def __init__(self, message: str = "Validation failed", errors: Optional[List] = None):
        super().__init__(message=message, status_code=422, errors=errors)


class FileUploadException(LegalAIException):
    """413 - File too large or invalid."""

    def __init__(self, message: str = "File upload error"):
        super().__init__(message=message, status_code=413)


class PaymentException(LegalAIException):
    """402 - Payment error."""

    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message=message, status_code=402)


class AIProcessingException(LegalAIException):
    """503 - AI service unavailable or processing failed."""

    def __init__(self, message: str = "AI processing failed"):
        super().__init__(message=message, status_code=503)
