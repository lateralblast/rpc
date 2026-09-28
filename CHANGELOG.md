# Changelog

All notable changes to this project are documented in this file.

## [0.1.9] - 2026-09-29

- Fixed `requirements.txt`, which listed only `pycryptodome` and omitted
  `terminaltables` and the `PyP100` fork that `rpc.py` also imports

## [0.1.8] - 2026-09-29

- Fixed `--item list` printing a spurious extra `key: value` line due to a
  loop variable shadowing the requested item key
- Fixed `--save` silently discarding credentials for a plug not already
  present in an existing credentials file

## [0.1.7] - 2026-09-29

- Relicensed from CC BY-SA to CC BY-NC-SA and added a `LICENSE` file

## [0.1.6] - 2026-08-14

- Fixed python module check

## [0.1.5] - 2025-07-02

- Updated documentation

## [0.1.4] - 2025-07-01

- Added initial code to scan for tapo devices

## [0.1.3] - 2025-06-26

- Fixes based on pylint recommendations
- Updated documentation

## [0.1.2] - 2025-06-26

- Added pylint switch

## [0.1.1] - 2025-06-26

- Fixed password file processing

## [0.1.0] - 2025-06-26

- Added code to check file permissions

## [0.0.9] - 2025-06-26

- Added verbose option

## [0.0.8] - 2025-06-26

- Added code to return a specific item of information

## [0.0.7] - 2025-06-26

- Updated documentation

## [0.0.6] - 2025-06-26

- Added tables format

## [0.0.5] - 2025-06-26

- Added JSON parsing

## [0.0.4] - 2025-06-26

- Added mask function

## [0.0.3] - 2025-06-26

- Fixes based on linter recommendations

## [0.0.2] - 2025-06-26

- Added password file code

## [0.0.1] - 2025-06-26

- Initial version
