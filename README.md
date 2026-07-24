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

Not implemented yet:

- `PROCEDURE`
- `FUNCTION`
- user-defined types
- records
- sets
- pointers
- file handling
- object-oriented pseudocode

## Strict mode

Strict mode currently enables additional checking:

- assignment must use `←`; ASCII `<-` is rejected
- variables must be declared before assignment
- identifiers are restricted to ASCII letters, digits and `_`, and must start with an ASCII letter

Run with strict mode:

```bash
python -m interpreter run path/to/program.pseudo --strict
```

## Development

Run tests:

```bash
python -m pytest -q
```
