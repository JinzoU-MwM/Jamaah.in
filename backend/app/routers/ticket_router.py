"""
Ticket Router — /tickets/*
User-facing endpoints for creating and managing support tickets.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.support_ticket import SupportTicket, TicketMessage, TicketStatus, TicketPriority, SenderType

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])


# --- Schemas ---

class CreateTicketRequest(BaseModel):
    subject: str
    message: str
    priority: Optional[str] = "medium"


class UserTicketListItem(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    message_count: int
    last_message_preview: str


class TicketMessageResponse(BaseModel):
    id: int
    sender_type: str
    content: str
    is_read: bool
    created_at: str


class UserTicketDetailResponse(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    messages: List[TicketMessageResponse]


class TicketReplyRequest(BaseModel):
    content: str


# --- Endpoints ---

@router.post("")
async def create_ticket(
    req: CreateTicketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new support ticket."""
    # Rate limiting: 5 tickets per hour (simple check)
    recent_tickets = db.query(SupportTicket).filter(
        SupportTicket.user_id == user.id,
        SupportTicket.created_at > datetime.utcnow() - timedelta(hours=1)
    ).count()

    if recent_tickets >= 5:
        raise HTTPException(
            status_code=429,
            detail="Batas pembuatan tiket tercapai. Silakan tunggu 1 jam."
        )

    # Validate priority
    try:
        priority_enum = TicketPriority(req.priority)
    except ValueError:
        priority_enum = TicketPriority.MEDIUM

    # Create ticket
    ticket = SupportTicket(
        user_id=user.id,
        subject=req.subject,
        priority=priority_enum,
    )
    db.add(ticket)
    db.flush()  # get ticket.id

    # Create initial message
    message = TicketMessage(
        ticket_id=ticket.id,
        sender_type=SenderType.USER,
        content=req.message,
        is_read=False,
    )
    db.add(message)
    db.commit()

    return {"success": True, "ticket_id": ticket.id}


@router.get("", response_model=List[UserTicketListItem])
async def list_my_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's tickets."""
    query = db.query(SupportTicket).filter(SupportTicket.user_id == user.id)

    if status:
        try:
            status_enum = TicketStatus(status)
            query = query.filter(SupportTicket.status == status_enum)
        except ValueError:
            pass

    tickets = query.order_by(SupportTicket.updated_at.desc()).offset(skip).limit(limit).all()

    items = []
    for ticket in tickets:
        message_count = db.query(func.count(TicketMessage.id)).filter(
            TicketMessage.ticket_id == ticket.id
        ).scalar() or 0

        last_message = db.query(TicketMessage).filter(
            TicketMessage.ticket_id == ticket.id
        ).order_by(TicketMessage.created_at.desc()).first()

        items.append(UserTicketListItem(
            id=ticket.id,
            subject=ticket.subject,
            status=ticket.status.value,
            priority=ticket.priority.value,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat(),
            message_count=message_count,
            last_message_preview=last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else ""),
        ))

    return items


@router.get("/{ticket_id}", response_model=UserTicketDetailResponse)
async def get_ticket_detail(
    ticket_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ticket detail with all messages."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == user.id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    # Mark admin messages as read
    db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id,
        TicketMessage.sender_type == SenderType.ADMIN,
        TicketMessage.is_read == False
    ).update({"is_read": True})
    db.commit()

    messages = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.created_at.asc()).all()

    return UserTicketDetailResponse(
        id=ticket.id,
        subject=ticket.subject,
        status=ticket.status.value,
        priority=ticket.priority.value,
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat(),
        messages=[
            TicketMessageResponse(
                id=msg.id,
                sender_type=msg.sender_type.value,
                content=msg.content,
                is_read=msg.is_read,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ],
    )


@router.post("/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: int,
    req: TicketReplyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User reply to their own ticket."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == user.id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    message = TicketMessage(
        ticket_id=ticket_id,
        sender_type=SenderType.USER,
        content=req.content,
        is_read=False,
    )
    db.add(message)

    # Update ticket timestamp and status if closed
    ticket.updated_at = datetime.utcnow()
    if ticket.status == TicketStatus.CLOSED or ticket.status == TicketStatus.RESOLVED:
        ticket.status = TicketStatus.IN_PROGRESS

    db.commit()
    return {"success": True, "message_id": message.id}
