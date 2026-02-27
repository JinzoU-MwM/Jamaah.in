"""
Analytics Router — Dashboard statistics for agency owners.
Aggregates group, jamaah, equipment, and passport data.
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, and_

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.team import TeamMember, MemberStatus
from sqlalchemy import or_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_user_group_filter(db: Session, user: User):
    """Build filter for groups accessible by the user (own + team)."""
    membership = db.query(TeamMember).filter(
        TeamMember.user_id == user.id,
        TeamMember.status == MemberStatus.ACTIVE,
    ).first()
    org_id = membership.org_id if membership else None

    if org_id:
        return or_(Group.user_id == user.id, Group.org_id == org_id)
    return Group.user_id == user.id


@router.get("/dashboard")
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate dashboard statistics for the current user."""
    group_filter = _get_user_group_filter(db, user)
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # --- Accessible group IDs ---
    group_ids = [
        gid for (gid,) in db.query(Group.id).filter(group_filter).all()
    ]

    if not group_ids:
        return {
            "total_groups": 0,
            "total_jamaah": 0,
            "groups_this_month": 0,
            "jamaah_this_month": 0,
            "gender_breakdown": {"male": 0, "female": 0, "unknown": 0},
            "equipment_rate": 0,
            "passport_expiring_soon": 0,
            "recent_groups": [],
            "monthly_trend": [],
        }

    # Total counts
    total_groups = len(group_ids)
    total_jamaah = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id.in_(group_ids)
    ).scalar() or 0

    # This month
    groups_this_month = db.query(func.count(Group.id)).filter(
        group_filter,
        Group.created_at >= month_start,
    ).scalar() or 0

    jamaah_this_month = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id.in_(group_ids),
        GroupMember.created_at >= month_start,
    ).scalar() or 0

    # Gender breakdown (from title)
    gender_data = db.query(
        case(
            (GroupMember.title.in_(["Mr", "Tuan", "mr", "tuan"]), "male"),
            (GroupMember.title.in_(["Mrs", "Ms", "Nyonya", "Nona", "mrs", "ms", "nyonya", "nona"]), "female"),
            else_="unknown",
        ).label("gender"),
        func.count(GroupMember.id),
    ).filter(
        GroupMember.group_id.in_(group_ids)
    ).group_by("gender").all()

    gender_breakdown = {"male": 0, "female": 0, "unknown": 0}
    for gender, count in gender_data:
        gender_breakdown[gender] = count

    # Equipment fulfillment rate
    if total_jamaah > 0:
        equipped = db.query(func.count(GroupMember.id)).filter(
            GroupMember.group_id.in_(group_ids),
            GroupMember.is_equipment_received == True,
        ).scalar() or 0
        equipment_rate = round((equipped / total_jamaah) * 100)
    else:
        equipment_rate = 0

    # Passport expiring within 90 days
    cutoff_date = (now + timedelta(days=90)).strftime("%Y-%m-%d")
    today_str = now.strftime("%Y-%m-%d")
    passport_expiring = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id.in_(group_ids),
        GroupMember.tanggal_paspor != "",
        GroupMember.tanggal_paspor != None,
        GroupMember.tanggal_paspor <= cutoff_date,
        GroupMember.tanggal_paspor >= today_str,
    ).scalar() or 0

    # Recent groups (last 5)
    recent = db.query(
        Group.id, Group.name, Group.created_at,
        func.count(GroupMember.id).label("member_count"),
    ).outerjoin(GroupMember, Group.id == GroupMember.group_id).filter(
        group_filter,
    ).group_by(Group.id, Group.name, Group.created_at).order_by(
        Group.updated_at.desc()
    ).limit(5).all()

    recent_groups = [
        {
            "id": g.id,
            "name": g.name,
            "member_count": g.member_count,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in recent
    ]

    # Monthly trend (last 6 months)
    six_months_ago = (now - timedelta(days=180)).replace(day=1)
    monthly_raw = db.query(
        extract("year", GroupMember.created_at).label("year"),
        extract("month", GroupMember.created_at).label("month"),
        func.count(GroupMember.id).label("count"),
    ).filter(
        GroupMember.group_id.in_(group_ids),
        GroupMember.created_at >= six_months_ago,
    ).group_by("year", "month").order_by("year", "month").all()

    monthly_trend = []
    for row in monthly_raw:
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        monthly_trend.append({
            "label": f"{month_names[int(row.month)]} {int(row.year)}",
            "count": row.count,
        })

    return {
        "total_groups": total_groups,
        "total_jamaah": total_jamaah,
        "groups_this_month": groups_this_month,
        "jamaah_this_month": jamaah_this_month,
        "gender_breakdown": gender_breakdown,
        "equipment_rate": equipment_rate,
        "passport_expiring_soon": passport_expiring,
        "recent_groups": recent_groups,
        "monthly_trend": monthly_trend,
    }
