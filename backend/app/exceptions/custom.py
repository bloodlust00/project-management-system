from typing import Any, List, Optional


class BaseAppException(Exception):
    """Base exception for all system-level exceptions."""

    def __init__(self, message: str, status_code: int = 500, errors: Optional[List[Any]] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


class NotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ForbiddenException(BaseAppException):
    """Exception raised when access to a resource is forbidden."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


class UnauthorizedException(BaseAppException):
    """Exception raised when authentication fails or is missing."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)


class BadRequestException(BaseAppException):
    """Exception raised when user input is invalid or contains malformed syntax."""

    def __init__(self, message: str = "Bad request", errors: Optional[List[Any]] = None):
        super().__init__(message=message, status_code=400, errors=errors)


class ConflictException(BaseAppException):
    """Exception raised when database conflict occurs (e.g. duplicate keys)."""

    def __init__(self, message: str = "Resource conflict already exists"):
        super().__init__(message=message, status_code=409)


class RateLimitException(BaseAppException):
    """Exception raised when API requests exceed threshold constraints."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message=message, status_code=429)


class DatabaseException(BaseAppException):
    """Exception raised when data storage engines error out."""

    def __init__(self, message: str = "Database transaction failed"):
        super().__init__(message=message, status_code=500)
