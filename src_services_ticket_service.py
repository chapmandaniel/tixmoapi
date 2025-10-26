"""
Ticket management service for handling ticket tiers and individual tickets.

This service provides comprehensive ticket tier management, inventory control,
ticket generation with QR codes, and ticket validation operations.
"""

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import List, Optional
import uuid
import qrcode
from io import BytesIO
import base64

from src.models.events import Event, TicketTier
from src.models.tickets import Ticket
from src.models.users import User
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
    TicketStatus,
)


class TicketService:
    """Service for ticket tier and individual ticket management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize ticket service.

        Args:
            db: Database session for operations
        """
        self.db = db

    async def create_ticket_tier(
        self,
        event_id: int,
        tier_data: CreateTicketTierRequest,
        promoter_id: int
    ) -> TicketTier:
        """
        Create a new ticket tier for an event.

        Args:
            event_id: Event ID
            tier_data: Tier creation data
            promoter_id: Promoter creating the tier

        Returns:
            Created ticket tier

        Raises:
            HTTPException: If event not found or permission denied
        """
        # Verify event exists and belongs to promoter
        event = await self._get_event_with_permission(event_id, promoter_id)

        # Check if event is published (can still add tiers to published events)
        # but not to completed or cancelled events
        if event.status in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add tiers to {event.status} events"
            )

        # Get the highest position for ordering
        result = await self.db.execute(
            select(func.max(TicketTier.position))
            .where(TicketTier.event_id == event_id)
        )
        max_position = result.scalar() or -1

        # Create ticket tier
        tier = TicketTier(
            event_id=event_id,
            name=tier_data.name,
            description=tier_data.description,
            price=tier_data.price,
            quantity=tier_data.quantity,
            sold=0,
            reserved=0,
            min_purchase=tier_data.min_purchase,
            max_purchase=tier_data.max_purchase,
            position=tier_data.position if tier_data.position is not None else max_position + 1,
            sale_start_time=tier_data.sale_start_time,
            sale_end_time=tier_data.sale_end_time,
            is_active=tier_data.is_active,
            requires_approval=tier_data.requires_approval,
        )

        self.db.add(tier)
        await self.db.commit()
        await self.db.refresh(tier)

        return tier

    async def get_event_tiers(
        self,
        event_id: int,
        include_inactive: bool = False
    ) -> List[TicketTier]:
        """
        Get all ticket tiers for an event.

        Args:
            event_id: Event ID
            include_inactive: Whether to include inactive tiers

        Returns:
            List of ticket tiers ordered by position
        """
        query = select(TicketTier).where(
            TicketTier.event_id == event_id
        )

        if not include_inactive:
            query = query.where(TicketTier.is_active == True)

        query = query.order_by(TicketTier.position)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_tier_by_id(self, tier_id: int) -> TicketTier:
        """
        Get ticket tier by ID.

        Args:
            tier_id: Tier ID

        Returns:
            Ticket tier

        Raises:
            HTTPException: If tier not found
        """
        result = await self.db.execute(
            select(TicketTier).where(TicketTier.id == tier_id)
        )
        tier = result.scalar_one_or_none()

        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket tier not found"
            )

        return tier

    async def update_ticket_tier(
        self,
        tier_id: int,
        tier_data: UpdateTicketTierRequest,
        promoter_id: int
    ) -> TicketTier:
        """
        Update a ticket tier.

        Args:
            tier_id: Tier ID
            tier_data: Update data
            promoter_id: Promoter making the update

        Returns:
            Updated ticket tier

        Raises:
            HTTPException: If tier not found or permission denied
        """
        # Get tier with event
        result = await self.db.execute(
            select(TicketTier)
            .options(selectinload(TicketTier.event))
            .where(TicketTier.id == tier_id)
        )
        tier = result.scalar_one_or_none()

        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket tier not found"
            )

        # Check permission
        await self._check_event_permission(tier.event, promoter_id)

        # Check if tickets have been sold
        if tier.sold > 0:
            # Restrict what can be updated after sales
            if tier_data.price is not None and tier_data.price != tier.price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change price after tickets have been sold"
                )
            
            if tier_data.quantity is not None and tier_data.quantity < tier.sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reduce quantity below sold count ({tier.sold})"
                )

        # Update fields
        update_data = tier_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tier, field, value)

        tier.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(tier)

        return tier

    async def delete_ticket_tier(
        self,
        tier_id: int,
        promoter_id: int
    ) -> None:
        """
        Delete a ticket tier.

        Args:
            tier_id: Tier ID
            promoter_id: Promoter deleting the tier

        Raises:
            HTTPException: If tier not found, permission denied, or has sold tickets
        """
        # Get tier with event
        result = await self.db.execute(
            select(TicketTier)
            .options(selectinload(TicketTier.event))
            .where(TicketTier.id == tier_id)
        )
        tier = result.scalar_one_or_none()

        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket tier not found"
            )

        # Check permission
        await self._check_event_permission(tier.event, promoter_id)

        # Cannot delete if tickets have been sold
        if tier.sold > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete tier with sold tickets. Set to inactive instead."
            )

        await self.db.delete(tier)
        await self.db.commit()

    async def get_tier_availability(
        self,
        tier_id: int
    ) -> TicketTierAvailabilityResponse:
        """
        Get real-time availability for a ticket tier.

        Args:
            tier_id: Tier ID

        Returns:
            Availability information

        Raises:
            HTTPException: If tier not found
        """
        tier = await self.get_tier_by_id(tier_id)

        # Calculate availability
        available = tier.quantity - tier.sold - tier.reserved
        is_sold_out = available <= 0

        # Check if currently on sale
        now = datetime.now(timezone.utc)
        is_on_sale = tier.is_active

        if tier.sale_start_time and now < tier.sale_start_time:
            is_on_sale = False
        if tier.sale_end_time and now > tier.sale_end_time:
            is_on_sale = False

        # Determine if can purchase
        can_purchase = is_on_sale and not is_sold_out

        # Generate message
        message = None
        if is_sold_out:
            message = "Sold out"
        elif not tier.is_active:
            message = "Not available for sale"
        elif tier.sale_start_time and now < tier.sale_start_time:
            message = f"Sales start {tier.sale_start_time.strftime('%B %d, %Y at %I:%M %p')}"
        elif tier.sale_end_time and now > tier.sale_end_time:
            message = "Sales have ended"

        return TicketTierAvailabilityResponse(
            tier_id=tier.id,
            tier_name=tier.name,
            price=tier.price,
            available=available,
            sold=tier.sold,
            quantity=tier.quantity,
            is_sold_out=is_sold_out,
            is_on_sale=is_on_sale,
            can_purchase=can_purchase,
            message=message
        )

    async def generate_ticket_qr_code(self, ticket_uuid: str) -> str:
        """
        Generate QR code for a ticket.

        Args:
            ticket_uuid: Ticket UUID

        Returns:
            Base64 encoded QR code image
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(ticket_uuid)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    async def get_ticket_by_id(
        self,
        ticket_id: int,
        user_id: int
    ) -> Ticket:
        """
        Get ticket by ID with permission check.

        Args:
            ticket_id: Ticket ID
            user_id: User requesting the ticket

        Returns:
            Ticket

        Raises:
            HTTPException: If ticket not found or permission denied
        """
        result = await self.db.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.tier).selectinload(TicketTier.event),
                selectinload(Ticket.order).selectinload(Ticket.order.user)
            )
            .where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Check permission - ticket owner or event promoter
        if ticket.order.user_id != user_id:
            # Check if user is the promoter
            event = ticket.tier.event
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.promoter))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.promoter or user.promoter.id != event.promoter_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this ticket"
                )

        return ticket

    async def get_user_tickets(
        self,
        user_id: int,
        include_used: bool = False
    ) -> List[Ticket]:
        """
        Get all tickets for a user.

        Args:
            user_id: User ID
            include_used: Whether to include used tickets

        Returns:
            List of tickets
        """
        query = (
            select(Ticket)
            .join(Ticket.order)
            .options(
                selectinload(Ticket.tier).selectinload(TicketTier.event),
                selectinload(Ticket.order)
            )
            .where(Ticket.order.has(user_id=user_id))
        )

        if not include_used:
            query = query.where(Ticket.status == TicketStatus.VALID)

        query = query.order_by(Ticket.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def set_ticket_attendee(
        self,
        ticket_id: int,
        attendee_data: SetAttendeeRequest,
        user_id: int
    ) -> Ticket:
        """
        Set attendee information for a ticket.

        Args:
            ticket_id: Ticket ID
            attendee_data: Attendee information
            user_id: User making the request

        Returns:
            Updated ticket

        Raises:
            HTTPException: If ticket not found or already used
        """
        ticket = await self.get_ticket_by_id(ticket_id, user_id)

        if ticket.status == TicketStatus.USED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update attendee info for used tickets"
            )

        if ticket.status in [TicketStatus.CANCELLED, TicketStatus.REFUNDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update attendee info for {ticket.status} tickets"
            )

        # Update attendee information
        ticket.attendee_name = attendee_data.attendee_name
        ticket.attendee_email = attendee_data.attendee_email
        ticket.attendee_phone = attendee_data.attendee_phone
        ticket.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def transfer_ticket(
        self,
        ticket_id: int,
        transfer_data: TransferTicketRequest,
        user_id: int
    ) -> Ticket:
        """
        Transfer ticket to another user.

        Args:
            ticket_id: Ticket ID
            transfer_data: Transfer information
            user_id: Current ticket owner

        Returns:
            Ticket after transfer

        Raises:
            HTTPException: If ticket cannot be transferred
        """
        ticket = await self.get_ticket_by_id(ticket_id, user_id)

        # Check if ticket can be transferred
        if ticket.status != TicketStatus.VALID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transfer {ticket.status} tickets"
            )

        # Check if event allows transfers (based on tier settings)
        if ticket.tier.requires_approval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This ticket type cannot be transferred"
            )

        # Find recipient user by email
        result = await self.db.execute(
            select(User).where(User.email == transfer_data.recipient_email)
        )
        recipient = result.scalar_one_or_none()

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient user not found. They must create an account first."
            )

        # Update ticket with new owner info in attendee fields
        ticket.attendee_name = recipient.name
        ticket.attendee_email = recipient.email
        ticket.updated_at = datetime.now(timezone.utc)

        # Note: In a real system, you might want to change the order ownership
        # or create a transfer record. For now, we'll just update attendee info.

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def validate_ticket(
        self,
        validation_data: ValidateTicketRequest,
        promoter_id: int
    ) -> ValidateTicketResponse:
        """
        Validate a ticket for check-in.

        Args:
            validation_data: Validation request
            promoter_id: Promoter performing validation

        Returns:
            Validation result

        Raises:
            HTTPException: If permission denied
        """
        # Find ticket by UUID
        result = await self.db.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.tier).selectinload(TicketTier.event),
                selectinload(Ticket.order)
            )
            .where(Ticket.uuid == validation_data.ticket_uuid)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            return ValidateTicketResponse(
                valid=False,
                message="Ticket not found",
                ticket_id=None,
                attendee_name=None,
                tier_name=None,
                event_title=None,
                checked_in_at=None
            )

        # Check if promoter owns the event
        event = ticket.tier.event
        if event.promoter_id != promoter_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to validate tickets for this event"
            )

        # Check ticket status
        if ticket.status == TicketStatus.USED:
            return ValidateTicketResponse(
                valid=False,
                message=f"Ticket already used on {ticket.checked_in_at.strftime('%B %d, %Y at %I:%M %p')}",
                ticket_id=ticket.id,
                attendee_name=ticket.attendee_name,
                tier_name=ticket.tier.name,
                event_title=event.title,
                checked_in_at=ticket.checked_in_at
            )

        if ticket.status in [TicketStatus.CANCELLED, TicketStatus.REFUNDED]:
            return ValidateTicketResponse(
                valid=False,
                message=f"Ticket has been {ticket.status}",
                ticket_id=ticket.id,
                attendee_name=ticket.attendee_name,
                tier_name=ticket.tier.name,
                event_title=event.title,
                checked_in_at=None
            )

        # Mark ticket as used
        ticket.status = TicketStatus.USED
        ticket.checked_in_at = datetime.now(timezone.utc)
        ticket.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(ticket)

        return ValidateTicketResponse(
            valid=True,
            message="Ticket validated successfully",
            ticket_id=ticket.id,
            attendee_name=ticket.attendee_name or "Not specified",
            tier_name=ticket.tier.name,
            event_title=event.title,
            checked_in_at=ticket.checked_in_at
        )

    async def _get_event_with_permission(
        self,
        event_id: int,
        promoter_id: int
    ) -> Event:
        """
        Get event and verify promoter permission.

        Args:
            event_id: Event ID
            promoter_id: Promoter ID

        Returns:
            Event

        Raises:
            HTTPException: If event not found or permission denied
        """
        result = await self.db.execute(
            select(Event).where(
                and_(
                    Event.id == event_id,
                    Event.deleted_at.is_(None)
                )
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        if event.promoter_id != promoter_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage this event"
            )

        return event

    async def _check_event_permission(
        self,
        event: Event,
        promoter_id: int
    ) -> None:
        """
        Check if promoter has permission for event.

        Args:
            event: Event to check
            promoter_id: Promoter ID

        Raises:
            HTTPException: If permission denied
        """
        if event.promoter_id != promoter_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage this event"
            )
