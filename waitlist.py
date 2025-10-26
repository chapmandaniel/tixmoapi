"""
Waitlist model for sold-out events.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.events import Event
    from src.models.users import User
    from src.models.ticket_tiers import TicketTier


class Waitlist(Base):
    """Waitlist model for managing event waitlists."""

    __tablename__ = "waitlist"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ticket_tiers.id", ondelete="SET NULL"), index=True
    )

    # Position in Waitlist
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Notification Status
    notified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Response
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="waiting")

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="waitlist_entries")
    user: Mapped["User"] = relationship("User", back_populates="waitlist_entries")
    tier: Mapped["TicketTier | None"] = relationship("TicketTier", back_populates="waitlist_entries")

    # Constraints - User can only be on waitlist once per event/tier combination
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", "tier_id", name="uq_waitlist_event_user_tier"),
    )

    def __repr__(self) -> str:
        return f"<Waitlist(id={self.id}, event_id={self.event_id}, position={self.position})>"

    @property
    def is_notified(self) -> bool:
        """Check if user has been notified."""
        return self.notified and self.notified_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if not self.notification_expires_at:
            return False
        return datetime.now(self.notification_expires_at.tzinfo) > self.notification_expires_at

    @property
    def is_waiting(self) -> bool:
        """Check if still waiting (not notified)."""
        return not self.notified and self.status == "waiting"

    @property
    def can_notify(self) -> bool:
        """Check if user can be notified."""
        return self.is_waiting and not self.is_expired
