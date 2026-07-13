# Oremi Ojọ

[![Buy me a beer](https://img.shields.io/badge/Buy%20me-a%20beer-1f425f.svg)](https://www.buymeacoffee.com/demsking)

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

![Oremi Ojọ Logo](https://gitlab.com/demsking/oremi-ojo/-/raw/main/htdocs/logo.png)

## Documentation

Find the Oremi Ojọ deployment and API documentation at
[https://demsking.gitlab.io/oremi-ojo](https://demsking.gitlab.io/oremi-ojo).

Release notes are available in [CHANGELOG.md](https://gitlab.com/demsking/oremi-ojo/blob/main/CHANGELOG.md).

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
- **Multilingual Output**: Responses are generated directly in the detected
  (or requested) output language.
- **Multi-Service & Multi-Location Routing**: A single query can request
  weather, air quality, and pollen for one or several places.
- **Structured Pollen Schema**: Pollen responses include `units`,
  `dominant_pollen`, and a per-pollen `details` map with `level` and
  `severity`.
- **Dockerized**: Easily deployable using the `demsking/oremi-ojo` Docker
  image.

## Contribute

Please follow [CONTRIBUTING.md](https://gitlab.com/demsking/oremi-ojo/blob/main/CONTRIBUTING.md).

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
[LICENSE](https://gitlab.com/demsking/oremi-ojo/blob/main/LICENSE).
