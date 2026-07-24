# psei

Minimal Cambridge-style pseudocode interpreter.

This project implements a practical subset of Cambridge International AS & A Level
Computer Science 9618-style pseudocode.

## Current supported subset

Supported:

- basic declarations:
  - `INTEGER`
  - `REAL`
  - `CHAR`
  - `STRING`
  - `BOOLEAN`
  - `DATE`
- constants with literal values
- assignment using `←`
- one-dimensional and two-dimensional arrays
- whole-array assignment with cloning semantics
- `INPUT`
- `OUTPUT`
- arithmetic:
  - `+`
  - `-`
  - `*`
  - `/`
  - `DIV`
  - `MOD`
- comparisons:
  - `=`
  - `<>`
  - `<`
  - `<=`
  - `>`
  - `>=`
- logic:
  - `AND`
  - `OR`
  - `NOT`
  - `AND` and `OR` use short-circuit evaluation
- selection:
  - `IF ... THEN ... ELSE ... ENDIF`
  - `CASE OF ... OTHERWISE ... ENDCASE`
- loops:
  - `FOR ... TO ... STEP ... NEXT`
  - `WHILE ... ENDWHILE`
  - `REPEAT ... UNTIL`
- built-in functions:
  - `RIGHT`
  - `MID`
  - `LENGTH`
  - `LCASE`
  - `UCASE`
  - `INT`
  - `RAND`

Phase 0 internal groundwork:

- AST statement nodes now have a single `span` field each
- the runtime has a scope stack with a global environment plus push/pop local scopes
- `BYVAL` and `BYREF` are tokenised and reserved for future procedure/function support

Not implemented yet:

- `PROCEDURE`
- `FUNCTION`
- user-defined types
- records
- sets
- pointers
- file handling
- object-oriented pseudocode

## Strict mode semantics

Strict mode is intentionally limited and explicit. It is a Cambridge-style
guardrail, not yet a complete validator for every presentation rule in the
pseudocode guide.

Strict mode currently guarantees:

- assignment must use `←`; ASCII `<-` is rejected
- variables must be declared before assignment
- identifiers are restricted to ASCII letters, digits and `_`
- identifiers must start with an ASCII letter

Non-strict mode currently allows:

- assignment using either `←` or ASCII `<-`
- assignment to an undeclared variable, creating it with an inferred type
- non-ASCII alphabetic characters in identifiers

Both modes still perform core runtime checks, including:

- declared assignment type checks
- constant immutability
- constant values must be literals
- array bounds checks
- arithmetic errors such as division by zero
- Boolean condition checks for `IF`, `WHILE` and `REPEAT`

`BYVAL` and `BYREF` are currently recognised as keywords only. Parameter
passing behavior will be implemented when `PROCEDURE` and `FUNCTION` support is
added.

Run with strict mode:

```bash
python -m interpreter run path/to/program.pseudo --strict
```

## Development

Run tests:

```bash
python -m pytest -q
```
