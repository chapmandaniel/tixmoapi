"""
Audit Log model for security and compliance tracking.
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
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.users import User


class AuditLog(Base):
    """Audit log model for tracking critical system actions."""

    __tablename__ = "audit_log"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key to User (optional - some actions may be system-initiated)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Action Information
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Change Tracking
    old_data: Mapped[dict | None] = mapped_column(JSONB)
    new_data: Mapped[dict | None] = mapped_column(JSONB)

    # Request Information
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"

    @property
    def is_create(self) -> bool:
        """Check if action is a create."""
        return self.action.lower() in ["create", "insert", "add"]

    @property
    def is_update(self) -> bool:
        """Check if action is an update."""
        return self.action.lower() in ["update", "modify", "edit"]

    @property
    def is_delete(self) -> bool:
        """Check if action is a delete."""
        return self.action.lower() in ["delete", "remove"]

    @property
    def has_changes(self) -> bool:
        """Check if audit log contains change data."""
        return self.old_data is not None or self.new_data is not None
