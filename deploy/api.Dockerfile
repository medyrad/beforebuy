FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "--chdir", "backend", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
