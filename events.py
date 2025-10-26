"""
Event API endpoints.

Provides routes for:
- POST /events - Create new event (promoters only)
- GET /events - List events with filters
- GET /events/{event_id} - Get event details
- PUT /events/{event_id} - Update event (owner/admin only)
- DELETE /events/{event_id} - Delete event (owner/admin only)
- POST /events/{event_id}/publish - Publish event (owner/admin only)
- POST /events/{event_id}/cancel - Cancel event (owner/admin only)
- POST /events/{event_id}/complete - Mark event as completed (owner/admin only)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user, get_current_promoter_user
from src.models.users import User
from src.models.events import EventStatus
from src.schemas.events import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailResponse,
    PublishEventRequest,
    CancelEventRequest,
    EventListResponse,
)
from src.schemas.common import (
    SuccessResponse,
    MessageResponse,
    PagedResponse,
)
from src.services.event_service import EventService

# Create router with prefix and tags
router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Event does not exist"},
    }
)


# ============================================================================
# Event CRUD Endpoints
# ============================================================================

@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new event",
    description="Create a new event. Requires promoter role. Events start in draft status."
)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Create a new event.
    
    **Required role:** Promoter or Admin
    
    **Process:**
    1. Validates promoter is verified
    2. Creates event in DRAFT status
    3. Returns created event
    
    **Next steps:**
    - Add ticket tiers
    - Configure event details
    - Publish event when ready
    """
    service = EventService(db)
    
    # Get promoter_id from current user
    if not current_user.promoter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must have a promoter account to create events"
        )
    
    event = await service.create_event(
        event_data=event_data,
        promoter_id=current_user.promoter.id
    )
    
    return EventResponse.model_validate(event)


@router.get(
    "",
    response_model=PagedResponse[EventListResponse],
    summary="List events",
    description="Get a paginated list of events with optional filters"
)
async def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    status_filter: Optional[EventStatus] = Query(None, description="Filter by status"),
    promoter_id: Optional[int] = Query(None, description="Filter by promoter ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title, description, venue"),
    include_past: bool = Query(False, description="Include past events"),
    db: AsyncSession = Depends(get_db)
) -> PagedResponse[EventListResponse]:
    """
    List events with filters and pagination.
    
    **Public endpoint** - No authentication required
    
    **Filters:**
    - status: Filter by event status (draft, published, cancelled, completed)
    - promoter_id: Show events from specific promoter
    - category: Filter by category (music, sports, etc.)
    - is_featured: Show only featured events
    - search: Search in title, description, and venue
    - include_past: Include events that have already ended
    
    **Pagination:**
    - skip: Offset for pagination
    - limit: Maximum results per page (max 100)
    
    **Returns:**
    - Paginated list of events
    - Total count
    - Page information
    """
    service = EventService(db)
    
    events, total = await service.list_events(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        promoter_id=promoter_id,
        category=category,
        is_featured=is_featured,
        search=search,
        include_past=include_past,
    )
    
    # Convert to response models
    event_responses = [EventListResponse.model_validate(e) for e in events]
    
    return PagedResponse(
        items=event_responses,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit if total > 0 else 0
    )


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Get event details",
    description="Get detailed information about a specific event"
)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
) -> EventDetailResponse:
    """
    Get detailed event information.
    
    **Public endpoint** - No authentication required
    
    **Returns:**
    - Complete event details
    - Promoter information
    - Ticket tier information
    - Availability status
    
    **Note:** View count is incremented on each request
    """
    service = EventService(db)
    
    event = await service.get_event(event_id)
    
    # Increment view count (async, don't await)
    await service.increment_view_count(event_id)
    
    return EventDetailResponse.model_validate(event)


@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update event",
    description="Update event details. Only event owner or admin can update."
)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Update an event.
    
    **Required role:** Event owner (promoter) or Admin
    
    **Restrictions:**
    - Published events: Can only update description and images
    - Cancelled events: Can only update description and images
    - Draft events: Can update all fields
    
    **Note:** Some fields cannot be updated after publishing to protect ticket buyers
    """
    service = EventService(db)
    
    event = await service.update_event(
        event_id=event_id,
        event_data=event_data,
        user_id=current_user.id
    )
    
    return EventResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    summary="Delete event",
    description="Delete an event. Only event owner or admin can delete."
)
async def delete_event(
    event_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (cannot be undone)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete an event (soft delete by default).
    
    **Required role:** Event owner (promoter) or Admin
    
    **Soft Delete (default):**
    - Event status set to CANCELLED
    - Event marked with deletion timestamp
    - Event hidden from public listings
    - Data preserved for historical records
    
    **Hard Delete:**
    - Permanently removes event from database
    - Cannot be undone
    - Only allowed if no tickets sold
    
    **Note:** Events with sold tickets cannot be deleted, only cancelled
    """
    service = EventService(db)
    
    await service.delete_event(
        event_id=event_id,
        user_id=current_user.id,
        hard_delete=hard_delete
    )
    
    delete_type = "permanently deleted" if hard_delete else "cancelled and archived"
    
    return MessageResponse(
        message=f"Event successfully {delete_type}",
        success=True
    )


# ============================================================================
# Event Status Management
# ============================================================================

@router.post(
    "/{event_id}/publish",
    response_model=EventResponse,
    summary="Publish event",
    description="Publish a draft event to make it publicly visible and available for ticket sales"
)
async def publish_event(
    event_id: int,
    publish_data: PublishEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Publish an event.
    
    **Required role:** Event owner (promoter) or Admin
    
    **Prerequisites:**
    - Event must be in DRAFT status
    - Event must have at least one ticket tier
    - All required fields must be complete:
      - Title
      - Description
      - Venue name
      - Start time
      - End time
    
    **What happens:**
    - Event status changes to PUBLISHED
    - Event becomes visible in public listings
    - Tickets become available for purchase
    - Optional: Event can be marked as featured
    
    **Note:** Once published, some event details cannot be changed
    """
    service = EventService(db)
    
    event = await service.publish_event(
        event_id=event_id,
        user_id=current_user.id,
        publish_data=publish_data
    )
    
    return EventResponse.model_validate(event)


@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    summary="Cancel event",
    description="Cancel an event and optionally refund all attendees"
)
async def cancel_event(
    event_id: int,
    cancel_data: CancelEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Cancel an event.
    
    **Required role:** Event owner (promoter) or Admin
    
    **What happens:**
    - Event status changes to CANCELLED
    - Event removed from public listings
    - Cancellation reason stored
    - Optional: All attendees can be refunded
    
    **Refund process:**
    - If refund_attendees=true, all tickets are refunded
    - Refunds processed through original payment method
    - Attendees notified via email
    
    **Note:** Cannot cancel already completed events
    """
    service = EventService(db)
    
    event = await service.cancel_event(
        event_id=event_id,
        user_id=current_user.id,
        cancel_data=cancel_data
    )
    
    return EventResponse.model_validate(event)


@router.post(
    "/{event_id}/complete",
    response_model=EventResponse,
    summary="Mark event as completed",
    description="Mark an event as completed after it has ended"
)
async def complete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Mark an event as completed.
    
    **Required role:** Event owner (promoter) or Admin
    
    **Prerequisites:**
    - Event end time must have passed
    - Event cannot already be completed
    
    **What happens:**
    - Event status changes to COMPLETED
    - Event archived in listings
    - Useful for analytics and reporting
    
    **Note:** This is typically done automatically, but can be manually triggered
    """
    service = EventService(db)
    
    event = await service.mark_completed(
        event_id=event_id,
        user_id=current_user.id
    )
    
    return EventResponse.model_validate(event)


# ============================================================================
# Promoter-Specific Endpoints
# ============================================================================

@router.get(
    "/my/events",
    response_model=PagedResponse[EventListResponse],
    summary="Get my events",
    description="Get all events created by the current promoter"
)
async def get_my_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[EventStatus] = Query(None),
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
) -> PagedResponse[EventListResponse]:
    """
    Get all events created by current promoter.
    
    **Required role:** Promoter or Admin
    
    **Returns:**
    - All events owned by the promoter
    - Includes drafts, published, cancelled, and completed events
    - Paginated results
    
    **Filters:**
    - status: Filter by event status
    """
    service = EventService(db)
    
    if not current_user.promoter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must have a promoter account"
        )
    
    events, total = await service.list_events(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        promoter_id=current_user.promoter.id,
        include_past=True,  # Include all events for promoter
    )
    
    event_responses = [EventListResponse.model_validate(e) for e in events]
    
    return PagedResponse(
        items=event_responses,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit if total > 0 else 0
    )
