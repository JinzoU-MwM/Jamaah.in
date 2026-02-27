"""
Team / Organization router — Multi-User Teams (Pro Feature)
CRUD for organizations, team member management, invitations.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.team import (
    Organization, TeamMember, TeamInvite,
    TeamRole, MemberStatus,
)
from app.models.group import Group

router = APIRouter(prefix="/team", tags=["Team"])


# ---- Schemas ----

class CreateOrgRequest(BaseModel):
    name: str

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "viewer"  # owner | admin | viewer

class UpdateRoleRequest(BaseModel):
    role: str


# ---- Helpers ----

def get_user_org(db: Session, user_id: int):
    """Get the organization the user belongs to (if any)."""
    membership = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.status == MemberStatus.ACTIVE
    ).first()
    if not membership:
        return None, None
    org = db.query(Organization).filter(Organization.id == membership.org_id).first()
    return org, membership


def require_role(membership: TeamMember, min_role: str):
    """Check minimum role: owner > admin > viewer."""
    role_hierarchy = {"owner": 3, "admin": 2, "viewer": 1}
    if not membership or role_hierarchy.get(membership.role, 0) < role_hierarchy.get(min_role, 0):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


# ---- Endpoints ----

@router.post("/create")
async def create_organization(
    req: CreateOrgRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new organization. The creator becomes the owner."""
    # Check user doesn't already have an org
    existing_org, _ = get_user_org(db, current_user.id)
    if existing_org:
        raise HTTPException(400, "Anda sudah memiliki organisasi")

    org = Organization(name=req.name.strip(), created_by=current_user.id)
    db.add(org)
    db.flush()

    # Add creator as owner
    member = TeamMember(
        org_id=org.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
        status=MemberStatus.ACTIVE,
    )
    db.add(member)

    # Migrate existing personal groups to org
    personal_groups = db.query(Group).filter(
        Group.user_id == current_user.id,
        Group.org_id == None
    ).all()
    for g in personal_groups:
        g.org_id = org.id

    db.commit()
    db.refresh(org)

    return {
        "id": org.id,
        "name": org.name,
        "member_count": 1,
        "role": "owner",
    }


@router.get("/")
async def get_team(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's organization and team members."""
    org, membership = get_user_org(db, current_user.id)
    if not org:
        return {"organization": None, "members": [], "invites": []}

    members = db.query(TeamMember).filter(
        TeamMember.org_id == org.id,
        TeamMember.status == MemberStatus.ACTIVE,
    ).all()

    invites = []
    if membership.role in ("owner", "admin"):
        invites = db.query(TeamInvite).filter(
            TeamInvite.org_id == org.id,
            TeamInvite.status == "pending",
        ).all()

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "created_at": org.created_at.isoformat() if org.created_at else None,
        },
        "my_role": membership.role,
        "members": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "name": m.user.name if m.user else "Unknown",
                "email": m.user.email if m.user else "",
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            }
            for m in members
        ],
        "invites": [
            {
                "id": inv.id,
                "email": inv.email,
                "role": inv.role,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            }
            for inv in invites
        ],
    }


@router.post("/invite")
async def invite_member(
    req: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invite a user by email to join the organization."""
    org, membership = get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(404, "Anda belum memiliki organisasi")
    require_role(membership, "admin")

    if req.role not in ("admin", "viewer"):
        raise HTTPException(400, "Role harus 'admin' atau 'viewer'")

    # Check if already a member
    target_user = db.query(User).filter(User.email == req.email).first()
    if target_user:
        existing = db.query(TeamMember).filter(
            TeamMember.org_id == org.id,
            TeamMember.user_id == target_user.id,
            TeamMember.status == MemberStatus.ACTIVE,
        ).first()
        if existing:
            raise HTTPException(400, "User sudah menjadi anggota tim")

    # Check existing pending invite
    existing_invite = db.query(TeamInvite).filter(
        TeamInvite.org_id == org.id,
        TeamInvite.email == req.email,
        TeamInvite.status == "pending",
    ).first()
    if existing_invite:
        raise HTTPException(400, "Undangan sudah dikirim ke email ini")

    invite = TeamInvite(
        org_id=org.id,
        email=req.email,
        role=req.role,
        invited_by=current_user.id,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return {
        "id": invite.id,
        "email": invite.email,
        "role": invite.role,
        "token": invite.token,
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
    }


@router.post("/join/{token}")
async def join_organization(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept an invitation and join an organization."""
    invite = db.query(TeamInvite).filter(
        TeamInvite.token == token,
        TeamInvite.status == "pending",
    ).first()
    if not invite:
        raise HTTPException(404, "Undangan tidak ditemukan atau sudah kadaluarsa")

    if invite.email != current_user.email:
        raise HTTPException(403, "Undangan ini bukan untuk akun Anda")

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        db.commit()
        raise HTTPException(400, "Undangan sudah kadaluarsa")

    # Check if user already in an org
    existing_org, _ = get_user_org(db, current_user.id)
    if existing_org:
        raise HTTPException(400, "Anda sudah menjadi anggota organisasi lain")

    # Add as team member
    member = TeamMember(
        org_id=invite.org_id,
        user_id=current_user.id,
        role=invite.role,
        status=MemberStatus.ACTIVE,
        invited_by=invite.invited_by,
    )
    db.add(member)

    # Migrate user's personal groups to the org
    personal_groups = db.query(Group).filter(
        Group.user_id == current_user.id,
        Group.org_id == None
    ).all()
    for g in personal_groups:
        g.org_id = invite.org_id

    invite.status = "accepted"
    db.commit()

    org = db.query(Organization).filter(Organization.id == invite.org_id).first()
    return {
        "message": f"Berhasil bergabung ke {org.name}",
        "organization": org.name,
        "role": invite.role,
    }


@router.patch("/members/{member_id}")
async def update_member_role(
    member_id: int,
    req: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change a member's role (owner/admin only)."""
    org, membership = get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(404, "Organisasi tidak ditemukan")
    require_role(membership, "owner")

    target = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.org_id == org.id,
    ).first()
    if not target:
        raise HTTPException(404, "Anggota tidak ditemukan")

    if target.user_id == current_user.id:
        raise HTTPException(400, "Tidak bisa mengubah role sendiri")

    if req.role not in ("admin", "viewer"):
        raise HTTPException(400, "Role harus 'admin' atau 'viewer'")

    target.role = req.role
    db.commit()

    return {"id": target.id, "role": target.role}


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from the organization (owner/admin only)."""
    org, membership = get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(404, "Organisasi tidak ditemukan")
    require_role(membership, "admin")

    target = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.org_id == org.id,
    ).first()
    if not target:
        raise HTTPException(404, "Anggota tidak ditemukan")

    if target.role == "owner":
        raise HTTPException(400, "Tidak bisa menghapus owner")

    if target.user_id == current_user.id:
        raise HTTPException(400, "Tidak bisa menghapus diri sendiri")

    target.status = MemberStatus.REMOVED
    db.commit()

    return {"message": "Anggota berhasil dihapus"}


@router.delete("/invites/{invite_id}")
async def cancel_invite(
    invite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending invitation."""
    org, membership = get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(404, "Organisasi tidak ditemukan")
    require_role(membership, "admin")

    invite = db.query(TeamInvite).filter(
        TeamInvite.id == invite_id,
        TeamInvite.org_id == org.id,
        TeamInvite.status == "pending",
    ).first()
    if not invite:
        raise HTTPException(404, "Undangan tidak ditemukan")

    db.delete(invite)
    db.commit()

    return {"message": "Undangan dibatalkan"}
