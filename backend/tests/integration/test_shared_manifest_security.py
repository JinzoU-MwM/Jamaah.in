from datetime import timedelta

from app.auth import create_access_token, hash_password
from app.models.group import Group
from app.models.user import User, Subscription, PlanType, SubscriptionStatus, utc_now


def _create_pro_user(db_session, email: str) -> User:
    user = User(
        email=email,
        name="Pro User",
        password_hash=hash_password("password123"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            trial_start=utc_now(),
            trial_end=utc_now() + timedelta(days=7),
            subscribed_at=utc_now(),
            expires_at=utc_now() + timedelta(days=30),
        )
    )
    db_session.commit()
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_shared_manifest_lockout_after_repeated_wrong_pin(client, db_session):
    user = _create_pro_user(db_session, "shared@example.com")
    group = Group(user_id=user.id, name="Shared Group")
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    share_resp = client.post(
        f"/groups/{group.id}/share",
        headers=_auth_headers(user),
        json={"pin": "1234", "expires_in_days": 30},
    )
    assert share_resp.status_code == 200
    shared_token = share_resp.json()["shared_token"]

    for _ in range(4):
        wrong = client.post(f"/shared/manifest/{shared_token}", json={"pin": "9999"})
        assert wrong.status_code == 401

    locked = client.post(f"/shared/manifest/{shared_token}", json={"pin": "9999"})
    assert locked.status_code == 429
