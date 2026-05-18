#!/bin/bash
set -e

echo "[entrypoint] Running database migrations..."
cd /app/backend

set +e
MIGRATION_OUTPUT="$(python -m alembic upgrade head 2>&1)"
MIGRATION_STATUS=$?
set -e

if [ $MIGRATION_STATUS -ne 0 ]; then
    echo "$MIGRATION_OUTPUT"
    if echo "$MIGRATION_OUTPUT" | grep -q "Can't locate revision identified by"; then
        echo "[entrypoint] Detected unknown alembic revision. Stamping and retrying..."
        python -m alembic stamp --purge merge_heads_20260304
        python -m alembic upgrade head
    else
        echo "[entrypoint] Migration failed, but continuing with startup..."
    fi
fi

echo "[entrypoint] Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
