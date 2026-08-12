"""
Legal AI System - Standardized API Responses
==============================================
Common response models used across all API endpoints.
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: Optional[str] = None
    message: str


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response envelope.
    All API endpoints return this structure for consistency.
    """
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None
    errors: Optional[List[ErrorDetail]] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[PaginationMeta] = None,
) -> dict:
    """Create a standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta.model_dump() if meta else None,
        "errors": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def paginated_response(
    data: Any,
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> dict:
    """Create a standardized paginated response."""
    total_pages = (total + per_page - 1) // per_page
    return success_response(
        data=data,
        message=message,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )
