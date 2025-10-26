"""
Event schemas for event management and CRUD operations.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class EventStatus(str, Enum):
    """Event status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventCreate(BaseModel):
    """Create event request schema."""

    title: str = Field(
        min_length=1,
        max_length=255,
        description="Event title"
    )
    description: Optional[str] = Field(
        default=None,
        description="Event description"
    )
    venue_name: str = Field(
        min_length=1,
        max_length=255,
        description="Venue name"
    )
    venue_address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Venue address"
    )
    venue_city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Venue city"
    )
    venue_state: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Venue state/province"
    )
    venue_country: str = Field(
        default="US",
        min_length=2,
        max_length=2,
        description="Venue country code"
    )
    venue_latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Venue latitude"
    )
    venue_longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Venue longitude"
    )
    start_time: datetime = Field(description="Event start time (ISO 8601 format)")
    end_time: datetime = Field(description="Event end time (must be after start_time)")
    doors_open_time: Optional[datetime] = Field(
        default=None,
        description="Doors open time (must be before or equal to start_time)"
    )
    timezone: str = Field(
        default="UTC",
        description="Event timezone (e.g., 'America/New_York')"
    )
    capacity: int = Field(
        ge=1,
        le=1000000,
        description="Event capacity (number of tickets total)"
    )
    age_restriction: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Minimum age restriction"
    )
    is_private: bool = Field(
        default=False,
        description="Whether event is private (invite-only)"
    )
    featured_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Featured image URL"
    )
    banner_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Banner image URL"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Event category (e.g., 'music', 'sports', 'comedy')"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Event tags for categorization"
    )

    @validator("end_time")
    def end_after_start(cls, v, values):
        """Validate end time is after start time."""
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("Event end_time must be after start_time")
        return v

    @validator("doors_open_time")
    def doors_before_start(cls, v, values):
        """Validate doors open time is before start time."""
        if v is not None and "start_time" in values and v > values["start_time"]:
            raise ValueError("Doors open time must be before or equal to start time")
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "title": "Summer Music Festival 2025",
                "description": "The biggest music festival of the summer!",
                "venue_name": "Central Park",
                "venue_city": "New York",
                "venue_state": "NY",
                "venue_country": "US",
                "start_time": "2025-07-15T18:00:00Z",
                "end_time": "2025-07-15T23:00:00Z",
                "timezone": "America/New_York",
                "capacity": 5000,
                "category": "music",
                "tags": ["festival", "music", "summer"]
            }
        }


class EventUpdate(BaseModel):
    """Update event request schema."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Event title"
    )
    description: Optional[str] = Field(default=None, description="Event description")
    venue_name: Optional[str] = Field(default=None, max_length=255, description="Venue name")
    venue_address: Optional[str] = Field(default=None, max_length=500, description="Venue address")
    venue_city: Optional[str] = Field(default=None, max_length=100, description="Venue city")
    venue_state: Optional[str] = Field(default=None, max_length=100, description="Venue state")
    venue_latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Latitude")
    venue_longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Longitude")
    doors_open_time: Optional[datetime] = Field(default=None, description="Doors open time")
    timezone: Optional[str] = Field(default=None, description="Event timezone")
    capacity: Optional[int] = Field(default=None, ge=1, le=1000000, description="Capacity")
    age_restriction: Optional[int] = Field(default=None, ge=0, le=120, description="Age restriction")
    is_private: Optional[bool] = Field(default=None, description="Is private")
    featured_image_url: Optional[str] = Field(default=None, max_length=500, description="Featured image")
    banner_image_url: Optional[str] = Field(default=None, max_length=500, description="Banner image")
    category: Optional[str] = Field(default=None, max_length=50, description="Category")
    tags: Optional[list[str]] = Field(default=None, description="Tags")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "title": "Summer Music Festival 2025 - UPDATED",
                "capacity": 6000
            }
        }


class EventResponse(BaseModel):
    """Event response schema."""

    id: int = Field(description="Event ID")
    uuid: str = Field(description="Event UUID")
    title: str = Field(description="Event title")
    slug: str = Field(description="URL-friendly event slug")
    description: Optional[str] = Field(default=None, description="Event description")
    venue_name: str = Field(description="Venue name")
    venue_address: Optional[str] = Field(default=None, description="Venue address")
    venue_city: Optional[str] = Field(default=None, description="Venue city")
    venue_state: Optional[str] = Field(default=None, description="Venue state")
    venue_country: str = Field(description="Venue country")
    start_time: datetime = Field(description="Event start time")
    end_time: datetime = Field(description="Event end time")
    timezone: str = Field(description="Event timezone")
    status: str = Field(description="Event status (draft, published, cancelled, completed)")
    capacity: int = Field(description="Event capacity")
    age_restriction: Optional[int] = Field(default=None, description="Age restriction")
    is_private: bool = Field(description="Is private")
    featured_image_url: Optional[str] = Field(default=None, description="Featured image")
    category: Optional[str] = Field(default=None, description="Event category")
    tags: Optional[list[str]] = Field(default=None, description="Event tags")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    promoter_id: int = Field(description="Promoter ID")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Summer Music Festival 2025",
                "slug": "summer-music-festival-2025",
                "venue_name": "Central Park",
                "venue_city": "New York",
                "start_time": "2025-07-15T18:00:00Z",
                "end_time": "2025-07-15T23:00:00Z",
                "status": "published",
                "capacity": 5000,
                "created_at": "2025-10-26T10:00:00Z"
            }
        }


class EventDetailResponse(BaseModel):
    """Detailed event response schema with ticket tiers."""

    id: int = Field(description="Event ID")
    uuid: str = Field(description="Event UUID")
    title: str = Field(description="Event title")
    slug: str = Field(description="URL-friendly event slug")
    description: Optional[str] = Field(default=None, description="Event description")
    venue_name: str = Field(description="Venue name")
    venue_address: Optional[str] = Field(default=None, description="Venue address")
    venue_city: Optional[str] = Field(default=None, description="Venue city")
    venue_state: Optional[str] = Field(default=None, description="Venue state")
    venue_country: str = Field(description="Venue country")
    venue_latitude: Optional[float] = Field(default=None, description="Latitude")
    venue_longitude: Optional[float] = Field(default=None, description="Longitude")
    start_time: datetime = Field(description="Event start time")
    end_time: datetime = Field(description="Event end time")
    doors_open_time: Optional[datetime] = Field(default=None, description="Doors open time")
    timezone: str = Field(description="Event timezone")
    status: str = Field(description="Event status")
    capacity: int = Field(description="Event capacity")
    age_restriction: Optional[int] = Field(default=None, description="Age restriction")
    is_private: bool = Field(description="Is private")
    featured_image_url: Optional[str] = Field(default=None, description="Featured image")
    banner_image_url: Optional[str] = Field(default=None, description="Banner image")
    category: Optional[str] = Field(default=None, description="Event category")
    tags: Optional[list[str]] = Field(default=None, description="Event tags")
    view_count: int = Field(description="Number of times viewed")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    cancelled_at: Optional[datetime] = Field(default=None, description="Cancellation timestamp")
    cancellation_reason: Optional[str] = Field(default=None, description="Reason for cancellation")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    promoter: "PromoterSummary" = Field(description="Promoter information")
    tiers: list["TicketTierSummary"] = Field(default_factory=list, description="Ticket tiers")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PromoterSummary(BaseModel):
    """Promoter summary for event response."""

    id: int = Field(description="Promoter ID")
    company_name: Optional[str] = Field(default=None, description="Company name")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class TicketTierSummary(BaseModel):
    """Ticket tier summary for event response."""

    id: int = Field(description="Tier ID")
    name: str = Field(description="Tier name")
    price: float = Field(description="Tier price")
    available: int = Field(description="Available tickets")
    sold: int = Field(description="Sold tickets")
    quantity: int = Field(description="Total quantity")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PublishEventRequest(BaseModel):
    """Publish event request schema."""

    message: Optional[str] = Field(
        default=None,
        description="Optional message to include with publication"
    )


class CancelEventRequest(BaseModel):
    """Cancel event request schema."""

    reason: str = Field(
        min_length=1,
        max_length=500,
        description="Reason for cancellation"
    )
    refund_tickets: bool = Field(
        default=True,
        description="Whether to refund all ticket purchases"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "reason": "Venue became unavailable",
                "refund_tickets": True
            }
        }


class EventListResponse(BaseModel):
    """Event list response schema (minimal)."""

    id: int = Field(description="Event ID")
    uuid: str = Field(description="Event UUID")
    title: str = Field(description="Event title")
    slug: str = Field(description="Event slug")
    venue_city: Optional[str] = Field(default=None, description="Venue city")
    start_time: datetime = Field(description="Start time")
    featured_image_url: Optional[str] = Field(default=None, description="Featured image")
    category: Optional[str] = Field(default=None, description="Category")
    status: str = Field(description="Status")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# Update forward references
EventDetailResponse.model_rebuild()
