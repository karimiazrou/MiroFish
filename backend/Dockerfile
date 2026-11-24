FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Install the locked application dependencies, then a pinned production WSGI server.
COPY backend/pyproject.toml backend/uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
RUN uv sync --frozen --no-dev \
    && uv pip install --python .venv/bin/python gunicorn==23.0.0

COPY backend/ ./

EXPOSE 5001
CMD ["uv", "run", "--no-sync", "gunicorn", "--workers", "1", "--threads", "8", "--timeout", "360", "--bind", "0.0.0.0:5001", "app:create_app()"]
