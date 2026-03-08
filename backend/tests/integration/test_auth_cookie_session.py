from datetime import timedelta

from app.auth import hash_password, AUTH_COOKIE_NAME
from app.models.user import User, Subscription, PlanType, SubscriptionStatus, utc_now


def _create_verified_user(db_session):
    user = User(
        email="cookie-user@example.com",
        name="Cookie User",
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
            plan=PlanType.FREE,
            status=SubscriptionStatus.TRIAL,
            trial_start=utc_now(),
            trial_end=utc_now() + timedelta(days=7),
        )
    )
    db_session.commit()
    return user


def test_login_sets_cookie_and_me_works_without_authorization_header(client, db_session):
    _create_verified_user(db_session)

    login_resp = client.post(
        "/auth/login",
        json={"email": "cookie-user@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    assert AUTH_COOKIE_NAME in login_resp.headers.get("set-cookie", "")

    me_resp = client.get("/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "cookie-user@example.com"

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200

    me_after_logout = client.get("/auth/me")
    assert me_after_logout.status_code == 401
