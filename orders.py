"""
Order and OrderItem models for ticket purchases.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid as uuid_lib

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.users import User
    from src.models.events import Event
    from src.models.ticket_tiers import TicketTier
    from src.models.tickets import Ticket
    from src.models.payment_transactions import PaymentTransaction


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    """Order model for ticket purchases."""

    __tablename__ = "orders"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4
    )

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Order Information
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Status
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.PENDING, nullable=False, index=True
    )

    # Pricing
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    service_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Payment Information
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING, nullable=False, index=True
    )
    payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    payment_method: Mapped[str | None] = mapped_column(String(50))

    # Order Lifecycle
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    refund_reason: Mapped[str | None] = mapped_column(Text)

    # Billing Information
    billing_email: Mapped[str | None] = mapped_column(String(255))
    billing_name: Mapped[str | None] = mapped_column(String(255))
    billing_address: Mapped[dict | None] = mapped_column(JSONB)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    event: Mapped["Event"] = relationship("Event", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="order")
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction", back_populates="order"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="check_subtotal"),
        CheckConstraint("service_fee >= 0", name="check_service_fee"),
        CheckConstraint("tax >= 0", name="check_tax"),
        CheckConstraint("total_amount >= 0", name="check_total_amount"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """Check if order is pending."""
        return self.status == OrderStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        """Check if order is confirmed."""
        return self.status == OrderStatus.CONFIRMED

    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == OrderStatus.CANCELLED

    @property
    def is_refunded(self) -> bool:
        """Check if order is refunded."""
        return self.status == OrderStatus.REFUNDED

    @property
    def is_paid(self) -> bool:
        """Check if payment is completed."""
        return self.payment_status == PaymentStatus.COMPLETED

    @property
    def total_tickets(self) -> int:
        """Get total number of tickets in order."""
        return sum(item.quantity for item in self.order_items)


class OrderItem(Base):
    """Order item model for line items in an order."""

    __tablename__ = "order_items"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ticket_tiers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Item Details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    tier: Mapped["TicketTier"] = relationship("TicketTier", back_populates="order_items")

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity"),
        CheckConstraint("unit_price >= 0", name="check_unit_price"),
        CheckConstraint("subtotal >= 0", name="check_subtotal"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, quantity={self.quantity}, subtotal={self.subtotal})>"
