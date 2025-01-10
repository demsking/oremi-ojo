**Oremi Forecast** is a powerful and user-friendly API for retrieving weather
forecasts, geographical location data, and server-related information. Built
with FastAPI and designed to run in a Docker container, Oremi Forecast provides
developers with easy access to accurate weather and geocoding data.

## Features

- **Weather Forecasts**: Retrieve detailed weather information, including
  temperature, humidity, wind speed, wind direction, sunrise, and sunset times.
- **Pollen Data**: Access pollen levels and types (e.g., grass, birch, olive)
  for specific locations, helping users manage allergies and plan outdoor
  activities.
- **Geocoding**: Perform forward and reverse geocoding to find locations by
  name, address, or coordinates.
- **Caching**: Supports caching of data to improve performance and reduce
  redundant API calls.
- **Dockerized**: Easily deployable using the `demsking/oremi-forecast` Docker
  image.

## Docker Image

The [`demsking/oremi-forecast`](https://hub.docker.com/r/demsking/oremi-forecast)
Docker image is officially available on Docker Hub, supporting both
`linux/amd64` and `linux/arm64` platforms. The image is configured to expose
port `1111`, which serves the API and documentation endpoints.

The local documentation can be accessed at `http://localhost:1111/docs` for easy
reference on available endpoints and usage instructions.

## Environment Variables

When configuring **Oremi Forecast**, several environment variables are used to
control its behavior and connect with external services. Below is a breakdown
of these variables, grouped by their purpose.

### HTTP and Caching Configuration

These variables control HTTP request behavior and caching settings.

- **HTTP_AGENT**:
  User agent string for HTTP requests. This string identifies the application
  and its version in HTTP requests. Defaults to `'oremi-forecast/<version>'`.

- **CACHE_DIR**:
  The directory in which to store cached data. Defaults to `'/usr/local/cache'`.

### CORS Configuration

- **ALLOWED_ORIGINS**: A comma-separated list of origins allowed for
  cross-origin requests. This helps secure the API by limiting access to
  trusted domains (e.g., `"https://example.com,https://another.com"`).

### API and Logging Configuration

These variables control the API root path, logging behavior, and server settings.

- **ROOT_PATH**:
  Defines the base URL path for all API routes. Defaults to `'/'`.

- **LOG_FILE**:
  Path to the log file for storing application logs. Empty defaults to console.

- **LOG_LEVEL**:
  Controls the verbosity of logs. Options: `'DEBUG'`, `'INFO'`, `'WARNING'`,
  `'ERROR'`, `'CRITICAL'`. Defaults to `'INFO'`.

### Performance Configuration

Settings that control the server's performance.

- **WORKERS**:
  The number of worker processes for handling requests. Defaults to the
  number of CPU cores on the system.
