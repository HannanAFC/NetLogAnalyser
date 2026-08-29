FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.13-slim

COPY --from=uv /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    RUNNING_IN_CONTAINER=true

WORKDIR /app

ARG APP_VERSION=0.0.0
ENV APP_VERSION=${APP_VERSION}

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]