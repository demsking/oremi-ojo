# Oremi Weather Agent

[![Buy me a beer](https://img.shields.io/badge/Buy%20me-a%20beer-1f425f.svg)](https://www.buymeacoffee.com/demsking)

**Oremi Weather Agent** is a powerful and user-friendly API for retrieving weather
forecasts, air quality data, pollen levels, geographical location data, and
server-related information. Built with FastAPI and designed to run in a Docker
container, Oremi Weather Agent provides developers with easy access to accurate
weather and geocoding data.

![Oremi Weather Agent Logo](doc/logo.jpg)

## Documentation

Find the Oremi Weather Agent deployment and API documentation at
[https://demsking.gitlab.io/oremi-weather-agent](https://demsking.gitlab.io/oremi-weather-agent).

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
  air quality, or pollen data for specific locations.
- **Multilingual Output Pipeline**: Responses are generated in English first,
  then translated to the detected (or requested) output language.
- **Multi-Service & Multi-Location Routing**: A single query can request
  weather, air quality, and pollen for one or several places.
- **Structured Pollen Schema**: Pollen responses include `units`,
  `dominant_pollen`, and a per-pollen `details` map with `level` and
  `severity`.
- **Dockerized**: Easily deployable using the `demsking/oremi-weather-agent` Docker
  image.

## Contribute

Please follow [CONTRIBUTING.md](https://gitlab.com/demsking/oremi-weather-agent/blob/main/CONTRIBUTING.md).

## Versioning

Given a version number `MAJOR.MINOR.PATCH`, increment the:

- `MAJOR` version when you make incompatible API changes,
- `MINOR` version when you add functionality in a backwards-compatible manner,
  and
- `PATCH` version when you make backwards-compatible bug fixes.

Additional labels for pre-release and build metadata are available as extensions
to the `MAJOR.MINOR.PATCH` format.

See [SemVer.org](https://semver.org/) for more details.

## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.
You may obtain a copy of the License at
[LICENSE](https://gitlab.com/demsking/oremi-weather-agent/blob/main/LICENSE).
