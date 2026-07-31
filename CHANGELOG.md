# Changelog

## Unreleased

## 0.1.2 - 2026-07-31

### Added

- Add a non-executing `cambridge-2027` compliance profile
- Add `pseudo check` with text and JSON diagnostics
- Check keyword case, structural indentation, identifiers, formal syntax and
  documented `psei` extensions
- Auto-detect and preprocess examination line numbers
- Add guide-section conformance tests for the 2027-2029 pseudocode guide
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
