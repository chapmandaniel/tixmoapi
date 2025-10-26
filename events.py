"""
Event model for ticket listings.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid as uuid_lib

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.promoters import Promoter
    from src.models.ticket_tiers import TicketTier
    from src.models.orders import Order
    from src.models.tickets import Ticket
    from src.models.waitlist import Waitlist


class EventStatus(str, enum.Enum):
    """Event status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):
    """Event model for ticket sales listings."""

    __tablename__ = "events"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4
    )

    # Foreign Key to Promoter
    promoter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promoters.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Basic Information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Venue Information
    venue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    venue_address: Mapped[str | None] = mapped_column(String(500))
    venue_city: Mapped[str | None] = mapped_column(String(100), index=True)
    venue_state: Mapped[str | None] = mapped_column(String(100))
    venue_country: Mapped[str] = mapped_column(String(2), default="US")
    venue_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    venue_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))

    # Date and Time
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    doors_open_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Status and Configuration
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, native_enum=False), default=EventStatus.DRAFT, nullable=False, index=True
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    age_restriction: Mapped[int | None] = mapped_column(Integer)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)

    # Media
    featured_image_url: Mapped[str | None] = mapped_column(String(500))
    banner_image_url: Mapped[str | None] = mapped_column(String(500))

    # Categorization
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    category: Mapped[str | None] = mapped_column(String(50), index=True)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    # Publication and Cancellation
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Relationships
    promoter: Mapped["Promoter"] = relationship("Promoter", back_populates="events")
    ticket_tiers: Mapped[list["TicketTier"]] = relationship(
        "TicketTier", back_populates="event", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="event")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="event")
    waitlist_entries: Mapped[list["Waitlist"]] = relationship(
        "Waitlist", back_populates="event", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="check_dates"),
        CheckConstraint(
            "doors_open_time IS NULL OR doors_open_time <= start_time", 
            name="check_doors_open"
        ),
        CheckConstraint("capacity > 0", name="check_capacity"),
        CheckConstraint("age_restriction IS NULL OR age_restriction >= 0", name="check_age"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_published(self) -> bool:
        """Check if event is published."""
        return self.status == EventStatus.PUBLISHED and self.published_at is not None

    @property
    def is_cancelled(self) -> bool:
        """Check if event is cancelled."""
        return self.status == EventStatus.CANCELLED

    @property
    def is_upcoming(self) -> bool:
        """Check if event is in the future."""
        return self.start_time > datetime.now(self.start_time.tzinfo)

    @property
    def is_past(self) -> bool:
        """Check if event has ended."""
        return self.end_time < datetime.now(self.end_time.tzinfo)

    @property
    def is_deleted(self) -> bool:
        """Check if event is soft-deleted."""
        return self.deleted_at is not None

    @property
    def location_string(self) -> str:
        """Get formatted location string."""
        parts = [self.venue_city, self.venue_state, self.venue_country]
        return ", ".join(filter(None, parts))
