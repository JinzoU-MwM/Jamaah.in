"""
Integration tests for persistent AI result cache repository.
"""
from datetime import timedelta

from app.models.ai_result_cache import AIResultCache
from app.models.user import utc_now
from app.services.ai_result_cache_repo import (
    get_ai_cache,
    get_ai_cache_stats,
    purge_expired_ai_cache,
    put_ai_cache,
)


def test_put_and_get_ai_cache(db_session):
    key = "k1" * 32
    payload = {"nama": "Budi", "document_type": "KTP"}

    put_ai_cache(
        db_session,
        cache_key=key,
        input_hash="h1" * 32,
        model="gemini-2.5-flash",
        prompt_version="v1",
        task_type="extract_document_data:image",
        result=payload,
        ttl_seconds=300,
    )

    cached = get_ai_cache(db_session, cache_key=key)
    assert cached == payload

    row = db_session.query(AIResultCache).filter(AIResultCache.cache_key == key).first()
    assert row is not None
    assert row.hits == 1


def test_get_ai_cache_returns_none_when_expired(db_session):
    key = "k2" * 32
    payload = {"ok": True}

    put_ai_cache(
        db_session,
        cache_key=key,
        input_hash="h2" * 32,
        model="gemini-2.5-flash",
        prompt_version="v1",
        task_type="extract_document_data:image",
        result=payload,
        ttl_seconds=300,
    )

    row = db_session.query(AIResultCache).filter(AIResultCache.cache_key == key).first()
    row.expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()

    assert get_ai_cache(db_session, cache_key=key) is None
    assert db_session.query(AIResultCache).filter(AIResultCache.cache_key == key).first() is None


def test_purge_expired_and_stats(db_session):
    put_ai_cache(
        db_session,
        cache_key="k3" * 32,
        input_hash="h3" * 32,
        model="gemini-2.5-flash",
        prompt_version="v1",
        task_type="extract_document_data:image",
        result={"a": 1},
        ttl_seconds=300,
    )
    put_ai_cache(
        db_session,
        cache_key="k4" * 32,
        input_hash="h4" * 32,
        model="gemini-2.5-flash",
        prompt_version="v1",
        task_type="extract_document_data:image",
        result={"b": 2},
        ttl_seconds=300,
    )

    expiring_row = (
        db_session.query(AIResultCache)
        .filter(AIResultCache.cache_key == "k4" * 32)
        .first()
    )
    expiring_row.expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()

    before = get_ai_cache_stats(db_session)
    assert before["total"] == 2
    assert before["expired"] == 1
    assert before["active"] == 1

    deleted = purge_expired_ai_cache(db_session)
    assert deleted == 1

    after = get_ai_cache_stats(db_session)
    assert after["total"] == 1
    assert after["expired"] == 0
    assert after["active"] == 1

