"""Error handling utilities and models."""

from typing import Any, Dict
from pydantic import BaseModel
from fastapi import HTTPException


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: int
    message: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorDetail


def create_error_response(code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": {
            "code": code,
            "message": message
        }
    }


def raise_http_error(status_code: int, message: str) -> None:
    """Raise an HTTPException with standardized error format."""
    raise HTTPException(
        status_code=status_code,
        detail=create_error_response(status_code, message)
    )