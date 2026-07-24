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
- user-defined enumerated types:
  - `TYPE Season = (Spring, Summer, Autumn, Winter)`
- user-defined record types:
  - `TYPE ... ENDTYPE`
  - field access using dot notation, for example `Pupil.LastName`
  - record assignment with cloning semantics
  - arrays of records
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
- procedures:
  - `PROCEDURE ... ENDPROCEDURE`
  - `CALL ProcedureName(...)`
  - `BYVAL`
  - `BYREF`
- functions:
  - `FUNCTION ... RETURNS ... ENDFUNCTION`
  - `RETURN`
  - function calls inside expressions
- built-in functions:
  - `RIGHT`
  - `MID`
  - `LENGTH`
  - `LCASE`
  - `UCASE`
  - `INT`
  - `RAND`

Not implemented yet:

- sets
- pointers
- file handling
- object-oriented pseudocode

## User-defined type notes

Enumerated types:

```text
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE ThisSeason : Season
ThisSeason ← Spring
```

Enumerated values are case-insensitive identifiers. If a variable has the same
name as an enumerated value, the variable shadows the enumerated value.

Record types:

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE FirstName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.YearGroup ← 6
```

Record fields are accessed using dot notation. Record values are copied on
assignment, so assigning one record variable to another does not alias their
field storage.

Arrays of records are supported:

```text
DECLARE Form : ARRAY[1:30] OF StudentRecord

Form[1].LastName ← "Ali"
Form[1].YearGroup ← 12
```

Record fields and array elements can be passed `BYREF`.

## Procedure and function notes

Parameters are passed by value by default.

```text
PROCEDURE AddOne(X : INTEGER)
```

`BYVAL` and `BYREF` can be used explicitly:

```text
PROCEDURE Swap(BYREF X : INTEGER, Y : INTEGER)
```

The passing mode persists across comma-separated parameters until another
`BYVAL` or `BYREF` keyword appears. In the example above, both `X` and `Y` are
passed by reference.

Functions cannot have `BYREF` parameters.

`RETURN` is valid only inside a function. It immediately exits the function and
returns its value.

Top-level type, procedure and function declarations are registered before normal
statements are executed, so forward calls are supported.

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
- unknown user-defined type checks
- record field checks
- enumerated type assignment checks
- arithmetic errors such as division by zero
- Boolean condition checks for `IF`, `WHILE` and `REPEAT`
- procedure/function arity checks
- function return type checks
- `BYREF` argument lvalue and type checks

Run with strict mode:

```bash
python -m interpreter run path/to/program.pseudo --strict
```

## Development

Run tests:

```bash
python -m pytest -q
```
