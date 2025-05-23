#
## Stage 1: Builder
FROM python:3.11-alpine3.21 AS builder

ENV UV_LINK_MODE=copy

# Set the shell to /bin/ash and enable pipefail
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --locked --no-install-project --compile-bytecode

# Sync the project
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --locked

#
## Stage 2: Final
FROM python:3.11-alpine3.21

# Set the shell to /bin/ash and enable pipefail
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

ENV PATH="/opt/oremi-weather-agent/bin:$PATH"
ENV PYTHONPATH="/opt/oremi-weather-agent:/opt/oremi-weather-agent/.venv/lib/python3.11/site-packages"
ENV PYTHONUNBUFFERED="1"
ENV PYTHONDONTWRITEBYTECODE="1"

ENV TZ=UTC
ENV HOST="0.0.0.0"

ENV CACHE_DIR="/var/cache/oremi-weather-agent"

# Install dependencies
RUN apk update \
  && apk add --no-cache tzdata

# Copy the environment, but not the source code
COPY --from=builder --chown=oremi:oremi /app/.venv /opt/oremi-weather-agent/.venv

# Binaries
COPY bin/* /opt/oremi-weather-agent/bin/
RUN chmod +x /opt/oremi-weather-agent/bin/* \
  && mkdir -p /var/cache/oremi-weather-agent

# Copy application files
COPY server/ /opt/oremi-weather-agent/server
COPY pyproject.toml LICENSE DOCUMENTATION.md /opt/oremi-weather-agent/

# Expose the port
EXPOSE 1777

# Execute the application
CMD ["oremi-weather-agent"]
