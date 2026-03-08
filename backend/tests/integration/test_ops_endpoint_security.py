"""
Security tests for operational endpoints (/metrics and /cache-stats).
"""


def test_metrics_hidden_when_ops_endpoints_private_without_token(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_OPS_ENDPOINTS", "false")
    monkeypatch.delenv("OPS_ENDPOINT_TOKEN", raising=False)

    response = client.get("/metrics")
    assert response.status_code == 404


def test_metrics_requires_valid_ops_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_OPS_ENDPOINTS", "false")
    monkeypatch.setenv("OPS_ENDPOINT_TOKEN", "ops-secret")

    unauthorized = client.get("/metrics")
    wrong = client.get("/metrics", headers={"x-ops-token": "wrong"})
    authorized = client.get("/metrics", headers={"x-ops-token": "ops-secret"})

    assert unauthorized.status_code == 401
    assert wrong.status_code == 401
    assert authorized.status_code == 200
    assert "# TYPE http_requests_total counter" in authorized.text


def test_cache_stats_requires_valid_ops_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_OPS_ENDPOINTS", "false")
    monkeypatch.setenv("OPS_ENDPOINT_TOKEN", "ops-secret")

    unauthorized = client.get("/cache-stats")
    authorized = client.get("/cache-stats", headers={"x-ops-token": "ops-secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
