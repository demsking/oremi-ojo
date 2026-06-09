# Changelog

All notable changes to this project are documented in this file.

## 3.0.0-beta12 - 2026-06-09

### Added

- Multilingual output pipeline for generative responses:
  - English-first message generation.
  - Automatic translation to detected output language for `/agent/climate`.
  - Translation to requested BCP-47 language code for `/agent/alerts`.
- Output language detection from user query in `/agent/climate`.
- Translation quality review pass for localized weather/alert messages.
- French pollen terminology glossary guardrails for translation consistency.
- Release documentation updates in `README.md` and `DOCUMENTATION.md`.

### Changed

- Pollen provider now uses Open-Meteo/CAMS pollen fields and structured data mapping.
- Pollen schema now emphasizes structured details by pollen type with:
  - `details: dict[PollenName, PollenDetail]`
  - `units`
  - `dominant_pollen`
- Pollen severity classification refined to a finer-grained scale.
- `/agent/climate` supports multi-service and multi-location orchestration in one query.
- `/agent/climate` returns HTTP `460` when no service can be identified.
- `/agent/alerts` returns HTTP `503` when provider resolution fails.

### Fixed

- Date extraction flow made more deterministic and resilient.
- Reduced duplicated logic in controller prompt/date/translation flow.
- Improved translation fluency and reduced literal phrasing artifacts.
