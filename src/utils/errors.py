"""Error handling utilities and models."""

from typing import Any, Dict, Literal
from pydantic import BaseModel
from fastapi import HTTPException


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: int
    message: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorDetail


class StructuredErrorResponse(BaseModel):
    """CHA-110 structured error response format."""
    error: bool
    message: str
    retry_action: str
    error_code: str


def create_error_response(code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": {
            "code": code,
            "message": message
        }
    }


def create_structured_error(
    message: str,
    error_code: str,
    retry_action: Literal["restart_or_retry", "retry_or_restart", "retry_or_new_message", "retry", "restart"]
) -> Dict[str, Any]:
    """Create a CHA-110 structured error response."""
    return {
        "error": True,
        "message": message,
        "retry_action": retry_action,
        "error_code": error_code
    }


def raise_http_error(status_code: int, message: str) -> None:
    """Raise an HTTPException with standardized error format."""
    raise HTTPException(
        status_code=status_code,
        detail=create_error_response(status_code, message)
    )


def raise_structured_error(
    status_code: int,
    message: str,
    error_code: str,
    retry_action: Literal["restart_or_retry", "retry_or_restart", "retry_or_new_message", "retry", "restart"]
) -> None:
    """Raise an HTTPException with CHA-110 structured error format."""
    raise HTTPException(
        status_code=status_code,
        detail=create_structured_error(message, error_code, retry_action)
    )