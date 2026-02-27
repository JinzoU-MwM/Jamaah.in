"""
Document Router — /documents/*
Generates printable HTML documents for groups (rooming list, group manifest).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_user_from_token_or_header(token: str = Query(None), user: User = Depends(get_current_user)):
    """Allow auth via query param (for new-tab links) or header."""
    return user


def get_user_group(group_id: int, user: User, db: Session) -> Group:
    """Fetch group and verify ownership/team access."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")

    # Check access: owner or same org
    if group.user_id != user.id:
        if not (group.org_id and hasattr(user, 'groups')):
            from app.models.team import TeamMember
            team = db.query(TeamMember).filter(
                TeamMember.user_id == user.id,
                TeamMember.org_id == group.org_id,
            ).first()
            if not team:
                raise HTTPException(status_code=403, detail="Akses ditolak")
    return group


# Shared HTML boilerplate
def html_page(title: str, body: str, subtitle: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1e293b; padding: 24px; background: #fff; }}
  .header {{ text-align: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #10b981; }}
  .header h1 {{ font-size: 20px; color: #1e293b; margin-bottom: 4px; }}
  .header p {{ font-size: 13px; color: #64748b; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px; }}
  th {{ background: #f1f5f9; color: #475569; padding: 8px 10px; text-align: left; font-weight: 600; border: 1px solid #e2e8f0; white-space: nowrap; }}
  td {{ padding: 6px 10px; border: 1px solid #e2e8f0; vertical-align: top; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .section-title {{ font-size: 15px; font-weight: 700; color: #10b981; margin: 20px 0 10px; padding-bottom: 4px; border-bottom: 1px solid #d1fae5; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
  .badge-blue {{ background: #dbeafe; color: #1d4ed8; }}
  .badge-green {{ background: #d1fae5; color: #047857; }}
  .footer {{ text-align: center; margin-top: 24px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }}
  @media print {{
    body {{ padding: 12px; }}
    .no-print {{ display: none !important; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
<button class="no-print" onclick="window.print()" style="position:fixed;top:12px;right:12px;padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:600;z-index:99;">
  🖨️ Cetak / Print
</button>
{body}
<div class="footer">Dicetak dari Jamaah.in</div>
</body>
</html>"""


@router.get("/{group_id}/rooming-list", response_class=HTMLResponse)
async def rooming_list(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate printable rooming list for hotel check-in."""
    group = get_user_group(group_id, user, db)
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    # Group by room
    rooms = {}
    unassigned = []
    for m in members:
        if m.room_id:
            if m.room_id not in rooms:
                room_name = m.room.room_number if m.room else f"Room {m.room_id}"
                room_type = m.room.room_type if m.room else ""
                rooms[m.room_id] = {"name": room_name, "type": room_type, "members": []}
            rooms[m.room_id]["members"].append(m)
        else:
            unassigned.append(m)

    body = ""

    # Assigned rooms
    if rooms:
        body += '<div class="section-title">Daftar Kamar</div>'
        for rid, rdata in sorted(rooms.items()):
            body += f'<table><thead><tr>'
            body += f'<th colspan="4">🏨 {rdata["name"]} <span class="badge badge-blue">{rdata["type"]}</span> — {len(rdata["members"])} orang</th>'
            body += '</tr><tr><th>#</th><th>Nama</th><th>No Paspor</th><th>Gender</th></tr></thead><tbody>'
            for i, m in enumerate(rdata["members"], 1):
                g = "L" if m.gender == "male" else "P" if m.gender == "female" else "-"
                body += f'<tr><td>{i}</td><td>{m.nama}</td><td>{m.no_paspor or "-"}</td><td>{g}</td></tr>'
            body += '</tbody></table>'

    # Unassigned
    if unassigned:
        body += f'<div class="section-title">Belum Ditentukan Kamar ({len(unassigned)} orang)</div>'
        body += '<table><thead><tr><th>#</th><th>Nama</th><th>No Paspor</th></tr></thead><tbody>'
        for i, m in enumerate(unassigned, 1):
            body += f'<tr><td>{i}</td><td>{m.nama}</td><td>{m.no_paspor or "-"}</td></tr>'
        body += '</tbody></table>'

    if not members:
        body = '<p style="text-align:center;color:#94a3b8;padding:40px;">Belum ada data jamaah dalam grup ini.</p>'

    return html_page(
        f"Rooming List — {group.name}",
        body,
        f"{len(members)} jamaah · {len(rooms)} kamar",
    )


@router.get("/{group_id}/group-manifest", response_class=HTMLResponse)
async def group_manifest(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate printable group manifest for transport/hotel check-in."""
    group = get_user_group(group_id, user, db)
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).order_by(GroupMember.nama).all()

    body = '<table><thead><tr>'
    body += '<th>#</th><th>Nama</th><th>No Paspor</th><th>Tgl Lahir</th><th>No HP</th><th>Ukuran Baju</th>'
    body += '</tr></thead><tbody>'
    for i, m in enumerate(members, 1):
        body += f'''<tr>
            <td>{i}</td>
            <td><strong>{m.nama}</strong></td>
            <td>{m.no_paspor or "-"}</td>
            <td>{m.tanggal_lahir or "-"}</td>
            <td>{m.no_hp or m.no_telepon or "-"}</td>
            <td>{m.baju_size or "-"}</td>
        </tr>'''
    body += '</tbody></table>'

    if not members:
        body = '<p style="text-align:center;color:#94a3b8;padding:40px;">Belum ada data jamaah dalam grup ini.</p>'

    return html_page(
        f"Manifest Jamaah — {group.name}",
        body,
        f"{len(members)} jamaah",
    )
