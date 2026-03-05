# Observability

## Request ID Tracing

- Every HTTP request gets a `request_id`.
- If the client sends `X-Request-ID`, the backend reuses it.
- If missing, backend generates one and returns it in `X-Request-ID` response header.

## Structured Request Logs

Backend emits structured logs for each request with these fields:

- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`

On unhandled exceptions, the `http_request_failed` log includes stack trace plus `request_id`.

## Metrics Endpoint

- Backend exposes Prometheus-style metrics at `GET /metrics`.
- Core metrics:
  - `http_requests_total`
  - `http_errors_total`
  - `http_request_duration_seconds` (histogram)
  - `gemini_calls_total`
  - `gemini_cache_requests_total` (`result=hit|miss`)

## Example

```json
{
  "event": "http_request",
  "request_id": "7a9408f893904b57900ccf1fd8a39f8a",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 4.21,
  "level": "info",
  "timestamp": "2026-03-05T04:41:52.292736Z"
}
```
