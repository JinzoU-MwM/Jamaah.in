"""
Notification Router — /notifications
Generates on-the-fly notifications by scanning user data for actionable alerts.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate notifications on-the-fly by scanning:
    - Passport expiry within 90 days
    - Subscription expiring within 7 days
    - Groups with incomplete critical data
    - Empty groups
    """
    notifications = []
    now = datetime.utcnow()

    # Get user's groups (own + org)
    from app.models.team import TeamMember
    group_ids = set()
    own_groups = db.query(Group).filter(Group.user_id == user.id).all()
    for g in own_groups:
        group_ids.add(g.id)

    # Org groups
    if hasattr(user, 'id'):
        team_memberships = db.query(TeamMember).filter(TeamMember.user_id == user.id).all()
        for tm in team_memberships:
            org_groups = db.query(Group).filter(Group.org_id == tm.org_id).all()
            for g in org_groups:
                group_ids.add(g.id)

    all_groups = db.query(Group).filter(Group.id.in_(group_ids)).all() if group_ids else []

    # 1. PASSPORT EXPIRY ALERTS
    # Check members whose passport date + 5 years is within 90 days
    for group in all_groups:
        members = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
        for m in members:
            if not m.tanggal_paspor:
                continue
            try:
                passport_date = datetime.strptime(m.tanggal_paspor, "%Y-%m-%d")
                expiry_date = passport_date + timedelta(days=5*365)
                days_until = (expiry_date - now).days

                if days_until <= 0:
                    notifications.append({
                        "type": "passport_expired",
                        "severity": "error",
                        "title": "Paspor Kedaluwarsa",
                        "message": f"{m.nama} — paspor sudah expired ({m.tanggal_paspor})",
                        "group_id": group.id,
                        "group_name": group.name,
                    })
                elif days_until <= 30:
                    notifications.append({
                        "type": "passport_expiring",
                        "severity": "warning",
                        "title": "Paspor Segera Habis",
                        "message": f"{m.nama} — {days_until} hari lagi ({group.name})",
                        "group_id": group.id,
                        "group_name": group.name,
                    })
                elif days_until <= 90:
                    notifications.append({
                        "type": "passport_expiring",
                        "severity": "info",
                        "title": "Paspor Akan Habis",
                        "message": f"{m.nama} — {days_until} hari lagi ({group.name})",
                        "group_id": group.id,
                        "group_name": group.name,
                    })
            except (ValueError, TypeError):
                continue

    # 2. SUBSCRIPTION EXPIRY
    sub = user.subscription
    if sub and sub.expires_at:
        days_left = (sub.expires_at - now).days
        if 0 < days_left <= 7:
            notifications.append({
                "type": "subscription_expiring",
                "severity": "warning",
                "title": "Langganan Segera Habis",
                "message": f"Langganan Pro berakhir dalam {days_left} hari",
                "group_id": None,
                "group_name": None,
            })
        elif days_left <= 0 and sub.plan == "pro":
            notifications.append({
                "type": "subscription_expired",
                "severity": "error",
                "title": "Langganan Habis",
                "message": "Langganan Pro telah berakhir. Perpanjang untuk terus menggunakan fitur Pro.",
                "group_id": None,
                "group_name": None,
            })

    # 3. INCOMPLETE DATA
    critical_fields = ["nama", "no_paspor", "tanggal_lahir", "no_hp"]
    for group in all_groups:
        members = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
        incomplete_count = 0
        for m in members:
            for field in critical_fields:
                if not getattr(m, field, None):
                    incomplete_count += 1
                    break
        if incomplete_count > 0:
            notifications.append({
                "type": "incomplete_data",
                "severity": "info",
                "title": "Data Belum Lengkap",
                "message": f"{incomplete_count} jamaah di \"{group.name}\" belum melengkapi data penting",
                "group_id": group.id,
                "group_name": group.name,
            })

    # 4. EMPTY GROUPS
    for group in all_groups:
        if group.member_count == 0:
            notifications.append({
                "type": "empty_group",
                "severity": "info",
                "title": "Grup Kosong",
                "message": f"\"{group.name}\" belum memiliki data jamaah",
                "group_id": group.id,
                "group_name": group.name,
            })

    # Sort: errors first, then warnings, then info
    severity_order = {"error": 0, "warning": 1, "info": 2}
    notifications.sort(key=lambda n: severity_order.get(n["severity"], 3))

    return {"notifications": notifications, "count": len(notifications)}
