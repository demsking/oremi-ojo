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

- **OREMI_OJO_SERVER_HOST**: The host address on which the application will listen. Default is `"0.0.0.0"`.
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

## Model Context Protocol

Oremi Ojọ implements the Model Context Protocol (MCP) using a strongly-typed
server. It exposes its core functionality as a set of tools, resources and
prompts that LLM agents can call directly.

The MCP server uses the **Streamable HTTP transport** protocol and is mounted at:

```txt
/mcp
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
- **`get_pollen_forecast`**: Retrieve hourly pollen forecast for a specific location. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.
    - `timezone` (str, default: `"auto"`): Timezone identifier.

#### Geocoding

- **`search_locations`**: Look up location coordinates and details for a query string (forward geocoding).
  - _Arguments_:
    - `query` (str): Search query (city, address, or landmark).
    - `limit` (int, default: `10`): Maximum number of results to return.
- **`reverse_geocode`**: Retrieve address and place name details by latitude and longitude coordinates.
  - _Arguments_:
    - `lat` (float): Latitude.
    - `lon` (float): Longitude.

### Available MCP Resources

The MCP server exposes weather and environmental data as dynamic resource templates that can be read by clients:

- **`weather:///{lat}/{lon}/current`**: Retrieve current weather conditions (temperature, humidity, wind, etc.) as a JSON resource.
  - _Template Parameters_:
    - `lat` (str): Latitude of the location.
    - `lon` (str): Longitude of the location.
- **`weather:///{lat}/{lon}/alerts`**: Retrieve active severe weather alerts and warnings as a JSON resource.
  - _Template Parameters_:
    - `lat` (str): Latitude.
    - `lon` (str): Longitude.
- **`weather:///{lat}/{lon}/air-quality`**: Retrieve current air quality indexes (AQI) and pollutant levels as a JSON resource.
  - _Template Parameters_:
    - `lat` (str): Latitude.
    - `lon` (str): Longitude.
- **`weather:///{lat}/{lon}/pollen`**: Retrieve current pollen allergen presence and concentration levels as a JSON resource.
  - _Template Parameters_:
    - `lat` (str): Latitude.
    - `lon` (str): Longitude.

### Available MCP Prompts

Prompts are predefined template messages for specific tasks, allowing agents to coordinate multi-step workflows:

- **`current_weather`**: Assist in getting the current weather conditions for a specific location.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`today_weather`**: Assist in getting today's weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`tonight_weather`**: Assist in getting tonight's weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`tomorrow_weather`**: Assist in getting tomorrow's weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`weekend_weather`**: Assist in getting the weekend weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`weekly_weather`**: Assist in getting a weekly weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`hourly_weather`**: Assist in getting an hourly weather forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`air_quality`**: Assist in getting the air quality (AQI) for a location.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`uv_index`**: Assist in getting the UV index forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`weather_alerts`**: Assist in checking for active weather alerts.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`sun_times`**: Assist in getting sunrise and sunset times.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`weather_summary`**: Assist in getting a comprehensive weather summary.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`plan_day`**: Assist in planning their day around the weather.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`outdoor_activity`**: Assist in determining if weather is suitable for outdoor activities.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`current_pollen_conditions`**: Assist in checking current pollen conditions. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`daily_pollen_forecast`**: Assist in getting the daily pollen forecast. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`pollen_outlook`**: Assist in getting a general pollen outlook. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`pollen_risk_assessment`**: Assist in assessing pollen allergy risks. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`pollen_health_advice`**: Assist in getting health advice related to current pollen levels. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`outdoor_activity_pollen_check`**: Assist in checking if outdoor activities are safe regarding pollen. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`pollen_alert_subscription`**: Assist in setting up pollen alerts. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.
  - _Arguments_:
    - `location` (str): The location name or address.
- **`explain_pollen_type`**: Assist in understanding a specific pollen type.
  - _Arguments_:
    - `pollen_type` (str): The pollen type to explain, e.g., 'birch', 'grass'.
- **`weather_data_source`**: Provide information about the data source used for weather forecasts and current conditions.
- **`air_quality_data_source`**: Provide information about the data source used for air quality information.
- **`pollen_data_source`**: Provide information about the data source used for pollen levels and forecasts.
- **`geocoding_data_source`**: Provide information about the data source used for location geocoding and address lookups.
- **`data_sources_summary`**: Provide a comprehensive summary of all external data sources powering Oremi Ojọ.

## Development

See the [contribution guide](https://gitlab.com/demsking/oremi-ojo/-/blob/main/CONTRIBUTING.md)
for development environment and contribution guidance.

## Versioning

Oremi Ojọ project adheres to [Semantic Versioning](https://semver.org/)
(SemVer). Version numbers follow the `MAJOR.MINOR.PATCH` format:

- **MAJOR** version increments for incompatible API changes
- **MINOR** version increments for backward-compatible new functionality
- **PATCH** version increments for backward-compatible bug fixes

The current version can be found by running:

```bash
oremi-ojo --version
```

## License

Copyright 2026 Sébastien Demanou. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://gitlab.com/demsking/oremi-ojo/-/blob/main/LICENSE

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
