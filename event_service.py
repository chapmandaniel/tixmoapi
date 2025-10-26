"""
Event Service - Business logic for event management.

Handles:
- Event creation, updates, deletion
- Permission and ownership checks
- Status management (draft, published, cancelled, completed)
- Promoter validation
- Soft delete support
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from src.models.events import Event, EventStatus
from src.models.promoters import Promoter
from src.models.users import User, UserRole
from src.schemas.events import (
    EventCreate,
    EventUpdate,
    PublishEventRequest,
    CancelEventRequest,
)


class EventService:
    """Service for event management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    # ========================================================================
    # Core CRUD Operations
    # ========================================================================

    async def create_event(
        self, 
        event_data: EventCreate, 
        promoter_id: int
    ) -> Event:
        """
        Create a new event.

        Args:
            event_data: Event creation data
            promoter_id: ID of the promoter creating the event

        Returns:
            Created event

        Raises:
            HTTPException: If promoter not found or not verified
        """
        # Verify promoter exists and is verified
        promoter = await self._get_promoter(promoter_id)
        if not promoter.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Promoter account must be verified to create events"
            )

        # Create event instance
        event = Event(
            promoter_id=promoter_id,
            title=event_data.title,
            description=event_data.description,
            venue_name=event_data.venue_name,
            venue_address=event_data.venue_address,
            venue_city=event_data.venue_city,
            venue_state=event_data.venue_state,
            venue_country=event_data.venue_country,
            venue_latitude=event_data.venue_latitude,
            venue_longitude=event_data.venue_longitude,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            doors_open_time=event_data.doors_open_time,
            timezone=event_data.timezone,
            capacity=event_data.capacity,
            age_restriction=event_data.age_restriction,
            is_private=event_data.is_private,
            featured_image_url=event_data.featured_image_url,
            banner_image_url=event_data.banner_image_url,
            category=event_data.category,
            tags=event_data.tags or [],
            status=EventStatus.DRAFT,  # New events start as draft
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        # Load relationships
        await self.db.refresh(event, ["promoter"])

        return event

    async def get_event(
        self, 
        event_id: int, 
        include_deleted: bool = False
    ) -> Event:
        """
        Get event by ID.

        Args:
            event_id: Event ID
            include_deleted: Whether to include soft-deleted events

        Returns:
            Event instance

        Raises:
            HTTPException: If event not found
        """
        query = select(Event).where(Event.id == event_id)
        
        if not include_deleted:
            query = query.where(Event.deleted_at.is_(None))

        # Load relationships
        query = query.options(
            selectinload(Event.promoter).selectinload(Promoter.user),
            selectinload(Event.ticket_tiers)
        )

        result = await self.db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return event

    async def list_events(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[EventStatus] = None,
        promoter_id: Optional[int] = None,
        category: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        include_past: bool = False,
    ) -> tuple[list[Event], int]:
        """
        List events with filters and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Filter by event status
            promoter_id: Filter by promoter
            category: Filter by category
            is_featured: Filter by featured status
            search: Search in title and description
            include_past: Include past events

        Returns:
            Tuple of (events list, total count)
        """
        # Build base query
        query = select(Event).where(Event.deleted_at.is_(None))

        # Apply filters
        if status_filter:
            query = query.where(Event.status == status_filter)

        if promoter_id:
            query = query.where(Event.promoter_id == promoter_id)

        if category:
            query = query.where(Event.category == category)

        if is_featured is not None:
            query = query.where(Event.is_featured == is_featured)

        if not include_past:
            query = query.where(Event.end_time > datetime.now(timezone.utc))

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                    Event.venue_name.ilike(search_term),
                    Event.venue_city.ilike(search_term)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply pagination and ordering
        query = (
            query
            .options(
                selectinload(Event.promoter).selectinload(Promoter.user),
                selectinload(Event.ticket_tiers)
            )
            .order_by(Event.start_time.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        return events, total or 0

    async def update_event(
        self,
        event_id: int,
        event_data: EventUpdate,
        user_id: int,
    ) -> Event:
        """
        Update an event.

        Args:
            event_id: Event ID
            event_data: Update data
            user_id: ID of user making the update

        Returns:
            Updated event

        Raises:
            HTTPException: If unauthorized or event not found
        """
        # Get event and check permissions
        event = await self.get_event(event_id)
        await self._check_event_permission(event, user_id)

        # Cannot update published/cancelled events extensively
        if event.status in [EventStatus.PUBLISHED, EventStatus.CANCELLED]:
            # Only allow limited updates for published/cancelled events
            allowed_fields = {"description", "featured_image_url", "banner_image_url"}
            update_dict = event_data.model_dump(exclude_unset=True)
            if not all(key in allowed_fields for key in update_dict.keys()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot modify core details of {event.status.value} events"
                )

        # Apply updates
        update_dict = event_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(event, field, value)

        event.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(event)
        await self.db.refresh(event, ["promoter", "ticket_tiers"])

        return event

    async def delete_event(
        self,
        event_id: int,
        user_id: int,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete an event (soft delete by default).

        Args:
            event_id: Event ID
            user_id: ID of user deleting the event
            hard_delete: If True, permanently delete

        Raises:
            HTTPException: If unauthorized or event has sold tickets
        """
        event = await self.get_event(event_id)
        await self._check_event_permission(event, user_id)

        # Check if event has sold tickets
        if event.status == EventStatus.PUBLISHED:
            # Check for sold tickets
            from src.models.tickets import Ticket
            ticket_query = select(func.count()).select_from(Ticket).where(
                Ticket.event_id == event_id
            )
            ticket_count = await self.db.scalar(ticket_query)
            
            if ticket_count and ticket_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete event with sold tickets. Cancel the event instead."
                )

        if hard_delete:
            await self.db.delete(event)
        else:
            event.deleted_at = datetime.now(timezone.utc)
            event.status = EventStatus.CANCELLED

        await self.db.commit()

    # ========================================================================
    # Status Management
    # ========================================================================

    async def publish_event(
        self,
        event_id: int,
        user_id: int,
        publish_data: PublishEventRequest,
    ) -> Event:
        """
        Publish an event (make it publicly visible).

        Args:
            event_id: Event ID
            user_id: ID of user publishing
            publish_data: Publication settings

        Returns:
            Published event

        Raises:
            HTTPException: If unauthorized or event not ready for publishing
        """
        event = await self.get_event(event_id)
        await self._check_event_permission(event, user_id)

        # Validate event can be published
        if event.status != EventStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only draft events can be published (current status: {event.status.value})"
            )

        # Ensure event has at least one ticket tier
        if not event.ticket_tiers or len(event.ticket_tiers) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event must have at least one ticket tier before publishing"
            )

        # Validate event details are complete
        required_fields = {
            "title": event.title,
            "description": event.description,
            "venue_name": event.venue_name,
            "start_time": event.start_time,
            "end_time": event.end_time,
        }
        
        missing_fields = [
            field for field, value in required_fields.items() 
            if not value
        ]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Publish the event
        event.status = EventStatus.PUBLISHED
        event.is_featured = publish_data.is_featured
        event.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(event)
        await self.db.refresh(event, ["promoter", "ticket_tiers"])

        return event

    async def cancel_event(
        self,
        event_id: int,
        user_id: int,
        cancel_data: CancelEventRequest,
    ) -> Event:
        """
        Cancel an event.

        Args:
            event_id: Event ID
            user_id: ID of user cancelling
            cancel_data: Cancellation details

        Returns:
            Cancelled event

        Raises:
            HTTPException: If unauthorized
        """
        event = await self.get_event(event_id)
        await self._check_event_permission(event, user_id)

        if event.status == EventStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is already cancelled"
            )

        if event.status == EventStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed events"
            )

        # Update event status
        event.status = EventStatus.CANCELLED
        event.cancellation_reason = cancel_data.reason
        event.cancelled_at = datetime.now(timezone.utc)
        event.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(event)

        # TODO: Handle refunds if cancel_data.refund_attendees is True
        # This will be implemented in the payment service

        return event

    async def mark_completed(
        self,
        event_id: int,
        user_id: int,
    ) -> Event:
        """
        Mark an event as completed.

        Args:
            event_id: Event ID
            user_id: ID of user marking complete

        Returns:
            Completed event

        Raises:
            HTTPException: If unauthorized or event not past
        """
        event = await self.get_event(event_id)
        await self._check_event_permission(event, user_id)

        if event.status == EventStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is already marked as completed"
            )

        if event.end_time > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark event as completed before end time"
            )

        event.status = EventStatus.COMPLETED
        event.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(event)

        return event

    # ========================================================================
    # Permission and Validation Helpers
    # ========================================================================

    async def _get_promoter(self, promoter_id: int) -> Promoter:
        """Get promoter by ID."""
        query = select(Promoter).where(Promoter.id == promoter_id)
        result = await self.db.execute(query)
        promoter = result.scalar_one_or_none()

        if not promoter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promoter not found"
            )

        return promoter

    async def _check_event_permission(
        self, 
        event: Event, 
        user_id: int
    ) -> None:
        """
        Check if user has permission to modify event.

        Args:
            event: Event to check
            user_id: User ID to check

        Raises:
            HTTPException: If user lacks permission
        """
        # Get user
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Admins can modify any event
        if user.role == UserRole.ADMIN:
            return

        # Load promoter relationship if not loaded
        if not event.promoter:
            await self.db.refresh(event, ["promoter"])

        # Check if user owns the event through promoter
        if event.promoter.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this event"
            )

    async def increment_view_count(self, event_id: int) -> None:
        """Increment event view counter."""
        event = await self.get_event(event_id)
        event.view_count += 1
        await self.db.commit()
