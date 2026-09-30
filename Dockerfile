FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /bin/

RUN groupadd --system app && \
    useradd --system --gid app --create-home app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY manage.py ./
COPY config/ ./config/
COPY apps/ ./apps/
COPY common/ ./common/

USER app

EXPOSE 8000

CMD ["uv", "run", "--frozen", "--no-sync", "python", "manage.py", "runserver", "0.0.0.0:8000"]