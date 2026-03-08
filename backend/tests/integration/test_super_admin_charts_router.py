"""
Integration tests for super admin chart series endpoint.
"""
from datetime import timedelta

from fastapi import status

from app.auth import create_access_token
from app.models.user import UsageLog, Payment, PaymentStatus, utc_now


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_super_admin_charts_requires_auth(client):
    response = client.get("/super-admin/charts")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_super_admin_charts_requires_super_admin(client, test_user):
    response = client.get("/super-admin/charts", headers=_auth_headers(test_user.id))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_super_admin_charts_returns_real_aggregates(client, db_session, test_user):
    test_user.is_super_admin = True
    db_session.commit()

    now = utc_now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_anchor = (month_start - timedelta(days=1)).replace(day=15)

    db_session.add_all(
        [
            UsageLog(user_id=test_user.id, count=3, created_at=now),
            UsageLog(user_id=test_user.id, count=2, created_at=now),
            UsageLog(user_id=test_user.id, count=4, created_at=now - timedelta(days=1)),
            Payment(
                user_id=test_user.id,
                order_id="chart-paid-current",
                amount=150000,
                status=PaymentStatus.PAID,
                created_at=now,
                paid_at=now,
            ),
            Payment(
                user_id=test_user.id,
                order_id="chart-paid-prev",
                amount=250000,
                status=PaymentStatus.PAID,
                created_at=prev_month_anchor,
                paid_at=prev_month_anchor,
            ),
            Payment(
                user_id=test_user.id,
                order_id="chart-pending-current",
                amount=999000,
                status=PaymentStatus.PENDING,
                created_at=now,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/super-admin/charts", headers=_auth_headers(test_user.id))
    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    assert len(payload["user_activity"]) == 30
    assert len(payload["revenue_monthly"]) == 12

    daily = {item["date"]: item["count"] for item in payload["user_activity"]}
    assert daily[now.date().isoformat()] == 5
    assert daily[(now - timedelta(days=1)).date().isoformat()] == 4

    monthly = {item["month"]: item["amount"] for item in payload["revenue_monthly"]}
    assert monthly[now.strftime("%Y-%m")] == 150000
    assert monthly[prev_month_anchor.strftime("%Y-%m")] == 250000
