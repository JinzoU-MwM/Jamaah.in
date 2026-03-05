"""
Repository helpers for persistent AI result cache.
"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_result_cache import AIResultCache
from app.models.user import utc_now


def get_ai_cache(
    db: Session,
    *,
    cache_key: str,
) -> dict[str, Any] | None:
    """Return cached payload for a key, or None if missing/expired."""
    now = utc_now()
    row = db.query(AIResultCache).filter(AIResultCache.cache_key == cache_key).first()
    if row is None:
        return None

    if row.expires_at <= now:
        db.delete(row)
        db.commit()
        return None

    row.hits += 1
    row.last_accessed_at = now
    db.commit()

    return json.loads(row.result_json)


def put_ai_cache(
    db: Session,
    *,
    cache_key: str,
    input_hash: str,
    model: str,
    prompt_version: str,
    task_type: str,
    result: dict[str, Any],
    ttl_seconds: int,
) -> AIResultCache:
    """Upsert persistent cache row."""
    now = utc_now()
    expires_at = now + timedelta(seconds=max(1, ttl_seconds))
    payload = json.dumps(result, ensure_ascii=False)

    row = db.query(AIResultCache).filter(AIResultCache.cache_key == cache_key).first()
    if row is None:
        row = AIResultCache(
            cache_key=cache_key,
            input_hash=input_hash,
            model=model,
            prompt_version=prompt_version,
            task_type=task_type,
            result_json=payload,
            hits=0,
            created_at=now,
            last_accessed_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    else:
        row.input_hash = input_hash
        row.model = model
        row.prompt_version = prompt_version
        row.task_type = task_type
        row.result_json = payload
        row.expires_at = expires_at
        row.last_accessed_at = now

    db.commit()
    db.refresh(row)
    return row


def purge_expired_ai_cache(db: Session) -> int:
    """Delete expired rows and return number of deleted records."""
    now = utc_now()
    deleted = (
        db.query(AIResultCache)
        .filter(AIResultCache.expires_at <= now)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted)


def get_ai_cache_stats(db: Session) -> dict[str, int]:
    """Return basic persistent cache stats."""
    now = utc_now()
    total = db.query(AIResultCache).count()
    expired = db.query(AIResultCache).filter(AIResultCache.expires_at <= now).count()
    active = total - expired
    return {
        "total": int(total),
        "active": int(active),
        "expired": int(expired),
    }

