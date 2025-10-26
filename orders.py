"""
Order and purchase schemas for ticket buying flow.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrderItemRequest(BaseModel):
    """Order item in purchase request."""

    tier_id: int = Field(
        ge=1,
        description="Ticket tier ID"
    )
    quantity: int = Field(
        ge=1,
        le=1000,
        description="Number of tickets to purchase"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "tier_id": 1,
                "quantity": 2
            }
        }


class CreateOrderRequest(BaseModel):
    """Create order request schema."""

    event_id: int = Field(
        ge=1,
        description="Event ID"
    )
    items: list[OrderItemRequest] = Field(
        min_items=1,
        max_items=100,
        description="Items to purchase"
    )
    billing_email: Optional[EmailStr] = Field(
        default=None,
        description="Billing email (defaults to user email)"
    )
    billing_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Billing name"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "items": [
                    {"tier_id": 1, "quantity": 2},
                    {"tier_id": 2, "quantity": 1}
                ],
                "billing_email": "john@example.com",
                "billing_name": "John Doe"
            }
        }


class BillingAddress(BaseModel):
    """Billing address schema."""

    street: str = Field(max_length=255, description="Street address")
    city: str = Field(max_length=100, description="City")
    state: str = Field(max_length=100, description="State/Province")
    postal_code: str = Field(max_length=20, description="Postal code")
    country: str = Field(min_length=2, max_length=2, description="Country code")


class CreateOrderWithBillingRequest(BaseModel):
    """Create order with full billing information."""

    event_id: int = Field(ge=1, description="Event ID")
    items: list[OrderItemRequest] = Field(min_items=1, description="Items to purchase")
    billing_email: EmailStr = Field(description="Billing email")
    billing_name: str = Field(max_length=255, description="Billing name")
    billing_address: Optional[BillingAddress] = Field(
        default=None,
        description="Billing address"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "event_id": 1,
                "items": [{"tier_id": 1, "quantity": 2}],
                "billing_email": "john@example.com",
                "billing_name": "John Doe",
                "billing_address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "US"
                }
            }
        }


class OrderItemResponse(BaseModel):
    """Order item in response."""

    id: int = Field(description="Order item ID")
    tier_id: int = Field(description="Tier ID")
    tier_name: str = Field(description="Tier name")
    quantity: int = Field(description="Quantity")
    unit_price: float = Field(description="Price per ticket")
    subtotal: float = Field(description="Line item total")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema."""

    id: int = Field(description="Order ID")
    uuid: str = Field(description="Order UUID")
    order_number: str = Field(description="Order number")
    event_id: int = Field(description="Event ID")
    event_title: Optional[str] = Field(default=None, description="Event title")
    status: str = Field(description="Order status")
    payment_status: str = Field(description="Payment status")
    subtotal: float = Field(description="Subtotal before fees/tax")
    service_fee: float = Field(description="Service fee")
    tax: float = Field(description="Tax")
    total_amount: float = Field(description="Total amount")
    currency: str = Field(description="Currency code")
    items: list[OrderItemResponse] = Field(description="Order items")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Order expiration time")
    confirmed_at: Optional[datetime] = Field(default=None, description="Confirmation time")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "order_number": "ORD-2025-001",
                "event_id": 1,
                "status": "pending",
                "payment_status": "pending",
                "subtotal": 99.98,
                "service_fee": 5.00,
                "tax": 8.40,
                "total_amount": 113.38,
                "currency": "USD"
            }
        }


class OrderDetailResponse(BaseModel):
    """Detailed order response."""

    id: int = Field(description="Order ID")
    uuid: str = Field(description="Order UUID")
    order_number: str = Field(description="Order number")
    event_id: int = Field(description="Event ID")
    event: "EventOrderInfo" = Field(description="Event details")
    status: str = Field(description="Order status")
    payment_status: str = Field(description="Payment status")
    subtotal: float = Field(description="Subtotal")
    service_fee: float = Field(description="Service fee")
    tax: float = Field(description="Tax")
    total_amount: float = Field(description="Total amount")
    currency: str = Field(description="Currency")
    items: list[OrderItemResponse] = Field(description="Order items")
    tickets_count: int = Field(description="Total number of tickets")
    billing_email: Optional[str] = Field(default=None, description="Billing email")
    billing_name: Optional[str] = Field(default=None, description="Billing name")
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    payment_intent_id: Optional[str] = Field(default=None, description="Stripe payment intent ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Order expiration")
    confirmed_at: Optional[datetime] = Field(default=None, description="Confirmation time")
    refunded_at: Optional[datetime] = Field(default=None, description="Refund time")
    refund_amount: Optional[float] = Field(default=None, description="Refund amount")
    refund_reason: Optional[str] = Field(default=None, description="Refund reason")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class EventOrderInfo(BaseModel):
    """Event information in order response."""

    id: int = Field(description="Event ID")
    title: str = Field(description="Event title")
    start_time: datetime = Field(description="Start time")
    venue_name: str = Field(description="Venue name")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ConfirmOrderRequest(BaseModel):
    """Confirm order request (after payment)."""

    payment_intent_id: str = Field(description="Stripe payment intent ID")
    payment_method: Optional[str] = Field(
        default=None,
        description="Payment method used"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "payment_intent_id": "pi_3Kj7L9C0Z3Q7X4W2Q7X4",
                "payment_method": "card"
            }
        }


class CancelOrderRequest(BaseModel):
    """Cancel order request schema."""

    reason: str = Field(
        min_length=1,
        max_length=500,
        description="Cancellation reason"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "reason": "I can no longer attend the event"
            }
        }


class RefundOrderRequest(BaseModel):
    """Refund order request schema."""

    reason: str = Field(
        min_length=1,
        max_length=500,
        description="Refund reason"
    )
    refund_amount: Optional[float] = Field(
        default=None,
        description="Amount to refund (defaults to full amount)"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "reason": "Event was cancelled",
                "refund_amount": 113.38
            }
        }


class PaymentIntentResponse(BaseModel):
    """Stripe payment intent response."""

    client_secret: str = Field(description="Stripe client secret for payment")
    payment_intent_id: str = Field(description="Stripe payment intent ID")
    amount: float = Field(description="Amount to charge in cents")
    currency: str = Field(description="Currency code")
    status: str = Field(description="Intent status")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "client_secret": "pi_3Kj7L9C0Z3Q7X4W2Q7X4_secret_abc123",
                "payment_intent_id": "pi_3Kj7L9C0Z3Q7X4W2Q7X4",
                "amount": 11338,
                "currency": "usd",
                "status": "requires_payment_method"
            }
        }


class OrderListResponse(BaseModel):
    """Order list response (minimal)."""

    id: int = Field(description="Order ID")
    order_number: str = Field(description="Order number")
    event_title: str = Field(description="Event title")
    status: str = Field(description="Order status")
    total_amount: float = Field(description="Total amount")
    currency: str = Field(description="Currency")
    tickets_count: int = Field(description="Number of tickets")
    created_at: datetime = Field(description="Creation timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class CreateOrderResponse(BaseModel):
    """Response when creating an order."""

    order: OrderResponse = Field(description="Created order")
    message: str = Field(description="Status message")
    expires_in: int = Field(description="Order expiration time in seconds")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "message": "Order created successfully. Proceed to payment.",
                "expires_in": 900,
                "order": {
                    "id": 1,
                    "order_number": "ORD-2025-001",
                    "status": "pending"
                }
            }
        }


# Update forward references
OrderDetailResponse.model_rebuild()
