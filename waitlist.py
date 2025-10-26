"""
Waitlist schemas for sold-out event management.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class JoinWaitlistRequest(BaseModel):
    """Join waitlist request schema."""

    event_id: int = Field(
        ge=1,
        description="Event ID to join waitlist for"
    )
    tier_id: Optional[int] = Field(
        default=None,
        description="Optional: specific tier to wait for"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "tier_id": 2
            }
        }


class WaitlistResponse(BaseModel):
    """Waitlist entry response schema."""

    id: int = Field(description="Waitlist entry ID")
    event_id: int = Field(description="Event ID")
    tier_id: Optional[int] = Field(default=None, description="Tier ID (if tier-specific)")
    position: int = Field(description="Position in waitlist (1 = first)")
    status: str = Field(
        description="Waitlist status (waiting, notified, expired, fulfilled)"
    )
    notified: bool = Field(description="Has user been notified")
    notified_at: Optional[datetime] = Field(default=None, description="Notification timestamp")
    notification_expires_at: Optional[datetime] = Field(
        default=None,
        description="When notification expires"
    )
    responded_at: Optional[datetime] = Field(default=None, description="When user responded")
    created_at: datetime = Field(description="Join timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "event_id": 1,
                "position": 1,
                "status": "waiting",
                "notified": False,
                "created_at": "2025-10-26T10:00:00Z"
            }
        }


class WaitlistDetailResponse(BaseModel):
    """Detailed waitlist entry response."""

    id: int = Field(description="Waitlist entry ID")
    event: "EventWaitlistInfo" = Field(description="Event details")
    tier: Optional["TierWaitlistInfo"] = Field(default=None, description="Tier details if tier-specific")
    position: int = Field(description="Position in waitlist")
    status: str = Field(description="Status")
    notified: bool = Field(description="Notified status")
    notified_at: Optional[datetime] = Field(default=None, description="Notification time")
    notification_expires_at: Optional[datetime] = Field(default=None, description="Notification expiration")
    responded_at: Optional[datetime] = Field(default=None, description="Response time")
    created_at: datetime = Field(description="Join time")
    updated_at: datetime = Field(description="Update time")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class EventWaitlistInfo(BaseModel):
    """Event information in waitlist response."""

    id: int = Field(description="Event ID")
    title: str = Field(description="Event title")
    start_time: datetime = Field(description="Event start time")
    venue_name: str = Field(description="Venue name")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class TierWaitlistInfo(BaseModel):
    """Tier information in waitlist response."""

    id: int = Field(description="Tier ID")
    name: str = Field(description="Tier name")
    price: float = Field(description="Tier price")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class LeaveWaitlistRequest(BaseModel):
    """Leave waitlist request schema."""

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for leaving"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "reason": "Found tickets elsewhere"
            }
        }


class WaitlistNotificationResponse(BaseModel):
    """Waitlist notification response."""

    id: int = Field(description="Waitlist entry ID")
    message: str = Field(description="Notification message")
    tickets_available: int = Field(description="Number of tickets available")
    expiration_time: datetime = Field(description="When this notification expires")
    action_url: str = Field(description="URL to complete purchase")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "id": 1,
                "message": "Tickets are now available! You are first in line.",
                "tickets_available": 5,
                "expiration_time": "2025-10-26T12:00:00Z",
                "action_url": "https://api.example.com/waitlist/1/purchase"
            }
        }


class RespondToWaitlistRequest(BaseModel):
    """Respond to waitlist notification request."""

    action: str = Field(
        regex="^(purchase|decline)$",
        description="Action to take (purchase or decline)"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "action": "purchase"
            }
        }


class WaitlistListResponse(BaseModel):
    """Waitlist entry in list response (minimal)."""

    id: int = Field(description="Waitlist entry ID")
    event_title: str = Field(description="Event title")
    tier_name: Optional[str] = Field(default=None, description="Tier name if tier-specific")
    position: int = Field(description="Position in line")
    status: str = Field(description="Status")
    created_at: datetime = Field(description="Join timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class JoinWaitlistResponse(BaseModel):
    """Response when joining waitlist."""

    waitlist: WaitlistResponse = Field(description="Waitlist entry created")
    message: str = Field(description="Status message")
    position: int = Field(description="Position in waitlist")
    estimated_wait: Optional[str] = Field(
        default=None,
        description="Estimated wait time (e.g., '2-3 weeks')"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "message": "Successfully joined waitlist!",
                "position": 1,
                "estimated_wait": "2-3 weeks",
                "waitlist": {
                    "id": 1,
                    "position": 1,
                    "status": "waiting"
                }
            }
        }


class WaitlistMetricsResponse(BaseModel):
    """Waitlist metrics for an event (promoter view)."""

    event_id: int = Field(description="Event ID")
    total_waitlist_count: int = Field(description="Total entries on waitlist")
    tier_id: Optional[int] = Field(default=None, description="Tier ID if tier-specific")
    tier_name: Optional[str] = Field(default=None, description="Tier name if tier-specific")
    waiting_count: int = Field(description="Count of waiting users")
    notified_count: int = Field(description="Count of notified users")
    fulfilled_count: int = Field(description="Count of fulfilled requests")
    expired_count: int = Field(description="Count of expired notifications")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "total_waitlist_count": 50,
                "waiting_count": 30,
                "notified_count": 15,
                "fulfilled_count": 5,
                "expired_count": 0
            }
        }


class BulkNotifyWaitlistRequest(BaseModel):
    """Bulk notify waitlist request (promoter action)."""

    event_id: int = Field(description="Event ID")
    tier_id: Optional[int] = Field(default=None, description="Optional tier ID to notify for specific tier")
    count: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Number of users to notify from top of waitlist"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Custom message to include in notification"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "count": 20,
                "message": "Great news! More tickets have become available!"
            }
        }


class BulkNotifyResponse(BaseModel):
    """Response from bulk notify action."""

    event_id: int = Field(description="Event ID")
    notified_count: int = Field(description="Number of users notified")
    message: str = Field(description="Status message")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "notified_count": 20,
                "message": "Successfully notified 20 users from the waitlist"
            }
        }


# Update forward references
WaitlistDetailResponse.model_rebuild()
