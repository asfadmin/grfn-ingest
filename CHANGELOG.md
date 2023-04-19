# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0]
### Added
- `VERSION` attribute is now populated in CMR and `version` is now a required field in the input metadata file
- Optionally populate new `WEATHER_MODEL`, `TEMPORAL_BASELINE_DAYS`, and `FRAME_NUMBER` attributes in CMR in support of
  v3.0.0 GUNW products

## [1.0.1]
### Added
- Unit tests for echo10-construction lambda

## [1.0.0]
### Added
- Versioned releases are now published to GitHub and changes are tracked in CHANGELOG.md
