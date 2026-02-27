"""
Progress Tracking Service for SSE (Server-Sent Events)
Manages real-time progress updates for document processing sessions.
"""
import json
import asyncio
import time
import logging
from typing import Dict, Any

from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

# Global dict to store progress per session
_progress_store: Dict[str, Dict[str, Any]] = {}

# SSE timeout (10 minutes — enough for large batch uploads)
SSE_TIMEOUT_SECONDS = 600
SSE_POLL_INTERVAL = 0.3


def update_progress(session_id: str, **kwargs):
    """Update progress for a session."""
    if session_id not in _progress_store:
        _progress_store[session_id] = {
            "current": 0, "total": 0, "status": "starting",
            "current_file": "", "completed_files": [],
            "failed_files": [], "done": False
        }
    _progress_store[session_id].update(kwargs)


def get_progress(session_id: str) -> dict | None:
    """Get current progress for a session."""
    return _progress_store.get(session_id)


def clear_progress(session_id: str):
    """Remove progress data for a session."""
    _progress_store.pop(session_id, None)


async def create_progress_stream(session_id: str):
    """Create an SSE event generator for real-time progress updates."""

    async def event_generator():
        last_sent = ""
        start = time.time()

        while time.time() - start < SSE_TIMEOUT_SECONDS:
            progress = _progress_store.get(session_id)
            if progress is None:
                yield {"event": "error", "data": json.dumps({"error": "Session not found"})}
                return

            current_json = json.dumps(progress)
            if current_json != last_sent:
                yield {"event": "progress", "data": current_json}
                last_sent = current_json

            if progress.get("done"):
                yield {"event": "done", "data": json.dumps({"status": "complete"})}
                # Clean up after a short delay
                await asyncio.sleep(2)
                _progress_store.pop(session_id, None)
                return

            await asyncio.sleep(SSE_POLL_INTERVAL)

        # Timeout cleanup
        _progress_store.pop(session_id, None)

    return EventSourceResponse(event_generator())
