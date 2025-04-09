FROM python:3.11-alpine3.21

ENV PATH="/opt/oremi-weather-agent/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="/opt/oremi-weather-agent:/usr/local/lib/python3.11/site-packages"
ENV PYTHONUNBUFFERED="1"
ENV PYTHONDONTWRITEBYTECODE="1"

ENV HOST="0.0.0.0"
ENV PORT=1777

ENV CACHE_DIR="/var/cache/oremi-weather-agent"

ENV OLLAMA_MODEL="demsking/oremi:latest"
ENV OLLAMA_BASEURL=

ENV LOG_LEVEL="info"
ENV LOG_FILE=

# Set the shell to /bin/ash and enable pipefail
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Upgrade pip and setuptools to the latest version
RUN pip install --upgrade pip setuptools wheel

# Build Python dependencies
COPY build/requirements.txt /opt/oremi-weather-agent/
RUN pip install --no-cache-dir -r /opt/oremi-weather-agent/requirements.txt

# Binaries
COPY bin/* /opt/oremi-weather-agent/bin/
RUN chmod +x /opt/oremi-weather-agent/bin/* \
  && mkdir -p /var/cache/oremi-weather-agent

# Copy application files
COPY pyproject.toml LICENSE DOCUMENTATION.md /opt/oremi-weather-agent/
COPY server/ /opt/oremi-weather-agent/server

EXPOSE 1777

CMD ["oremi-weather-agent"]
