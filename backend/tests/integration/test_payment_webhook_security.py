import hashlib
import hmac
import json
import importlib
from datetime import timedelta

payment_router_module = importlib.import_module("app.routers.payment_router")
from app.models.user import (
    User,
    Subscription,
    Payment,
    PlanType,
    SubscriptionStatus,
    PaymentStatus,
    utc_now,
)
from app.services import payment_service
from app.auth import hash_password


def _create_user_and_payment(db_session, order_id: str, amount: int = 80000):
    user = User(
        email=f"payer-{order_id.lower()}@example.com",
        name="Payer",
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
    db_session.add(
        Payment(
            user_id=user.id,
            order_id=order_id,
            amount=amount,
            status=PaymentStatus.PENDING,
        )
    )
    db_session.commit()
    return user


def _signed_payload(payload: dict, secret: str) -> tuple[bytes, str]:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return raw, signature


def test_webhook_rejects_invalid_signature(client, db_session, monkeypatch):
    _create_user_and_payment(db_session, order_id="PRO-1-AAAA1111")
    secret = "webhook-secret"
    monkeypatch.setattr(payment_service, "PAKASIR_WEBHOOK_SECRET", secret)

    raw, _ = _signed_payload({"order_id": "PRO-1-AAAA1111", "amount": 80000}, secret)
    resp = client.post(
        "/payment/webhook",
        data=raw,
        headers={"content-type": "application/json", "x-pakasir-signature": "invalid"},
    )
    assert resp.status_code == 401

    payment = db_session.query(Payment).filter(Payment.order_id == "PRO-1-AAAA1111").first()
    assert payment.status == PaymentStatus.PENDING


def test_webhook_rejects_when_provider_verification_fails(client, db_session, monkeypatch):
    _create_user_and_payment(db_session, order_id="PRO-2-BBBB2222")
    secret = "webhook-secret"
    monkeypatch.setattr(payment_service, "PAKASIR_WEBHOOK_SECRET", secret)
    monkeypatch.setattr(payment_router_module, "verify_transaction", lambda _oid: None)

    raw, sig = _signed_payload({"order_id": "PRO-2-BBBB2222", "amount": 80000}, secret)
    resp = client.post(
        "/payment/webhook",
        data=raw,
        headers={"content-type": "application/json", "x-pakasir-signature": sig},
    )
    assert resp.status_code == 502

    payment = db_session.query(Payment).filter(Payment.order_id == "PRO-2-BBBB2222").first()
    assert payment.status == PaymentStatus.PENDING


def test_webhook_rejects_verified_amount_mismatch(client, db_session, monkeypatch):
    _create_user_and_payment(db_session, order_id="PRO-3-CCCC3333", amount=80000)
    secret = "webhook-secret"
    monkeypatch.setattr(payment_service, "PAKASIR_WEBHOOK_SECRET", secret)
    monkeypatch.setattr(
        payment_router_module,
        "verify_transaction",
        lambda _oid: {"status": "paid", "amount": 90000, "reference": "ref-123"},
    )

    raw, sig = _signed_payload({"order_id": "PRO-3-CCCC3333", "amount": 80000}, secret)
    resp = client.post(
        "/payment/webhook",
        data=raw,
        headers={"content-type": "application/json", "x-pakasir-signature": sig},
    )
    assert resp.status_code == 400

    payment = db_session.query(Payment).filter(Payment.order_id == "PRO-3-CCCC3333").first()
    assert payment.status == PaymentStatus.PENDING


def test_webhook_accepts_paid_verified_transaction(client, db_session, monkeypatch):
    user = _create_user_and_payment(db_session, order_id="PRO-4-DDDD4444", amount=80000)
    secret = "webhook-secret"
    monkeypatch.setattr(payment_service, "PAKASIR_WEBHOOK_SECRET", secret)
    monkeypatch.setattr(
        payment_router_module,
        "verify_transaction",
        lambda _oid: {"status": "paid", "amount": 80000, "reference": "ref-xyz"},
    )

    raw, sig = _signed_payload({"order_id": "PRO-4-DDDD4444", "amount": 80000}, secret)
    resp = client.post(
        "/payment/webhook",
        data=raw,
        headers={"content-type": "application/json", "x-pakasir-signature": sig},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    payment = db_session.query(Payment).filter(Payment.order_id == "PRO-4-DDDD4444").first()
    assert payment.status == PaymentStatus.PAID

    db_session.refresh(user)
    assert user.subscription.plan == PlanType.PRO
