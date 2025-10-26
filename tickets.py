"""
Ticket model for individual tickets.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid as uuid_lib

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.orders import Order
    from src.models.ticket_tiers import TicketTier
    from src.models.events import Event
    from src.models.users import User


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""

    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Ticket(Base):
    """Ticket model for individual tickets with QR codes and validation."""

    __tablename__ = "tickets"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4
    )

    # Foreign Keys
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ticket_tiers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Ticket Information
    ticket_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    qr_code: Mapped[str | None] = mapped_column(Text)  # Base64 encoded QR code image

    # Status
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, native_enum=False), default=TicketStatus.VALID, nullable=False, index=True
    )

    # Attendee Information
    attendee_first_name: Mapped[str | None] = mapped_column(String(100))
    attendee_last_name: Mapped[str | None] = mapped_column(String(100))
    attendee_email: Mapped[str | None] = mapped_column(String(255))

    # Check-in
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_in_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )

    # Transfer
    transferred_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    transferred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Cancellation
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
    order: Mapped["Order"] = relationship("Order", back_populates="tickets")
    tier: Mapped["TicketTier"] = relationship("TicketTier", back_populates="tickets")
    event: Mapped["Event"] = relationship("Event", back_populates="tickets")
    user: Mapped["User"] = relationship("User", back_populates="tickets", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, code={self.ticket_code}, status={self.status})>"

    @property
    def is_valid(self) -> bool:
        """Check if ticket is valid for use."""
        return self.status == TicketStatus.VALID

    @property
    def is_used(self) -> bool:
        """Check if ticket has been used (checked in)."""
        return self.status == TicketStatus.USED or self.checked_in_at is not None

    @property
    def is_cancelled(self) -> bool:
        """Check if ticket is cancelled."""
        return self.status == TicketStatus.CANCELLED

    @property
    def is_refunded(self) -> bool:
        """Check if ticket is refunded."""
        return self.status == TicketStatus.REFUNDED

    @property
    def attendee_name(self) -> str | None:
        """Get full attendee name."""
        if self.attendee_first_name and self.attendee_last_name:
            return f"{self.attendee_first_name} {self.attendee_last_name}"
        return None

    @property
    def can_transfer(self) -> bool:
        """Check if ticket can be transferred."""
        # Can transfer if valid and event hasn't started
        if not self.is_valid:
            return False
        if self.is_used:
            return False
        # Check if event hasn't started (would need event relationship)
        return True

    @property
    def can_check_in(self) -> bool:
        """Check if ticket can be checked in."""
        return self.is_valid and not self.is_used
