# MiroFish — secure deployment notes

## Security model in this branch

This branch adds a **single-tenant deployment gate**, not a multi-user account
system. One server-side `API_AUTH_TOKEN` protects the API. All callers who are
authorized by that one deployment credential act as the same tenant. Do not
share the credential with untrusted users. Per-user project ownership and
multi-tenant data partitioning remain future work and are not claimed as fixed.

The Vue application never receives the API token. In the Docker Compose
deployment, Nginx injects `X-MiroFish-API-Key` on the private backend hop.
The backend is not published to the host; only the frontend/reverse-proxy
container is bound to `127.0.0.1:3000`.

## Generate secrets

Generate two independent random secrets (do not reuse either value):

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Put the first in `SECRET_KEY` and the second in `API_AUTH_TOKEN` in a local
`.env` file. Never commit `.env`, put the API token in a `VITE_*` variable,
or paste it into frontend code. Keep the file readable only by the deployment
operator.

## Local Docker deployment

```bash
docker compose build
docker compose up -d
```

Open `http://127.0.0.1:3000`. The backend is reachable only on the internal
Compose network. The Nginx container injects the server-side API key and
applies an ingress request-rate limit. The Flask middleware also applies
per-client and expensive-operation limits.

## Local source development

For a private, loopback-only developer workstation, set
`ALLOW_INSECURE_LOCAL_DEV=true` and keep `FLASK_HOST=127.0.0.1`.
This bypass is rejected for non-loopback clients and when Flask debug mode is
enabled. Do not use it on a LAN server, cloud VM, or public deployment.

## Remote access

The included Compose stack deliberately does not publish a public listener.
For remote access, place a separately managed HTTPS gateway in front of the
loopback-bound frontend, enforce TLS and access controls there, and review
trusted proxy settings before enabling them. Do not publish backend port 5001.

## Limits and remaining work

- The Python rate limiter is process-local. The Compose stack uses one Gunicorn
  worker so its in-process counters are shared across request threads. If the
  deployment is scaled to multiple workers/replicas, move rate limiting to a
  shared gateway or Redis-backed limiter.
- The current API key is a single service credential. It does not implement
  user accounts, roles, or per-project ownership. Do not expose one deployment
  to mutually untrusted users.
- The health endpoint is intentionally unauthenticated and returns only
  service status.
- Security tests are in `backend/tests/test_security.py`; run them in the
  project environment before deployment.
- No production deployment, external LLM/Zep call, or migration is performed
  by this patch.
