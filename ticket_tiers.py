"""
Ticket Tier model for different pricing levels.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
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
    from src.models.events import Event
    from src.models.order_items import OrderItem
    from src.models.tickets import Ticket
    from src.models.waitlist import Waitlist


class TicketTier(Base):
    """Ticket tier model for different pricing levels within an event."""

    __tablename__ = "ticket_tiers"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4
    )

    # Foreign Key to Event
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tier Information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Pricing
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Inventory
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Purchase Limits
    min_purchase: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_purchase: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Display Order
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Sale Period
    sale_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sale_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)

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
    event: Mapped["Event"] = relationship("Event", back_populates="ticket_tiers")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="tier")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="tier")
    waitlist_entries: Mapped[list["Waitlist"]] = relationship("Waitlist", back_populates="tier")

    # Constraints
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price"),
        CheckConstraint("quantity > 0", name="check_quantity"),
        CheckConstraint("sold >= 0", name="check_sold"),
        CheckConstraint("reserved >= 0", name="check_reserved"),
        CheckConstraint("sold + reserved <= quantity", name="check_quantity_valid"),
        CheckConstraint("min_purchase > 0", name="check_min_purchase"),
        CheckConstraint("max_purchase > 0", name="check_max_purchase"),
        CheckConstraint("max_purchase >= min_purchase", name="check_min_max_purchase"),
        CheckConstraint(
            "sale_end_time IS NULL OR sale_end_time > sale_start_time",
            name="check_sale_dates"
        ),
    )

    def __repr__(self) -> str:
        return f"<TicketTier(id={self.id}, name={self.name}, price={self.price})>"

    @property
    def available(self) -> int:
        """Get number of tickets available for purchase."""
        return self.quantity - self.sold - self.reserved

    @property
    def is_sold_out(self) -> bool:
        """Check if tier is sold out."""
        return self.available <= 0

    @property
    def is_on_sale(self) -> bool:
        """Check if tier is currently on sale."""
        if not self.is_active:
            return False

        now = datetime.now(datetime.now().astimezone().tzinfo)

        # Check sale start time
        if self.sale_start_time and now < self.sale_start_time:
            return False

        # Check sale end time
        if self.sale_end_time and now > self.sale_end_time:
            return False

        return True

    @property
    def percent_sold(self) -> float:
        """Get percentage of tickets sold."""
        if self.quantity == 0:
            return 0.0
        return (self.sold / self.quantity) * 100

    def can_purchase(self, quantity: int) -> tuple[bool, str | None]:
        """
        Check if a quantity of tickets can be purchased.
        
        Returns:
            Tuple of (can_purchase, error_message)
        """
        if not self.is_active:
            return False, "This ticket tier is not active"

        if not self.is_on_sale:
            return False, "This ticket tier is not currently on sale"

        if quantity < self.min_purchase:
            return False, f"Minimum purchase is {self.min_purchase} tickets"

        if quantity > self.max_purchase:
            return False, f"Maximum purchase is {self.max_purchase} tickets"

        if quantity > self.available:
            return False, f"Only {self.available} tickets available"

        return True, None
