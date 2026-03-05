"""
Integration tests for super admin AI cache endpoints.
"""
from datetime import timedelta

from fastapi import status

from app.auth import create_access_token
from app.models.ai_result_cache import AIResultCache
from app.models.user import utc_now


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_ai_cache_stats_requires_auth(client):
    response = client.get("/super-admin/ai-cache/stats")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ai_cache_stats_requires_super_admin(client, test_user):
    response = client.get("/super-admin/ai-cache/stats", headers=_auth_headers(test_user.id))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ai_cache_stats_returns_counts(client, db_session, test_user):
    test_user.is_super_admin = True
    db_session.commit()

    now = utc_now()
    db_session.add(
        AIResultCache(
            cache_key="a" * 64,
            input_hash="1" * 64,
            model="gemini-2.5-flash",
            prompt_version="v1",
            task_type="extract_document_data:image",
            result_json='{"ok":1}',
            hits=0,
            created_at=now,
            last_accessed_at=now,
            expires_at=now + timedelta(hours=1),
        )
    )
    db_session.add(
        AIResultCache(
            cache_key="b" * 64,
            input_hash="2" * 64,
            model="gemini-2.5-flash",
            prompt_version="v1",
            task_type="extract_document_data:image",
            result_json='{"ok":2}',
            hits=0,
            created_at=now,
            last_accessed_at=now,
            expires_at=now - timedelta(minutes=1),
        )
    )
    db_session.commit()

    response = client.get("/super-admin/ai-cache/stats", headers=_auth_headers(test_user.id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {"total": 2, "active": 1, "expired": 1}


def test_purge_expired_ai_cache_endpoint(client, db_session, test_user):
    test_user.is_super_admin = True
    db_session.commit()

    now = utc_now()
    db_session.add(
        AIResultCache(
            cache_key="c" * 64,
            input_hash="3" * 64,
            model="gemini-2.5-flash",
            prompt_version="v1",
            task_type="extract_document_data:image",
            result_json='{"ok":3}',
            hits=0,
            created_at=now,
            last_accessed_at=now,
            expires_at=now + timedelta(hours=1),
        )
    )
    db_session.add(
        AIResultCache(
            cache_key="d" * 64,
            input_hash="4" * 64,
            model="gemini-2.5-flash",
            prompt_version="v1",
            task_type="extract_document_data:image",
            result_json='{"ok":4}',
            hits=0,
            created_at=now,
            last_accessed_at=now,
            expires_at=now - timedelta(minutes=1),
        )
    )
    db_session.commit()

    response = client.post("/super-admin/ai-cache/purge-expired", headers=_auth_headers(test_user.id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["deleted"] == 1
    assert data["before"] == {"total": 2, "active": 1, "expired": 1}
    assert data["after"] == {"total": 1, "active": 1, "expired": 0}
