ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.13.7


# [uv]
################################################################################
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
################################################################################


# [builder]
################################################################################
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# dependencies only: this layer is rebuilt when pyproject.toml / uv.lock change,
# not on every code change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-dev --no-install-project
################################################################################


# [runtime]
################################################################################
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}" \
    TZ=Europe/Kiev

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app app ./app

# mount points for the named volumes: created here so they are owned by `app`
RUN mkdir -p /app/media/cvs /app/app/shared/utils/logger/log_files \
    && chown -R app:app /app/media /app/app/shared/utils/logger/log_files

USER app
################################################################################


# [parser]
################################################################################
FROM runtime AS parser

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

USER root

# Chromium and its system libraries, the version matches the locked playwright
RUN playwright install --with-deps chromium \
    && chown -R app:app /ms-playwright \
    && rm -rf /var/lib/apt/lists/*

USER app
################################################################################
