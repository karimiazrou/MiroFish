"""Security controls for the MiroFish HTTP API.

This first hardening layer is intentionally single-tenant: one server-side API
key protects the deployment. Do not use it as a multi-user authorization
system. Put the application behind a trusted reverse proxy and inject the key
server-side; never ship it in the Vue bundle.
"""
from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque
from ipaddress import ip_address

from flask import jsonify, request


class _WindowLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: tuple[str, str], limit: int, window: int = 60) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= window:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


_limiter = _WindowLimiter()


def _is_loopback(address: str | None) -> bool:
    try:
        return bool(address) and ip_address(address).is_loopback
    except ValueError:
        return False


def register_security(app) -> None:
    """Register CORS allow-list, API-key gate and process-local rate limits."""
    from flask_cors import CORS

    origins = [
        item.strip()
        for item in app.config.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    ]
    if origins:
        CORS(
            app,
            resources={r"/api/*": {"origins": origins}},
            allow_headers=["Content-Type", "Accept-Language", "X-MiroFish-API-Key"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            supports_credentials=False,
        )

    @app.before_request
    def protect_api():
        if not request.path.startswith("/api/") or request.method == "OPTIONS":
            return None

        expected = app.config.get("API_AUTH_TOKEN")
        supplied = request.headers.get("X-MiroFish-API-Key", "")

        # Explicit opt-in for local development only. Never enable this on a
        # public interface or production deployment.
        local_dev = (
            app.config.get("ALLOW_INSECURE_LOCAL_DEV", False)
            and not app.config.get("DEBUG", False)
            and _is_loopback(request.remote_addr)
        )
        if not expected:
            if not local_dev:
                return jsonify({"success": False, "error": "API authentication is not configured"}), 503
        elif not (supplied and hmac.compare_digest(str(expected), supplied)):
            return jsonify({"success": False, "error": "Authentication required"}), 401

        client = request.remote_addr or "unknown"
        general_limit = max(1, int(app.config.get("API_RATE_LIMIT_PER_MINUTE", 60)))
        if not _limiter.allow((client, "general"), general_limit):
            return jsonify({"success": False, "error": "Rate limit exceeded"}), 429

        expensive_prefixes = tuple(
            app.config.get(
                "API_EXPENSIVE_PATH_PREFIXES",
                ("/api/graph/ontology", "/api/simulation", "/api/report"),
            )
        )
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.path.startswith(expensive_prefixes):
            expensive_limit = max(1, int(app.config.get("API_EXPENSIVE_RATE_LIMIT_PER_MINUTE", 5)))
            if not _limiter.allow((client, "expensive"), expensive_limit):
                return jsonify({"success": False, "error": "Operation rate limit exceeded"}), 429
        return None
