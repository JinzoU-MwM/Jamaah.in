"""
Custom error handlers for structured error responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"


class ValidationError(AppError):
    """Data validation error."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR")


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class UnauthorizedError(AppError):
    """Unauthorized access error."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


async def app_error_handler(request: Request, exc: AppError):
    """Handle application errors."""
    logger.error(
        "Application error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        }
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from Pydantic."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Data yang dikirim tidak valid",
                "details": exc.errors(),
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected error",
        error_type=type(exc).__name__,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Terjadi kesalahan pada server. Silakan coba lagi nanti.",
            }
        }
    )
