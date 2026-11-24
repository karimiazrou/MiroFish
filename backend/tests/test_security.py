from flask import Flask
from app.utils.security import register_security


def _app(**overrides):
    app = Flask(__name__)
    app.config.update(
        API_AUTH_TOKEN="test-token-that-is-long-enough",
        ALLOW_INSECURE_LOCAL_DEV=False,
        DEBUG=False,
        CORS_ALLOWED_ORIGINS="https://trusted.example",
        API_RATE_LIMIT_PER_MINUTE=100,
        API_EXPENSIVE_RATE_LIMIT_PER_MINUTE=5,
        API_EXPENSIVE_PATH_PREFIXES=("/api/simulation",),
    )
    app.config.update(overrides)
    register_security(app)

    @app.get("/api/ping")
    def ping():
        return {"success": True}

    @app.post("/api/simulation/start")
    def start():
        return {"success": True}

    return app


def test_api_rejects_missing_and_invalid_key():
    client = _app().test_client()
    assert client.get("/api/ping").status_code == 401
    assert client.get("/api/ping", headers={"X-MiroFish-API-Key": "wrong"}).status_code == 401


def test_api_accepts_valid_server_injected_key():
    client = _app().test_client()
    response = client.get(
        "/api/ping",
        headers={"X-MiroFish-API-Key": "test-token-that-is-long-enough"},
    )
    assert response.status_code == 200


def test_api_fails_closed_when_key_is_not_configured():
    client = _app(API_AUTH_TOKEN=None).test_client()
    response = client.get("/api/ping")
    assert response.status_code == 503


def test_cors_allows_only_configured_origin():
    client = _app().test_client()
    trusted = client.options(
        "/api/ping",
        headers={
            "Origin": "https://trusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    untrusted = client.options(
        "/api/ping",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert trusted.headers.get("Access-Control-Allow-Origin") == "https://trusted.example"
    assert "Access-Control-Allow-Origin" not in untrusted.headers


def test_general_rate_limit_returns_429():
    client = _app(API_RATE_LIMIT_PER_MINUTE=1).test_client()
    headers = {"X-MiroFish-API-Key": "test-token-that-is-long-enough"}
    assert client.get("/api/ping", headers=headers, environ_overrides={"REMOTE_ADDR": "192.0.2.11"}).status_code == 200
    assert client.get("/api/ping", headers=headers, environ_overrides={"REMOTE_ADDR": "192.0.2.11"}).status_code == 429


def test_expensive_operations_have_separate_limit():
    client = _app(API_EXPENSIVE_RATE_LIMIT_PER_MINUTE=1).test_client()
    headers = {"X-MiroFish-API-Key": "test-token-that-is-long-enough"}
    assert client.post("/api/simulation/start", headers=headers, environ_overrides={"REMOTE_ADDR": "192.0.2.12"}).status_code == 200
    assert client.post("/api/simulation/start", headers=headers, environ_overrides={"REMOTE_ADDR": "192.0.2.12"}).status_code == 429


def test_local_bypass_is_limited_to_loopback():
    client = _app(API_AUTH_TOKEN=None, ALLOW_INSECURE_LOCAL_DEV=True).test_client()
    local = client.get("/api/ping", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    remote = client.get("/api/ping", environ_overrides={"REMOTE_ADDR": "198.51.100.25"})
    assert local.status_code == 200
    assert remote.status_code == 503
