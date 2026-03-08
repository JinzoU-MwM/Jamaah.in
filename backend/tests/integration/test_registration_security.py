from datetime import timedelta

from app.auth import create_access_token, hash_password
from app.models.group import Group
from app.models.registration import RegistrationLink
from app.models.user import User, Subscription, PlanType, SubscriptionStatus, utc_now


def _auth_headers(user_id: int, email: str) -> dict:
    token = create_access_token(data={"sub": str(user_id), "email": email})
    return {"Authorization": f"Bearer {token}"}


def _create_user(db_session, email: str) -> User:
    user = User(
        email=email,
        name=email.split("@")[0],
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


def test_registration_link_endpoints_enforce_group_ownership(client, db_session):
    owner = _create_user(db_session, "owner@example.com")
    attacker = _create_user(db_session, "attacker@example.com")

    group = Group(user_id=owner.id, name="Owner Group")
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    link = RegistrationLink(
        group_id=group.id,
        token=RegistrationLink.generate_token(),
        expires_at=utc_now() + timedelta(days=7),
        created_by=owner.id,
        is_active=True,
    )
    db_session.add(link)
    db_session.commit()

    attacker_headers = _auth_headers(attacker.id, attacker.email)
    get_resp = client.get(f"/registration/link/{group.id}", headers=attacker_headers)
    assert get_resp.status_code == 403

    revoke_resp = client.delete(f"/registration/link/{group.id}", headers=attacker_headers)
    assert revoke_resp.status_code == 403


def test_public_registration_accepts_multipart_phone_number(client, db_session):
    owner = _create_user(db_session, "registrar@example.com")
    group = Group(user_id=owner.id, name="Reg Group")
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    token = RegistrationLink.generate_token()
    db_session.add(
        RegistrationLink(
            group_id=group.id,
            token=token,
            expires_at=utc_now() + timedelta(days=7),
            created_by=owner.id,
            is_active=True,
        )
    )
    db_session.commit()

    files = {
        "phone_number": (None, "08123456789"),
        "ktp": ("ktp.jpg", b"fake-image", "image/jpeg"),
    }
    response = client.post(f"/registration/public/{token}", files=files)
    assert response.status_code == 200
    assert response.json()["success"] is True
