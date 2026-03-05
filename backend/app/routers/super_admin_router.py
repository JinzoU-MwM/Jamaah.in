"""
Super Admin Router — /super-admin/*
Provides super admin-only endpoints for managing the entire application.
Super admin is the app owner, separate from regular admins.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_super_admin
from app.models.user import User, Subscription, UsageLog, PlanType, SubscriptionStatus
from app.models.support_ticket import SupportTicket, TicketMessage, TicketStatus, TicketPriority, SenderType
from app.services.ai_result_cache_repo import get_ai_cache_stats, purge_expired_ai_cache

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


# --- Schemas ---

class SuperAdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    pro_users: int
    free_users: int
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    total_revenue: int


class TicketListItem(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_name: str
    subject: str
    status: str
    priority: str
    created_at: str
    last_message_at: str
    message_count: int
    is_read: bool
    unread_user_messages: int


class TicketMessageResponse(BaseModel):
    id: int
    sender_type: str
    content: str
    created_at: str


class TicketDetailResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_name: str
    subject: str
    status: str
    priority: str
    created_at: str
    messages: List[TicketMessageResponse]


class TicketReplyRequest(BaseModel):
    content: str


class TicketStatusRequest(BaseModel):
    status: str  # "open", "in_progress", "resolved", "closed"


class UnreadCountResponse(BaseModel):
    unread_tickets: int
    unread_messages: int


class AICacheStatsResponse(BaseModel):
    total: int
    active: int
    expired: int


class AICachePurgeResponse(BaseModel):
    deleted: int
    before: AICacheStatsResponse
    after: AICacheStatsResponse


# --- Endpoints ---

@router.get("/stats", response_model=SuperAdminStatsResponse)
async def super_admin_stats(
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Get super admin dashboard statistics."""
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    pro = db.query(Subscription).filter(Subscription.plan == PlanType.PRO).count()
    free = total - pro

    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.OPEN).count()
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.RESOLVED).count()

    # Calculate revenue from payments
    from app.models.user import Payment, PaymentStatus
    revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.PAID
    ).scalar() or 0

    return SuperAdminStatsResponse(
        total_users=total,
        active_users=active,
        pro_users=pro,
        free_users=free,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        total_revenue=revenue,
    )


@router.get("/tickets", response_model=List[TicketListItem])
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """List all support tickets with filters."""
    query = db.query(SupportTicket)

    if status:
        try:
            status_enum = TicketStatus(status)
            query = query.filter(SupportTicket.status == status_enum)
        except ValueError:
            pass

    if priority:
        try:
            priority_enum = TicketPriority(priority)
            query = query.filter(SupportTicket.priority == priority_enum)
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

        unread_user_messages = db.query(func.count(TicketMessage.id)).filter(
            TicketMessage.ticket_id == ticket.id,
            TicketMessage.sender_type == SenderType.USER,
            TicketMessage.is_read == False
        ).scalar() or 0

        items.append(TicketListItem(
            id=ticket.id,
            user_id=ticket.user_id,
            user_email=ticket.user.email,
            user_name=ticket.user.name,
            subject=ticket.subject,
            status=ticket.status.value,
            priority=ticket.priority.value,
            created_at=ticket.created_at.isoformat(),
            last_message_at=last_message.created_at.isoformat() if last_message else ticket.created_at.isoformat(),
            message_count=message_count,
            is_read=(unread_user_messages == 0),
            unread_user_messages=unread_user_messages,
        ))

    return items


@router.get("/tickets/unread-count", response_model=UnreadCountResponse)
async def get_unread_ticket_count(
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Get unread counts for admin (user messages not yet opened by admin)."""
    unread_messages = db.query(func.count(TicketMessage.id)).filter(
        TicketMessage.sender_type == SenderType.USER,
        TicketMessage.is_read == False
    ).scalar() or 0

    unread_tickets = db.query(func.count(func.distinct(TicketMessage.ticket_id))).filter(
        TicketMessage.sender_type == SenderType.USER,
        TicketMessage.is_read == False
    ).scalar() or 0

    return UnreadCountResponse(
        unread_tickets=unread_tickets,
        unread_messages=unread_messages,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket_detail(
    ticket_id: int,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Get ticket detail with all messages."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    # Mark admin messages as read
    db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id,
        TicketMessage.sender_type == "user",
        TicketMessage.is_read == False
    ).update({"is_read": True})
    db.commit()

    messages = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.created_at.asc()).all()

    return TicketDetailResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=ticket.user.email,
        user_name=ticket.user.name,
        subject=ticket.subject,
        status=ticket.status.value,
        priority=ticket.priority.value,
        created_at=ticket.created_at.isoformat(),
        messages=[
            TicketMessageResponse(
                id=msg.id,
                sender_type=msg.sender_type.value,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ],
    )


@router.post("/tickets/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: int,
    req: TicketReplyRequest,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Admin reply to a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    message = TicketMessage(
        ticket_id=ticket_id,
        sender_type="admin",
        content=req.content,
        is_read=False,
    )
    db.add(message)

    # Update ticket status to in_progress if it was open
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()

    db.commit()
    return {"success": True, "message_id": message.id}


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    req: TicketStatusRequest,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Update ticket status."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    try:
        ticket.status = TicketStatus(req.status)
        ticket.updated_at = datetime.utcnow()
        db.commit()
        return {"success": True, "status": ticket.status.value}
    except ValueError:
        raise HTTPException(status_code=400, detail="Status tidak valid")


@router.delete("/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Delete a support ticket and all its messages."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket tidak ditemukan")

    db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id).delete()
    db.query(SupportTicket).filter(SupportTicket.id == ticket_id).delete()
    db.commit()
    return {"success": True, "deleted_ticket_id": ticket_id}


@router.get("/ai-cache/stats", response_model=AICacheStatsResponse)
async def ai_cache_stats(
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Get persistent AI cache statistics."""
    del admin
    stats = get_ai_cache_stats(db)
    return AICacheStatsResponse(**stats)


@router.post("/ai-cache/purge-expired", response_model=AICachePurgeResponse)
async def purge_expired_ai_cache_endpoint(
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Purge expired persistent AI cache rows."""
    del admin
    before = get_ai_cache_stats(db)
    deleted = purge_expired_ai_cache(db)
    after = get_ai_cache_stats(db)
    return AICachePurgeResponse(
        deleted=deleted,
        before=AICacheStatsResponse(**before),
        after=AICacheStatsResponse(**after),
    )
