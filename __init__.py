"""
Models package initialization.

Imports all models to ensure they're registered with SQLAlchemy.
This is critical for:
- Alembic migration detection
- Relationship resolution
- Table creation
"""

from src.models.audit_log import AuditLog
from src.models.email_notifications import EmailNotification
from src.models.events import Event, EventStatus
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus
from src.models.payment_transactions import PaymentTransaction
from src.models.promoters import Promoter
from src.models.ticket_tiers import TicketTier
from src.models.tickets import Ticket, TicketStatus
from src.models.users import User, UserRole
from src.models.waitlist import Waitlist

# Export all models
__all__ = [
    # User and Promoter
    "User",
    "UserRole",
    "Promoter",
    # Events
    "Event",
    "EventStatus",
    "TicketTier",
    # Orders
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    # Tickets
    "Ticket",
    "TicketStatus",
    # Waitlist
    "Waitlist",
    # Payments
    "PaymentTransaction",
    # Notifications
    "EmailNotification",
    # Audit
    "AuditLog",
]
