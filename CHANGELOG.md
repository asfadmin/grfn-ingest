# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1]
### Changed
- Upgraded all Lambda functions to Python 3.12

## [2.0.0]
This release supports publishing v3 GUNW products to production CMR. CMR metadata has been significantly revised to reflect the current state of these products, align with other recently developed ASF CMR collections, and better support ASF search tooling.

### Changed
- Granules are now published to the `ARIA_S1_GUNW` collection in CMR instead of the `SENTINEL-1_INTERFEROGRAMS` collection.
- Granules are now published using the UMM-G json metadata format instead of the ECHO 10 xml format.
- Granule metadata content has been significantly revised.
- `perpendicular_baseline`, `temporal_baseline_days`, and `frame_number` are now required fields in the SDS metadata file instead of being optional.
### Removed
- Ingest of v2 GUNW products is no longer supported.
- Virtual geotiff products are no longer published to CMR.

## [1.2.1]
### Changed
- Upgraded Python and GitHub Action dependencies.

## [1.2.0]
### Removed
- ` (BETA)` from collection data set ID values to match new collection titles in grfn-cmr v2.1.0

## [1.1.0]
### Added
- `VERSION` attribute is now populated in CMR and `version` is now a required field in the input metadata file
- Optionally populate new `WEATHER_MODEL`, `TEMPORAL_BASELINE_DAYS`, and `FRAME_NUMBER` attributes in CMR in support of
  v3.0.0 GUNW products
### Changed
- Upgraded all dependencies and added `dependabot` configuration.
### Fixed
- Minor update to metadata schema for compatibility with latest version of `jsonschema`.

## [1.0.1]
### Added
- Unit tests for echo10-construction lambda

## [1.0.0]
### Added
- Versioned releases are now published to GitHub and changes are tracked in CHANGELOG.md
