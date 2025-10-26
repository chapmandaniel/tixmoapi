"""
Ticket management API endpoints.

This module provides REST API endpoints for ticket tier management,
ticket operations, and ticket validation for event check-in.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.database import get_db
from src.core.dependencies import get_current_promoter_user, get_current_user
from src.models.users import User
from src.services.ticket_service import TicketService
from src.schemas.tickets import (
    CreateTicketTierRequest,
    UpdateTicketTierRequest,
    TicketTierResponse,
    TicketTierAvailabilityResponse,
    TicketResponse,
    TicketDetailResponse,
    SetAttendeeRequest,
    TransferTicketRequest,
    ValidateTicketRequest,
    ValidateTicketResponse,
)


router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ============================================================================
# TICKET TIER MANAGEMENT ENDPOINTS (Promoter)
# ============================================================================


@router.post(
    "/events/{event_id}/tiers",
    response_model=TicketTierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket tier",
    description="Create a new ticket tier for an event. Promoter or Admin only."
)
async def create_ticket_tier(
    event_id: int,
    tier_data: CreateTicketTierRequest,
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new ticket tier for an event.
    
    **Permission**: Promoter or Admin only.
    
    **Validations**:
    - Event must exist and belong to promoter
    - Event cannot be completed or cancelled
    - max_purchase >= min_purchase
    - sale_end_time > sale_start_time
    
    **Example**:
    ```json
    {
        "name": "General Admission",
        "description": "Standard entry to the event",
        "price": 49.99,
        "quantity": 1000,
        "min_purchase": 1,
        "max_purchase": 10,
        "sale_start_time": "2025-10-26T00:00:00Z",
        "sale_end_time": "2025-07-14T23:59:59Z"
    }
    ```
    """
    service = TicketService(db)
    tier = await service.create_ticket_tier(
        event_id=event_id,
        tier_data=tier_data,
        promoter_id=current_user.promoter.id
    )
    return TicketTierResponse.model_validate(tier)


@router.get(
    "/events/{event_id}/tiers",
    response_model=List[TicketTierResponse],
    summary="List event tiers",
    description="Get all ticket tiers for an event."
)
async def list_event_tiers(
    event_id: int,
    include_inactive: bool = Query(
        default=False,
        description="Include inactive tiers"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all ticket tiers for an event.
    
    **Permission**: Public (no authentication required).
    
    **Query Parameters**:
    - `include_inactive`: Include inactive tiers (default: false)
    
    **Response**: List of tiers ordered by position.
    """
    service = TicketService(db)
    tiers = await service.get_event_tiers(
        event_id=event_id,
        include_inactive=include_inactive
    )
    return [TicketTierResponse.model_validate(tier) for tier in tiers]


@router.get(
    "/tiers/{tier_id}",
    response_model=TicketTierResponse,
    summary="Get tier details",
    description="Get detailed information about a ticket tier."
)
async def get_tier_details(
    tier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a ticket tier.
    
    **Permission**: Public (no authentication required).
    """
    service = TicketService(db)
    tier = await service.get_tier_by_id(tier_id)
    return TicketTierResponse.model_validate(tier)


@router.get(
    "/tiers/{tier_id}/availability",
    response_model=TicketTierAvailabilityResponse,
    summary="Check tier availability",
    description="Get real-time availability information for a ticket tier."
)
async def check_tier_availability(
    tier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time availability information for a ticket tier.
    
    **Permission**: Public (no authentication required).
    
    **Returns**:
    - Available count
    - Sold count
    - Total quantity
    - Whether on sale
    - Whether sold out
    - Status message
    """
    service = TicketService(db)
    availability = await service.get_tier_availability(tier_id)
    return availability


@router.put(
    "/tiers/{tier_id}",
    response_model=TicketTierResponse,
    summary="Update ticket tier",
    description="Update a ticket tier. Promoter or Admin only."
)
async def update_ticket_tier(
    tier_id: int,
    tier_data: UpdateTicketTierRequest,
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a ticket tier.
    
    **Permission**: Promoter (owner) or Admin only.
    
    **Restrictions after sales**:
    - Cannot change price after tickets sold
    - Cannot reduce quantity below sold count
    - Can update description, images, and other display fields
    
    **Example**:
    ```json
    {
        "quantity": 1500,
        "is_active": true
    }
    ```
    """
    service = TicketService(db)
    tier = await service.update_ticket_tier(
        tier_id=tier_id,
        tier_data=tier_data,
        promoter_id=current_user.promoter.id
    )
    return TicketTierResponse.model_validate(tier)


@router.delete(
    "/tiers/{tier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ticket tier",
    description="Delete a ticket tier. Promoter or Admin only."
)
async def delete_ticket_tier(
    tier_id: int,
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a ticket tier.
    
    **Permission**: Promoter (owner) or Admin only.
    
    **Restrictions**:
    - Cannot delete tiers with sold tickets
    - Set tier to inactive instead if tickets have been sold
    """
    service = TicketService(db)
    await service.delete_ticket_tier(
        tier_id=tier_id,
        promoter_id=current_user.promoter.id
    )
    return None


# ============================================================================
# TICKET OPERATIONS (User)
# ============================================================================


@router.get(
    "/my/tickets",
    response_model=List[TicketDetailResponse],
    summary="Get my tickets",
    description="Get all tickets owned by the current user."
)
async def get_my_tickets(
    include_used: bool = Query(
        default=False,
        description="Include used tickets"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tickets owned by the current user.
    
    **Permission**: Authenticated user only.
    
    **Query Parameters**:
    - `include_used`: Include used/checked-in tickets (default: false)
    
    **Returns**: List of tickets with QR codes, ordered by creation date (newest first).
    """
    service = TicketService(db)
    tickets = await service.get_user_tickets(
        user_id=current_user.id,
        include_used=include_used
    )
    
    # Generate ticket detail responses with QR codes
    ticket_responses = []
    for ticket in tickets:
        # Generate QR code if not already generated
        if not ticket.qr_code:
            ticket.qr_code = await service.generate_ticket_qr_code(str(ticket.uuid))
            await db.commit()
        
        ticket_responses.append(TicketDetailResponse.model_validate(ticket))
    
    return ticket_responses


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Get ticket details",
    description="Get detailed information about a specific ticket."
)
async def get_ticket_details(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific ticket.
    
    **Permission**: Ticket owner or event promoter only.
    
    **Returns**: Complete ticket information including QR code.
    """
    service = TicketService(db)
    ticket = await service.get_ticket_by_id(
        ticket_id=ticket_id,
        user_id=current_user.id
    )
    
    # Generate QR code if not already generated
    if not ticket.qr_code:
        ticket.qr_code = await service.generate_ticket_qr_code(str(ticket.uuid))
        await db.commit()
    
    return TicketDetailResponse.model_validate(ticket)


@router.patch(
    "/{ticket_id}/attendee",
    response_model=TicketResponse,
    summary="Set ticket attendee",
    description="Set or update attendee information for a ticket."
)
async def set_ticket_attendee(
    ticket_id: int,
    attendee_data: SetAttendeeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set or update attendee information for a ticket.
    
    **Permission**: Ticket owner only.
    
    **Restrictions**:
    - Cannot update used tickets
    - Cannot update cancelled or refunded tickets
    
    **Example**:
    ```json
    {
        "attendee_name": "John Doe",
        "attendee_email": "john@example.com",
        "attendee_phone": "+1234567890"
    }
    ```
    """
    service = TicketService(db)
    ticket = await service.set_ticket_attendee(
        ticket_id=ticket_id,
        attendee_data=attendee_data,
        user_id=current_user.id
    )
    return TicketResponse.model_validate(ticket)


@router.post(
    "/{ticket_id}/transfer",
    response_model=TicketResponse,
    summary="Transfer ticket",
    description="Transfer a ticket to another user."
)
async def transfer_ticket(
    ticket_id: int,
    transfer_data: TransferTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Transfer a ticket to another user.
    
    **Permission**: Ticket owner only.
    
    **Requirements**:
    - Ticket must be valid (not used, cancelled, or refunded)
    - Ticket type must allow transfers (requires_approval = false)
    - Recipient must have an account
    
    **Example**:
    ```json
    {
        "recipient_email": "friend@example.com",
        "message": "Enjoy the concert!"
    }
    ```
    """
    service = TicketService(db)
    ticket = await service.transfer_ticket(
        ticket_id=ticket_id,
        transfer_data=transfer_data,
        user_id=current_user.id
    )
    return TicketResponse.model_validate(ticket)


# ============================================================================
# TICKET VALIDATION (Promoter)
# ============================================================================


@router.post(
    "/validate",
    response_model=ValidateTicketResponse,
    summary="Validate ticket",
    description="Validate a ticket for event check-in. Promoter only."
)
async def validate_ticket(
    validation_data: ValidateTicketRequest,
    current_user: User = Depends(get_current_promoter_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a ticket for event check-in.
    
    **Permission**: Promoter (event owner) only.
    
    **Process**:
    1. Scan ticket QR code to get UUID
    2. Send UUID to this endpoint
    3. Receive validation result
    4. If valid, ticket is marked as used
    
    **Validation checks**:
    - Ticket exists
    - Promoter owns the event
    - Ticket status is valid
    - Ticket not already used
    
    **Example**:
    ```json
    {
        "ticket_uuid": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response**:
    ```json
    {
        "valid": true,
        "message": "Ticket validated successfully",
        "ticket_id": 123,
        "attendee_name": "John Doe",
        "tier_name": "VIP",
        "event_title": "Summer Music Festival",
        "checked_in_at": "2025-07-15T18:30:00Z"
    }
    ```
    """
    service = TicketService(db)
    result = await service.validate_ticket(
        validation_data=validation_data,
        promoter_id=current_user.promoter.id
    )
    return result
