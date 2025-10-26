"""
Email Notification model for tracking email delivery.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.users import User


class EmailNotification(Base):
    """Email notification model for tracking email delivery and engagement."""

    __tablename__ = "email_notifications"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key to User (optional - some emails may be to non-users)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Email Information
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)

    # Delivery Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    # Delivery Tracking
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bounced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error Information
    error_message: Mapped[str | None] = mapped_column(Text)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<EmailNotification(id={self.id}, email={self.email}, status={self.status})>"

    @property
    def is_sent(self) -> bool:
        """Check if email was sent."""
        return self.sent_at is not None

    @property
    def is_opened(self) -> bool:
        """Check if email was opened."""
        return self.opened_at is not None

    @property
    def is_clicked(self) -> bool:
        """Check if email links were clicked."""
        return self.clicked_at is not None

    @property
    def is_bounced(self) -> bool:
        """Check if email bounced."""
        return self.bounced_at is not None

    @property
    def is_pending(self) -> bool:
        """Check if email is pending delivery."""
        return self.status == "pending"

    @property
    def is_failed(self) -> bool:
        """Check if email delivery failed."""
        return self.status == "failed" or self.is_bounced
