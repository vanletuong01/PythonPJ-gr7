"""
Custom Exceptions + Global Error Handlers
Xử lý lỗi toàn cầu với structured error responses
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception class cho ứng dụng"""
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Input validation lỗi"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotFoundException(AppException):
    """Resource không tìm thấy"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource} '{identifier}' không tìm thấy",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UnauthorizedException(AppException):
    """Xác thực thất bại"""
    def __init__(self, message: str = "Xác thực thất bại"):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(AppException):
    """Không có quyền truy cập"""
    def __init__(self, message: str = "Không có quyền truy cập"):
        super().__init__(
            error_code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class DatabaseException(AppException):
    """Database operation lỗi"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            error_code="DATABASE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceException(AppException):
    """External API / service lỗi"""
    def __init__(self, service: str, message: str):
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class RateLimitException(AppException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[dict] = None,
    request_id: Optional[str] = None,
    include_traceback: bool = False
) -> dict:
    """Tạo structured error response"""
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()
    
    return response


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler cho tất cả exceptions"""
    
    # Lấy request ID từ headers
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Handle custom AppException
    if isinstance(exc, AppException):
        logger.warning(
            f"AppException: {exc.error_code} - {exc.message}",
            extra={"request_id": request_id, "error_code": exc.error_code}
        )
        error_response = create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    # Handle validation errors
    if isinstance(exc, RequestValidationError):
        logger.warning(
            f"ValidationError: {str(exc)}",
            extra={"request_id": request_id}
        )
        error_response = create_error_response(
            error_code="VALIDATION_ERROR",
            message="Input validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.errors(),
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response
        )
    
    # Handle unexpected errors
    logger.error(
        f"Unexpected error: {type(exc).__name__}: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    error_response = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        include_traceback=True  # Only in development
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def setup_exception_handlers(app: FastAPI):
    """Đăng ký exception handlers vào FastAPI app"""
    app.add_exception_handler(AppException, global_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
