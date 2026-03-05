"""
Integration tests for Prometheus-style HTTP metrics endpoint.
"""


def test_metrics_endpoint_exposes_http_metrics(client):
    client.get("/health")
    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text
    assert "# TYPE http_requests_total counter" in body
    assert '# TYPE http_errors_total counter' in body
    assert '# TYPE http_request_duration_seconds histogram' in body
    assert '# TYPE gemini_calls_total counter' in body
    assert '# TYPE gemini_cache_requests_total counter' in body
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in body


def test_metrics_endpoint_records_4xx_errors(client):
    client.get("/not-found-for-metrics-test")
    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text
    assert 'http_errors_total{method="GET",path="/not-found-for-metrics-test",status="404"}' in body
