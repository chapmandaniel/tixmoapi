"""
Common schemas used across the API.

Includes pagination, error responses, and shared response models.
"""

from typing import Generic, TypeVar, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(
        default="asc",
        regex="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'"
    )


class PagedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Number of items in this page")
    has_more: bool = Field(description="Whether there are more items")

    @property
    def page_number(self) -> int:
        """Calculate page number from skip and limit."""
        return (self.skip // self.limit) + 1


class ErrorDetail(BaseModel):
    """Error detail with field and message."""

    field: Optional[str] = Field(default=None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[list[ErrorDetail]] = Field(default=None, description="Detailed error info")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status (healthy, degraded, unhealthy)")
    version: str = Field(description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, str] = Field(default_factory=dict, description="Component health checks")


class MetadataResponse(BaseModel):
    """Base response with metadata."""

    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response wrapper."""

    data: T
    message: str = Field(default="Success", description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# HTTP Status Code Documentation
# 200: OK - Successful GET, PUT, DELETE
# 201: Created - Successful POST
# 204: No Content - Successful DELETE returning no content
# 400: Bad Request - Invalid input validation
# 401: Unauthorized - Missing or invalid authentication
# 403: Forbidden - Authenticated but not authorized
# 404: Not Found - Resource not found
# 409: Conflict - Business logic violation (e.g., sold out)
# 429: Too Many Requests - Rate limited
# 500: Internal Server Error - Server error
# 503: Service Unavailable - Service temporarily down


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(description="Response message")
