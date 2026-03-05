"""
Lightweight Prometheus-style HTTP metrics for backend observability.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware

HISTOGRAM_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


class MetricsStore:
    """In-memory HTTP metrics store with Prometheus text rendering."""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests_total = defaultdict(int)  # (method, path, status) -> count
        self._errors_total = defaultdict(int)  # (method, path, status) -> count
        self._duration_sum = defaultdict(float)  # (method, path) -> total seconds
        self._duration_count = defaultdict(int)  # (method, path) -> count
        self._duration_buckets = defaultdict(
            lambda: [0 for _ in HISTOGRAM_BUCKETS]
        )  # (method, path) -> per-bucket counts
        self._gemini_calls_total = defaultdict(int)  # task_type -> count
        self._gemini_cache_requests_total = defaultdict(int)  # (task_type, result, cache_mode) -> count

    def observe_http_request(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        request_key = (method, path, str(status_code))
        latency_key = (method, path)

        with self._lock:
            self._requests_total[request_key] += 1
            if status_code >= 400:
                self._errors_total[request_key] += 1

            self._duration_sum[latency_key] += duration_seconds
            self._duration_count[latency_key] += 1

            for idx, upper_bound in enumerate(HISTOGRAM_BUCKETS):
                if duration_seconds <= upper_bound:
                    self._duration_buckets[latency_key][idx] += 1

    def observe_gemini_api_call(self, task_type: str) -> None:
        with self._lock:
            self._gemini_calls_total[task_type] += 1

    def observe_gemini_cache_result(self, task_type: str, hit: bool, cache_mode: str = "default") -> None:
        result = "hit" if hit else "miss"
        normalized_mode = (cache_mode or "default").strip().lower()
        with self._lock:
            self._gemini_cache_requests_total[(task_type, result, normalized_mode)] += 1

    def reset(self) -> None:
        """Reset in-memory metrics (used by tests)."""
        with self._lock:
            self._requests_total.clear()
            self._errors_total.clear()
            self._duration_sum.clear()
            self._duration_count.clear()
            self._duration_buckets.clear()
            self._gemini_calls_total.clear()
            self._gemini_cache_requests_total.clear()

    def render_prometheus(self) -> str:
        lines: list[str] = []

        with self._lock:
            lines.append("# HELP http_requests_total Total HTTP requests processed.")
            lines.append("# TYPE http_requests_total counter")
            for (method, path, status), value in sorted(self._requests_total.items()):
                lines.append(
                    'http_requests_total{method="%s",path="%s",status="%s"} %s'
                    % (_escape_label(method), _escape_label(path), _escape_label(status), value)
                )

            lines.append("# HELP http_errors_total Total HTTP requests with status >= 400.")
            lines.append("# TYPE http_errors_total counter")
            for (method, path, status), value in sorted(self._errors_total.items()):
                lines.append(
                    'http_errors_total{method="%s",path="%s",status="%s"} %s'
                    % (_escape_label(method), _escape_label(path), _escape_label(status), value)
                )

            lines.append("# HELP http_request_duration_seconds HTTP request duration in seconds.")
            lines.append("# TYPE http_request_duration_seconds histogram")
            for latency_key in sorted(self._duration_count.keys()):
                method, path = latency_key
                labels = 'method="%s",path="%s"' % (_escape_label(method), _escape_label(path))
                bucket_counts = self._duration_buckets[latency_key]
                cumulative = 0

                for idx, upper_bound in enumerate(HISTOGRAM_BUCKETS):
                    cumulative += bucket_counts[idx]
                    lines.append(
                        'http_request_duration_seconds_bucket{%s,le="%s"} %s'
                        % (labels, upper_bound, cumulative)
                    )

                total_count = self._duration_count[latency_key]
                lines.append(
                    'http_request_duration_seconds_bucket{%s,le="+Inf"} %s'
                    % (labels, total_count)
                )
                lines.append(
                    "http_request_duration_seconds_sum{%s} %s"
                    % (labels, self._duration_sum[latency_key])
                )
                lines.append(
                    "http_request_duration_seconds_count{%s} %s"
                    % (labels, total_count)
                )

            lines.append("# HELP gemini_calls_total Total upstream Gemini API calls.")
            lines.append("# TYPE gemini_calls_total counter")
            for task_type, value in sorted(self._gemini_calls_total.items()):
                lines.append(
                    'gemini_calls_total{task_type="%s"} %s'
                    % (_escape_label(task_type), value)
                )

            lines.append("# HELP gemini_cache_requests_total Gemini cache result counts.")
            lines.append("# TYPE gemini_cache_requests_total counter")
            for (task_type, result, cache_mode), value in sorted(self._gemini_cache_requests_total.items()):
                lines.append(
                    'gemini_cache_requests_total{task_type="%s",result="%s",cache_mode="%s"} %s'
                    % (_escape_label(task_type), _escape_label(result), _escape_label(cache_mode), value)
                )

        lines.append("")
        return "\n".join(lines)


metrics_store = MetricsStore()


class HttpMetricsMiddleware(BaseHTTPMiddleware):
    """Record per-request counters and duration histogram."""

    async def dispatch(self, request, call_next):
        method = request.method
        path = request.url.path
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_seconds = max(0.0, time.perf_counter() - started_at)
            metrics_store.observe_http_request(method, path, 500, duration_seconds)
            raise

        duration_seconds = max(0.0, time.perf_counter() - started_at)
        metrics_store.observe_http_request(method, path, response.status_code, duration_seconds)
        return response
