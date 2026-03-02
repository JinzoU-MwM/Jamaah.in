# Super Admin Dashboard Design

> **Created:** 2026-03-02
> **Author:** Brainstorming session
> **Status:** Design Approved

## Overview

A full-featured super admin dashboard for the Jamaah.in app owner to:
- Manage all users (activate/deactivate, subscriptions, delete)
- Handle customer support tickets
- View system analytics with charts
- Access all user data

**Note:** Super admin is the app owner (configured via `SUPER_ADMIN_EMAIL`), separate from regular admin users.

---

## Architecture

### Super Admin Authentication

**Database Changes:**
- Add `is_super_admin: Boolean` column to `users` table
- Super admin identified by email from `SUPER_ADMIN_EMAIL` environment variable

**Backend Dependencies:**
```python
# app/auth.py
async def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """Require current user to be super admin."""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user
```

**Backend Files:**
```
backend/app/
├── models/
│   ├── user.py          # Add is_super_admin column
│   └── support_ticket.py # New: SupportTicket, TicketMessage
├── auth.py              # Add require_super_admin()
├── routers/
│   └── super_admin_router.py  # New: Super admin endpoints
```

### Super Admin vs Regular Admin

| Feature | Regular Admin | Super Admin |
|---------|--------------|--------------|
| View users | ✅ | ✅ |
| Activate/deactivate users | ✅ | ✅ |
| Manage subscriptions | ✅ | ✅ |
| Delete users | ✅ | ✅ |
| View support tickets | ✅ | ✅ |
| Manage other admins | ❌ | ✅ |
| Access all data | ❌ | ✅ |

---

## Support Tickets System

### Data Model

```python
class SupportTicket(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(255))
    status = Column(Enum("OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"))
    priority = Column(Enum("LOW", "MEDIUM", "HIGH", "URGENT"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    sender = Column(Enum("USER", "ADMIN"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    ticket = relationship("SupportTicket", back_populates="messages")
```

### API Endpoints

**Super Admin Endpoints (`/super-admin/*`):**
```
GET    /super-admin/stats               - Dashboard stats
GET    /super-admin/tickets             - List all tickets
GET    /super-admin/tickets/{id}        - Get ticket detail
POST   /super-admin/tickets/{id}/reply  - Admin reply
PATCH  /super-admin/tickets/{id}/status - Update status
DELETE /super-admin/tickets/{id}        - Delete ticket
```

**User Endpoints (`/tickets/*`):**
```
POST   /tickets             - Create new ticket
GET    /tickets             - List user's tickets
GET    /tickets/{id}        - Get ticket detail
POST   /tickets/{id}/reply  - User reply
```

---

## Frontend Dashboard

### File Structure

```
frontend-svelte/src/
├── lib/
│   ├── pages/
│   │   └── SuperAdminDashboard.svelte      # Main dashboard
│   └── components/
│       └── super-admin/
│           ├── StatsCards.svelte           # Overview cards
│           ├── Charts.svelte              # Analytics charts
│           ├── UserManagement.svelte       # User table + actions
│           ├── TicketList.svelte          # Tickets table
│           ├── TicketDetail.svelte         # Chat interface
│           └── UserDetailModal.svelte    # User edit modal
│   └── services/
│       └── superAdminApi.js             # API client
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  JAMAAH.IN - SUPER ADMIN                    [Logout]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 1,234   │  │   156    │  │  Rp 2.5M │  │   45     │ │
│  │  Users   │  │  Active  │  │ Revenue  │  │ Tickets  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │         User Activity Chart (30 days)              │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Revenue Growth (Monthly)                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

[ Tabs: Users | Tickets ]
```

### Tabs
- **Users Tab:** Search, filter, pagination, activate/deactivate, delete
- **Tickets Tab:** All tickets, status filter, priority badges
- **Ticket Detail:** Chat-style interface with admin reply box

---

## Database Migration

**Alembic Migration:**
```python
# alembic/versions/xxxxx_add_super_admin_and_support_tickets.py

def upgrade():
    # Add is_super_admin to users
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Create support_tickets table
    op.create_table('support_tickets', ...)

    # Create ticket_messages table
    op.create_table('ticket_messages', ...)
```

---

## API Response Schemas

```python
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
```

---

## Environment Variables

```env
# .env
SUPER_ADMIN_EMAIL=your-email@example.com
```

---

## Rate Limiting

- Ticket creation: 5 tickets per hour per user
- Admin replies: No limit

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** Svelte 5, Vite, TailwindCSS
- **Charts:** Chart.js or Recharts
- **Testing:** pytest
