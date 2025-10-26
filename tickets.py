"""
Ticket tier and individual ticket schemas.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enumeration."""

    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class CreateTicketTierRequest(BaseModel):
    """Create ticket tier request schema."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Tier name (e.g., 'General Admission', 'VIP')"
    )
    description: Optional[str] = Field(
        default=None,
        description="Tier description"
    )
    price: float = Field(
        ge=0,
        le=999999.99,
        description="Ticket price"
    )
    quantity: int = Field(
        ge=1,
        le=1000000,
        description="Number of tickets available"
    )
    min_purchase: int = Field(
        default=1,
        ge=1,
        le=1000,
        description="Minimum tickets per purchase"
    )
    max_purchase: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum tickets per purchase"
    )
    position: int = Field(
        default=0,
        ge=0,
        description="Display order position"
    )
    sale_start_time: Optional[datetime] = Field(
        default=None,
        description="When ticket sales begin"
    )
    sale_end_time: Optional[datetime] = Field(
        default=None,
        description="When ticket sales end"
    )
    is_active: bool = Field(
        default=True,
        description="Whether tier is active"
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether purchases require approval"
    )

    @validator("max_purchase")
    def max_gte_min(cls, v, values):
        """Validate max_purchase >= min_purchase."""
        if "min_purchase" in values and v < values["min_purchase"]:
            raise ValueError("max_purchase must be >= min_purchase")
        return v

    @validator("sale_end_time")
    def end_after_start(cls, v, values):
        """Validate sale_end_time > sale_start_time."""
        if v is not None and "sale_start_time" in values:
            if values["sale_start_time"] is not None and v <= values["sale_start_time"]:
                raise ValueError("sale_end_time must be after sale_start_time")
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "General Admission",
                "description": "General admission to the event",
                "price": 49.99,
                "quantity": 1000,
                "min_purchase": 1,
                "max_purchase": 10,
                "sale_start_time": "2025-10-26T00:00:00Z",
                "sale_end_time": "2025-07-14T23:59:59Z"
            }
        }


class UpdateTicketTierRequest(BaseModel):
    """Update ticket tier request schema."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Tier name"
    )
    description: Optional[str] = Field(default=None, description="Tier description")
    price: Optional[float] = Field(default=None, ge=0, le=999999.99, description="Price")
    quantity: Optional[int] = Field(default=None, ge=1, le=1000000, description="Quantity")
    min_purchase: Optional[int] = Field(default=None, ge=1, le=1000, description="Min purchase")
    max_purchase: Optional[int] = Field(default=None, ge=1, le=1000, description="Max purchase")
    position: Optional[int] = Field(default=None, ge=0, description="Position")
    sale_start_time: Optional[datetime] = Field(default=None, description="Sale start time")
    sale_end_time: Optional[datetime] = Field(default=None, description="Sale end time")
    is_active: Optional[bool] = Field(default=None, description="Is active")
    requires_approval: Optional[bool] = Field(default=None, description="Requires approval")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "quantity": 500,
                "is_active": False
            }
        }


class TicketTierResponse(BaseModel):
    """Ticket tier response schema."""

    id: int = Field(description="Tier ID")
    uuid: str = Field(description="Tier UUID")
    event_id: int = Field(description="Associated event ID")
    name: str = Field(description="Tier name")
    description: Optional[str] = Field(default=None, description="Tier description")
    price: float = Field(description="Ticket price")
    quantity: int = Field(description="Total quantity")
    sold: int = Field(description="Number sold")
    reserved: int = Field(description="Number reserved (on hold)")
    available: int = Field(description="Available for purchase")
    min_purchase: int = Field(description="Minimum purchase")
    max_purchase: int = Field(description="Maximum purchase")
    position: int = Field(description="Display position")
    sale_start_time: Optional[datetime] = Field(default=None, description="Sale start time")
    sale_end_time: Optional[datetime] = Field(default=None, description="Sale end time")
    is_active: bool = Field(description="Is active")
    requires_approval: bool = Field(description="Requires approval")
    is_sold_out: bool = Field(description="Is sold out")
    percent_sold: float = Field(description="Percentage of tickets sold")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "event_id": 1,
                "name": "General Admission",
                "price": 49.99,
                "quantity": 1000,
                "sold": 500,
                "reserved": 100,
                "available": 400,
                "is_active": True,
                "is_sold_out": False,
                "percent_sold": 50.0
            }
        }


class TicketTierAvailabilityResponse(BaseModel):
    """Ticket tier availability response."""

    tier_id: int = Field(description="Tier ID")
    tier_name: str = Field(description="Tier name")
    price: float = Field(description="Price")
    available: int = Field(description="Available tickets")
    sold: int = Field(description="Sold tickets")
    quantity: int = Field(description="Total quantity")
    is_sold_out: bool = Field(description="Is sold out")
    is_on_sale: bool = Field(description="Is currently on sale")
    can_purchase: bool = Field(description="Can purchase right now")
    message: Optional[str] = Field(default=None, description="Status message")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "tier_id": 1,
                "tier_name": "General Admission",
                "price": 49.99,
                "available": 400,
                "sold": 500,
                "quantity": 1000,
                "is_sold_out": False,
                "is_on_sale": True,
                "can_purchase": True
            }
        }


class TicketResponse(BaseModel):
    """Individual ticket response schema."""

    id: int = Field(description="Ticket ID")
    uuid: str = Field(description="Ticket UUID")
    ticket_code: str = Field(description="Unique ticket code")
    status: str = Field(description="Ticket status (valid, used, cancelled, refunded)")
    event_id: int = Field(description="Event ID")
    order_id: int = Field(description="Order ID")
    tier_name: Optional[str] = Field(default=None, description="Ticket tier name")
    attendee_first_name: Optional[str] = Field(default=None, description="Attendee first name")
    attendee_last_name: Optional[str] = Field(default=None, description="Attendee last name")
    attendee_email: Optional[str] = Field(default=None, description="Attendee email")
    checked_in_at: Optional[datetime] = Field(default=None, description="Check-in timestamp")
    transferred_at: Optional[datetime] = Field(default=None, description="Transfer timestamp")
    cancelled_at: Optional[datetime] = Field(default=None, description="Cancellation timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class TicketDetailResponse(BaseModel):
    """Detailed ticket response with QR code."""

    id: int = Field(description="Ticket ID")
    uuid: str = Field(description="Ticket UUID")
    ticket_code: str = Field(description="Ticket code")
    qr_code: Optional[str] = Field(default=None, description="QR code (base64 encoded)")
    status: str = Field(description="Ticket status")
    event_id: int = Field(description="Event ID")
    order_id: int = Field(description="Order ID")
    event: "EventTicketInfo" = Field(description="Event information")
    attendee_first_name: Optional[str] = Field(default=None, description="Attendee first name")
    attendee_last_name: Optional[str] = Field(default=None, description="Attendee last name")
    attendee_email: Optional[str] = Field(default=None, description="Attendee email")
    checked_in_at: Optional[datetime] = Field(default=None, description="Check-in time")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class EventTicketInfo(BaseModel):
    """Event information for ticket response."""

    id: int = Field(description="Event ID")
    title: str = Field(description="Event title")
    start_time: datetime = Field(description="Start time")
    end_time: datetime = Field(description="End time")
    venue_name: str = Field(description="Venue name")
    venue_city: Optional[str] = Field(default=None, description="Venue city")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SetAttendeeRequest(BaseModel):
    """Set attendee information request."""

    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="Attendee first name"
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="Attendee last name"
    )
    email: str = Field(description="Attendee email")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            }
        }


class TransferTicketRequest(BaseModel):
    """Transfer ticket request schema."""

    recipient_email: str = Field(description="Email of recipient")
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional transfer message"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "recipient_email": "friend@example.com",
                "message": "Enjoy the show!"
            }
        }


class ValidateTicketRequest(BaseModel):
    """Validate ticket request (check-in)."""

    ticket_code: str = Field(description="Ticket code to validate")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "ticket_code": "TK-2025-001-000001"
            }
        }


class ValidateTicketResponse(BaseModel):
    """Validate ticket response."""

    valid: bool = Field(description="Is ticket valid")
    message: str = Field(description="Validation message")
    ticket: Optional[TicketResponse] = Field(default=None, description="Ticket details if valid")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "valid": True,
                "message": "Ticket is valid and ready for check-in",
                "ticket": {
                    "id": 1,
                    "ticket_code": "TK-2025-001-000001",
                    "status": "valid"
                }
            }
        }


# Update forward references
TicketDetailResponse.model_rebuild()
