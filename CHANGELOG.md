# Changelog

## Unreleased

### Added

- Add complete scalar set operations, including algebra, membership,
  cardinality, subset/superset predicates and mutable-set procedures
- Render set values using deterministic brace notation

## 0.1.1 - 2026-07-29

### Fixed

- Preserve backslashes as literal characters in pseudocode strings
- Support bounded integer offsets for enumerated values, including pointer
  dereferences such as `MyPointer^ + 1`
- Keep text and random file type handling consistent between in-memory and
  local file systems
- Truncate local text files when they are opened in `WRITE` mode

### Changed

- Update package license metadata to the current SPDX format

## 0.1.0

Initial public release.

### Added

- Lexer, parser and interpreter for Cambridge-style pseudocode
- Basic data types
- Arrays
- Records
- Enumerated types
- Procedures and functions
- File handling
- Object-oriented subset
- CLI command `pseudo`
- REPL command
