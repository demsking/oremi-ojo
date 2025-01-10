#
## Stage 1: Build environment
FROM python:3.11-alpine3.19 AS build-env

ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_HOME='/usr/local'
ENV POETRY_VIRTUALENVS_CREATE=false

# Set the shell to /bin/ash and enable pipefail
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install build dependencies
RUN apk update \
  && apk add --no-cache curl \
  && curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /src
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-interaction --no-ansi --only=main

#
## Stage 2: Runtime environment
FROM python:3.11-alpine3.19

# Copy built Python dependencies from the build-env stage
COPY --from=build-env /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=build-env /usr/local/bin/ /usr/local/bin/

# Binaries
COPY bin/* /opt/oremi-forecast/bin/
RUN chmod +x /opt/oremi-forecast/bin/* \
  && mkdir -p /usr/local/cache

# Copy application files
COPY pyproject.toml LICENSE DOCUMENTATION.md /opt/oremi-forecast/
COPY server/ /opt/oremi-forecast/server

ENV PATH="/opt/oremi-forecast/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="/opt/oremi-forecast:/usr/local/lib/python3.11/site-packages"
ENV PYTHONUNBUFFERED="1"
ENV PYTHONDONTWRITEBYTECODE="1"

ENV TZ="UTC"
ENV CACHE_DIR="/usr/local/cache"

ENV LOG_LEVEL="info"
ENV LOG_FILE=

EXPOSE 1111

CMD ["oremi-forecast"]
