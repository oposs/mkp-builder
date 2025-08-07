# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### New

### Changed

### Fixed
- Fix lib.tar creation to properly handle both `check_mk/` and `python3/cmk/` directory structures with consistent MKP-compatible archive paths
- Add conflict detection when both `local/lib/check_mk/` and `local/lib/python3/cmk/` exist as directories

## 2.0.1 - 2025-08-07
### Changed
- Update README.md examples to use v2.0.0 and document breaking changes from v1.x

### Fixed
- Fix deprecated GitHub Actions ::set-output command usage to use new GITHUB_OUTPUT environment file format

## 2.0.0 - 2025-08-07
### New
- Add support for INI configuration format with `.mkp-builder.ini` files
- Add multiline description support in configuration files
- Add `__pycache__` directory filtering to exclude Python cache files from packages

### Changed
- **BREAKING**: Configuration file format changed from `.mkp-builderrc` (key=value) to `.mkp-builder.ini` (INI format with `[package]` section)
- **BREAKING**: Command line arguments renamed for clarity:
  - `--cmk-min` → `--version-min-required`
  - `--cmk-packaged` → `--version-packaged`
- **BREAKING**: GitHub Action inputs renamed:
  - `cmk-min-version` → `version-min-required`
  - `cmk-packaged-version` → `version-packaged`
- Internal configuration keys now match info file structure (e.g., `version.min_required`, `version.packaged`)
- Improved JSON formatting in `info.json` with proper indentation
- Enhanced Python dict formatting in `info` file using `pprint` module with 80-character line width

### Fixed
- Package files now properly exclude `__pycache__` directories and their contents

## 1.0.1 - 2025-08-06
### New
- Add full support for `VERSION_USABLE_UNTIL` including a command line argument, a GHA input and documentation.

## 1.0.0 - 2025-08-06
### New
- Initial release of CheckMK MKP Builder Action


