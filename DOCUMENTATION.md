**Oremi Ojọ** is a technical service that provides access to weather forecasts,
air quality information, pollen levels, and geocoding data. It exposes a
comprehensive set of REST API endpoints designed for reliable integration into
applications that require environmental and location intelligence. In addition
to its REST interface, Oremi Ojọ includes a Model Context Protocol (MCP)
interface that allows LLMs and agents to query its data using structured tools.

The name **"Ojọ"** comes from the Yoruba language and means **"weather"**. It
reflects the service's purpose of delivering current conditions, forecasts, and
related environmental data. Like other services in the Oremi ecosystem—such as
**Oremi Akọrin** and **Oremi Isinmi**—the name is concise, meaningful, and
rooted in Yoruba, reinforcing a consistent identity while remaining easy to
recognize and remember.

Project repository: https://gitlab.com/demsking/oremi-ojo

![Oremi Ojọ Logo](./static/logo.png)

## Features

- **Weather Forecasts**: Retrieve detailed weather information, including current conditions, hourly forecasts, daily forecasts, sunrise/sunset times, and weather alerts.
- **Air Quality Data**: Access air quality metrics (AQI) and levels for specific locations.
- **Pollen Data**: Get information about pollen levels and types (e.g., grass, birch, olive) to help manage allergies and plan outdoor activities.
- **Geocoding**: Perform forward and reverse geocoding to find locations by name, address, or coordinates (supporting multilingual display names via the `Accept-Language` header).
- **Model Context Protocol (MCP)**: Exposes a rich set of strongly-typed tools to LLMs/agents over a Streamable HTTP transport, allowing natural language interfaces to query environmental data.
- **Structured Pollen Payload**: Pollen responses expose `units`, `dominant_pollen`, and `details` by pollen type with `level` and `severity`.
- **Caching**: Supports caching of data to improve performance and reduce redundant API calls.
- **Dockerized**: Easily deployable using the [`demsking/oremi-ojo`](https://hub.docker.com/r/demsking/oremi-ojo) Docker image.

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
uv tool install oremi-ojo
```

#### Install with pip

```sh
python -m pip install oremi-ojo
```

#### Usage

```text
oremi-ojo [-h] [-v]
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

The [`demsking/oremi-ojo`](https://hub.docker.com/r/demsking/oremi-ojo)
Docker image is officially available on Docker Hub, supporting both
`linux/amd64` and `linux/arm64` platforms. The image exposes port `5040`, which
serves the REST API and the interactive documentation.

The interactive documentation can be accessed at `http://localhost:5040/docs/`
and allows testing available endpoints directly from the browser.

### Volumes

Oremi Ojọ is largely stateless and does not require persistent storage for
normal operation.

The Docker image does not define any persistent volumes. If you configure file
logging by setting `OREMI_OJO_LOG_FILE` to a location inside the container,
mount a host directory to preserve log files across container recreation.

### Deploy with Docker

Use the official Docker image
[`demsking/oremi-ojo`](https://hub.docker.com/r/demsking/oremi-ojo)
to run Oremi Ojọ:

```sh
docker run -d \
  --name oremi-ojo \
  --env-file <path_to_env_file> \
  -p 5040:5040 \
  demsking/oremi-ojo
```

Replace `<path_to_env_file>` with the path to your
[environment variables](#description/configuration) file containing the desired
configuration.

### Deploy with Docker Compose

Create a `compose.yaml` file:

```yaml
services:
  ojo:
    image: demsking/oremi-ojo
    ports:
      - "5040:5040"
```

Start the services with:

```sh
docker compose up -d
```

Once started, open the interactive documentation at:

```txt
http://localhost:5040/docs/
```

## Configuration

When configuring **Oremi Ojọ**, several environment variables are used to
control its behavior and connect with external services. Below is a breakdown
of these variables, grouped by their purpose.

### Server Configuration

- **OREMI_OJO_SERVER_HOST**: The host address on which the application will listen. Default is `"127.0.0.1"`.
- **OREMI_OJO_SERVER_PORT**: The port number on which the application will listen. Default is `5040`.
- **OREMI_OJO_API_PREFIX**: Base path for the API and docs routes. Default is `"/"`.

### HTTP Configuration

These variables control outbound HTTP calls made by Oremi Ojọ to external data
providers such as Nominatim and Open-Meteo. They do not control the server bind
address or the timeout for LLM generation.

- **OREMI_OJO_HTTP_REQUEST_TIMEOUT**: Global HTTP timeout in seconds for external requests. Default is `30.0`.
- **OREMI_OJO_HTTP_USER_AGENT**: User-Agent header sent to external HTTP services such as Nominatim. Default is `"oremi-ojo/<version> (https://gitlab.com/demsking/oremi-ojo)"`.
- **OREMI_OJO_HTTP_CACHE_TTL_SECONDS**: TTL in seconds for external HTTP cache sessions. Default is `3600.0`, matching the fastest hourly weather data refresh cadence used by the shared weather, air-quality, and pollen providers.

Example:

```env
OREMI_OJO_HTTP_REQUEST_TIMEOUT=20.0
OREMI_OJO_HTTP_USER_AGENT=oremi-ojo/3.0.0 (ops@example.com)
OREMI_OJO_HTTP_CACHE_TTL_SECONDS=1800.0
```

### Logging Configuration

- **OREMI_OJO_LOG_FILE**: Path to the log file for storing application logs. Empty defaults to console.
- **OREMI_OJO_LOG_LEVEL**: Controls the verbosity of logs. Options: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'`, `'CRITICAL'`. Default is `'INFO'`.

## MCP Integration

Oremi Ojọ implements the Model Context Protocol (MCP) using a strongly-typed
server. It exposes its core functionality as a set of tools that LLM agents can
call directly.

The MCP server uses the **Streamable HTTP transport** protocol and is mounted at:

```txt
/mcp
```

For example, when running locally on the default port, the MCP endpoint is:

```txt
http://localhost:5040/mcp
```

### Available MCP Tools

Below is the list of strongly-typed tools exposed by the MCP server:

#### Weather & Forecasts

- **`get_current_weather`**: Retrieve current weather conditions for a specific location.
  - _Arguments_:
    - `lat` (float): Latitude of the location.
    - `lon` (float): Longitude of the location.
    - `timezone` (str, default: `"auto"`): Timezone identifier.
    - `temperature_unit` (str, default: `"celsius"`): `"celsius"` or `"fahrenheit"`.
- **`get_hourly_forecast`**: Retrieve hourly weather forecast starting from the current hour.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
    - `timezone` (str, default: `"auto"`): Timezone identifier.
    - `temperature_unit` (str, default: `"celsius"`): `"celsius"` or `"fahrenheit"`.
    - `hours` (int, default: `24`): Number of hours to forecast.
- **`get_daily_forecast`**: Retrieve daily weather forecast for the next few days.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
    - `timezone` (str, default: `"auto"`): Timezone identifier.
    - `temperature_unit` (str, default: `"celsius"`): `"celsius"` or `"fahrenheit"`.
    - `days` (int, default: `7`): Number of days to forecast.
- **`get_weather_alerts`**: Retrieve severe weather alerts or warnings (extreme temperatures, high winds, heavy rain, high UV).
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
    - `timezone` (str, default: `"auto"`): Timezone identifier.
- **`get_sun_times`**: Retrieve sunrise and sunset times over the next few days.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
    - `timezone` (str, default: `"auto"`): Timezone identifier.
    - `days` (int, default: `7`): Number of days.

#### Environmental Data

- **`get_air_quality`**: Retrieve current air quality data (AQI and pollutant levels) using EAQI or USAQI standards.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
- **`get_pollen`**: Retrieve current pollen presence and concentration levels (e.g., grass, birch, olive) along with SILAM severity levels.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.

#### Geocoding

- **`search_locations`**: Look up location coordinates and details for a query string (forward geocoding).
  - _Arguments_:
    - `query` (str): Search query (city, address, or landmark).
    - `limit` (int, default: `10`): Maximum number of results to return.
- **`reverse_geocode`**: Retrieve address and place name details by latitude and longitude coordinates.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.

## Development

See the [contribution guide](https://gitlab.com/demsking/oremi-ojo/-/blob/main/CONTRIBUTING.md)
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
[LICENSE](https://gitlab.com/demsking/oremi-ojo/-/blob/main/LICENSE) for the
complete license text.
