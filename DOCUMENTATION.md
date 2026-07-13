**Oremi Ojọ** is a technical service that provides access to weather forecasts,
air quality information, pollen levels, and geocoding data. It exposes a
comprehensive set of REST API endpoints designed for reliable integration into
applications that require environmental and location intelligence. In addition
to its REST interface, Oremi Ojọ includes an MCP interface for structured
interactions and an agent endpoint that enables natural language queries over
its data.

The name **"Ojọ"** comes from the Yoruba language and means **"weather"**. It
reflects the service's purpose of delivering current conditions, forecasts, and
related environmental data. Like other services in the Oremi ecosystem—such as
**Oremi Akọrin** and **Oremi Isinmi**—the name is concise, meaningful, and
rooted in Yoruba, reinforcing a consistent identity while remaining easy to
recognize and remember.

Project repository: https://gitlab.com/demsking/oremi-ojo

![Oremi Ojọ Logo](./static/logo.png)

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
- **Multilingual Output**: Messages are generated directly in the
  detected/requested language.
- **Multi-Service & Multi-Location Queries**: One query can combine weather,
  air quality, and pollen requests across multiple locations.
- **Structured Pollen Payload**: Pollen responses expose `units`,
  `dominant_pollen`, and `details` by pollen type with `level` and `severity`.
- **Caching**: Supports caching of data to improve performance and reduce
  redundant API calls.
- **Dockerized**: Easily deployable using the [`demsking/oremi-ojo`](https://hub.docker.com/r/demsking/oremi-ojo)
  Docker image.

## Deployment

Oremi Ojọ is distributed as a multi-platform Docker image for
`linux/amd64` and `linux/arm64`. It can be deployed as a standalone service or
integrated into the Oremi ecosystem alongside services such as Oremi Isinmi,
Weather, Rediyo, and Kansa.

The following sections describe the available Docker image, persistent storage
requirements, and example deployments using both Docker and Docker Compose.

### Command Line

Before installing Oremi Ojọ from PyPI, ensure the following requirements are
met:

- Python 3.12 or later.
- `uv` (recommended) or `pip` for package installation.

Oremi Ojọ can be installed either as a standalone command-line application
or as a Python package.

#### Install with uv

```sh
uv tool install oremi-weather
```

#### Install with pip

```sh
python -m pip install oremi-weather
```

#### Usage

```text
oremi-weather [-h] [-v]
```

When started without arguments, Oremi Ojọ launches the HTTP server using the
configured environment variables.

#### Options

- `-h`, `--help`: Display the command-line help and exit.
- `-v`, `--version`: Display the installed version and exit.

All server configuration, including the listening address, port, LLM backend,
and service endpoints, is provided through environment variables rather than
command-line options.

### Docker Image

The [`demsking/oremi-weather`](https://hub.docker.com/r/demsking/oremi-weather)
Docker image is officially available on Docker Hub, supporting both
`linux/amd64` and `linux/arm64` platforms. The image exposes port `1777`, which
serves the REST API and the interactive documentation.

The interactive documentation can be accessed at `http://localhost:1777/docs/`
and allows testing available endpoints directly from the browser.

### Volumes

Oremi Ojọ is largely stateless and does not require persistent storage for
normal operation.

The Docker image does not define any persistent volumes. If you configure file
logging by setting `OREMI_OJO_LOG_FILE` to a location inside the container,
mount a host directory to preserve log files across container recreation.

### Deploy with Docker

Use the official Docker image
[`demsking/oremi-weather`](https://hub.docker.com/r/demsking/oremi-weather)
to run Oremi Ojọ:

```sh
docker run -d \
  --name oremi-weather \
  --env-file <path_to_env_file> \
  -p 1777:1777 \
  demsking/oremi-weather
```

Replace `<path_to_env_file>` with the path to your
[environment variables](#description/configuration) file containing the desired
configuration.

### Deploy with Docker Compose

Create a `compose.yaml` file:

```yaml
services:
  agent:
    image: demsking/oremi-weather
    depends_on:
      - ollama
    environment:
      OREMI_OJO_OLLAMA_BASE_URL: http://ollama:11434

  ollama:
    image: ollama/ollama
    restart: always
    runtime: nvidia
    volumes:
      - ~/.ollama:/root/.ollama
    environment:
      CUDA_VISIBLE_DEVICES: 0
```

Start the services with:

```sh
docker compose up -d
```

Once started, open the interactive documentation at:

```txt
http://localhost:31777/docs/
```

## Configuration

When configuring **Oremi Ojọ**, several environment variables are used to
control its behavior and connect with external services. Below is a breakdown
of these variables, grouped by their purpose.

### Server Configuration

- **OREMI_OJO_SERVER_HOST**: The host address on which the application will listen. Default is `"127.0.0.1"`.
- **OREMI_OJO_SERVER_PORT**: The port number on which the application will listen. Default is `1777`.
- **OREMI_OJO_API_PREFIX**: Base path for the API and docs routes. Default is `"/"`.
- **OREMI_OJO_REQUEST_TIMEOUT**: Global HTTP timeout in seconds for external requests. Default is `30.0`.
- **OREMI_OJO_USER_AGENT**: User-Agent header sent to external HTTP services such as Nominatim. Default is `"oremi-ojo/<version> (https://gitlab.com/demsking/oremi-ojo)"`.

### Caching Configuration

These variables control internal LLM caching and response generation.

- **OREMI_OJO_CACHE_ENABLED**: Enables the bounded internal cache. Default is `true`.
- **OREMI_OJO_CACHE_MAX_ENTRIES**: Maximum number of cached entries kept in memory. Default is `512`.
- **OREMI_OJO_CACHE_LLM_TTL_SECONDS**: TTL in seconds for cacheable LLM calls. Default is `300.0`.

### Ollama Configuration

- **OREMI_OJO_OLLAMA_BASE_URL**: Base URL of the Ollama API. Required when using an `ollama:` model.
- **OREMI_OJO_LLM_MODEL**: Model name to use for the agent. If it starts with `ollama:`, the prefix is stripped before the Ollama client is created. Default is `"ollama:qwen3.5:2b"`.
- **OREMI_OJO_LLM_REQUEST_TIMEOUT**: Timeout in seconds for LLM requests. Default is `15`.
- **OREMI_OJO_LLM_TEMPERATURE**: Sampling temperature used by the agent. Default is `0.3`.
- **OREMI_OJO_MAX_RESPONSE_TOKENS**: Maximum number of generated tokens. Default is `500`.
- **OREMI_OJO_LLM_SYSTEM_PROMPT**: System prompt for the agent. Default is the bundled prompt.

### API and Logging Configuration

- **OREMI_OJO_LOG_FILE**: Path to the log file for storing application logs. Empty defaults to console.
- **OREMI_OJO_LOG_LEVEL**: Controls the verbosity of logs. Options: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'`, `'CRITICAL'`. Default is `'INFO'`.

## MCP Integration

Oremi Ojọ exposes a Model Context Protocol server.

The MCP HTTP transport is mounted at:

- `GET /mcp`
- `POST /mcp`
- `DELETE /mcp`

The MCP tool catalog is generated from the Oremi Ojọ API routes that
belong to these tags:

- `Forecast Endpoints`
- `Geocode Endpoints`

The following tags are intentionally excluded from MCP tools:

- `Agent Endpoints`
- `Server Endpoints`

The MCP server is configured in HTTP mode and reuses the Oremi Ojọ
app's OpenAPI schema, so tool descriptions stay in sync with the public API.
Response schemas are described in full for better client generation and
assistant planning.

## Development

See the [contribution guide](https://gitlab.com/demsking/oremi-weather/-/blob/main/CONTRIBUTING.md)
for development environment and contribution guidance.

## Versioning

Oremi Ojọ follows [Semantic Versioning](https://semver.org/). Display the
installed version with:

```bash
oremi-ojo --version
```

## License

Copyright 2026 Sébastien Demanou. All Rights Reserved.

Licensed under the Apache License, Version 2.0. See the
[LICENSE](https://gitlab.com/demsking/oremi-weather/-/blob/main/LICENSE) for the
complete license text.
