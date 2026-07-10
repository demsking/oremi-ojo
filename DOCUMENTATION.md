**Oremi Weather Agent** is a powerful and user-friendly API for retrieving weather
forecasts, air quality data, pollen levels, geographical location data, and
server-related information. Built with FastAPI and designed to run in a Docker
container, Oremi Weather Agent provides developers with easy access to accurate
weather and geocoding data.

![Oremi Weather Agent Logo](./static/logo.jpg)

Release notes are available in [CHANGELOG.md](https://gitlab.com/demsking/oremi-weather-agent/blob/main/CHANGELOG.md).

## Features

- **Weather Forecasts**: Retrieve detailed weather information, including
  temperature, humidity, wind speed, wind direction, sunrise, and sunset times.
- **Air Quality Data**: Access air quality metrics such as AQI, PM2.5, PM10,
  NO₂, and O₃ levels for specific locations.
- **Pollen Data**: Get information about pollen levels and types (e.g., grass,
  birch, olive) to help manage allergies and plan outdoor activities.
- **Geocoding**: Perform forward and reverse geocoding to find locations by
  name, address, or coordinates.
- **Generative Responses**: Use natural language queries to retrieve weather,
  air quality, or pollen data for specific locations through `/agent/message`.
- **Alert Routing**: Send an alert-focused request to `/agent/message` with
  route metadata in the request context to switch to the alert generator.
- **Multilingual Output Pipeline**: Messages are generated in English first and
  translated to the detected/requested language.
- **Multi-Service & Multi-Location Queries**: One query can combine weather,
  air quality, and pollen requests across multiple locations.
- **Structured Pollen Payload**: Pollen responses expose `units`,
  `dominant_pollen`, and `details` by pollen type with `level` and `severity`.
- **Caching**: Supports caching of data to improve performance and reduce
  redundant API calls.
- **Dockerized**: Easily deployable using the [`demsking/oremi-weather-agent`](https://hub.docker.com/r/demsking/oremi-weather-agent)
  Docker image.

## Deployment

### Docker Image

The [`demsking/oremi-weather-agent`](https://hub.docker.com/r/demsking/oremi-weather-agent)
Docker image is officially available on Docker Hub, supporting both
`linux/amd64` and `linux/arm64` platforms. The image is configured to expose
port `1777`, which serves the API and documentation endpoints.

The local documentation can be accessed at `http://localhost:1777/docs` for easy
reference on available endpoints and usage instructions.

### Deploy with Docker

Use the official Docker image [`demsking/oremi-weather-agent`](https://hub.docker.com/r/demsking/oremi-weather-agent)
to run Oremi Weather Agent:

```sh
docker run -d --env-file <path_to_env_file> -p 1777:1777 demsking/oremi-weather-agent
```

Replace `<path_to_env_file>` with the path to your
[environment variables](#description/environment-variables) file containing the
necessary configurations.

### Deploy with Docker Compose

Create a `compose.yml` file:

```yaml
services:
  agent:
    image: demsking/oremi-weather-agent
    depends_on:
      - ollama
    environment:
      OREMI_WEATHER_OLLAMA_BASE_URL: http://ollama:11434

  ollama:
    image: ollama/ollama
    restart: always
    runtime: nvidia
    volumes:
      - ~/.ollama:/root/.ollama
```

Run the container using `docker compose`:

```sh
docker compose up -d
```

## Environment Variables

When configuring **Oremi Weather Agent**, several environment variables are used to
control its behavior and connect with external services. Below is a breakdown
of these variables, grouped by their purpose.

### Server Configuration

- **OREMI_WEATHER_SERVER_HOST**: The host address on which the application will listen. Default is `"127.0.0.1"`.
- **OREMI_WEATHER_SERVER_PORT**: The port number on which the application will listen. Default is `1777`.
- **OREMI_WEATHER_API_PREFIX**: Base path for the API and docs routes. Default is `"/"`.
- **OREMI_WEATHER_REQUEST_TIMEOUT**: Global HTTP timeout in seconds for external requests. Default is `30.0`.
- **OREMI_WEATHER_USER_AGENT**: User-Agent header sent to external HTTP services such as Nominatim. Default is `"oremi-weather-agent/<version> (https://gitlab.com/demsking/oremi-weather-agent)"`.

### Caching Configuration

These variables control internal LLM caching and response generation.

- **OREMI_WEATHER_CACHE_ENABLED**: Enables the bounded internal cache. Default is `true`.
- **OREMI_WEATHER_CACHE_MAX_ENTRIES**: Maximum number of cached entries kept in memory. Default is `512`.
- **OREMI_WEATHER_CACHE_LLM_TTL_SECONDS**: TTL in seconds for cacheable LLM calls. Default is `300.0`.

### Ollama Configuration

- **OREMI_WEATHER_OLLAMA_BASE_URL**: Base URL of the Ollama API. Required when using an `ollama:` model.
- **OREMI_WEATHER_LLM_MODEL**: Model name to use for the agent. If it starts with `ollama:`, the prefix is stripped before the Ollama client is created. Default is `"ollama:qwen3.5:2b"`.
- **OREMI_WEATHER_LLM_REQUEST_TIMEOUT**: Timeout in seconds for LLM requests. Default is `15`.
- **OREMI_WEATHER_LLM_TEMPERATURE**: Sampling temperature used by the agent. Default is `0.3`.
- **OREMI_WEATHER_MAX_RESPONSE_TOKENS**: Maximum number of generated tokens. Default is `500`.
- **OREMI_WEATHER_LLM_SYSTEM_PROMPT**: System prompt for the agent. Default is the bundled prompt.

### API and Logging Configuration

- **OREMI_WEATHER_LOG_FILE**: Path to the log file for storing application logs. Empty defaults to console.
- **OREMI_WEATHER_LOG_LEVEL**: Controls the verbosity of logs. Options: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'`, `'CRITICAL'`. Default is `'INFO'`.

## MCP Integration

Oremi Weather Agent exposes a Model Context Protocol server.

The MCP HTTP transport is mounted at:

- `GET /mcp`
- `POST /mcp`
- `DELETE /mcp`

The MCP tool catalog is generated from the Oremi Weather Agent API routes that
belong to these tags:

- `Forecast Endpoints`
- `Geocode Endpoints`

The following tags are intentionally excluded from MCP tools:

- `Agent Endpoints`
- `Server Endpoints`

The MCP server is configured in HTTP mode and reuses the Oremi Weather Agent
app's OpenAPI schema, so tool descriptions stay in sync with the public API.
Response schemas are described in full for better client generation and
assistant planning.

## Development

See the [contribution guide](https://gitlab.com/demsking/oremi-weather/-/blob/main/CONTRIBUTING.md)
for development environment and contribution guidance.

## Versioning

Oremi Weather Agent follows [Semantic Versioning](https://semver.org/). Display the
installed version with:

```bash
oremi-weather-agent --version
```

## License

Copyright 2026 Sébastien Demanou. All Rights Reserved.

Licensed under the Apache License, Version 2.0. See the
[LICENSE](https://gitlab.com/demsking/oremi-weather/-/blob/main/LICENSE) for the
complete license text.
