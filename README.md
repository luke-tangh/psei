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
- text file handling:
  - `OPENFILE ... FOR READ`
  - `OPENFILE ... FOR WRITE`
  - `OPENFILE ... FOR APPEND`
  - `READFILE`
  - `WRITEFILE`
  - `CLOSEFILE`
  - `EOF(...)`
- random file handling:
  - `OPENFILE ... FOR RANDOM`
  - `SEEK`
  - `GETRECORD`
  - `PUTRECORD`
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
  - `EOF`
  - `RIGHT`
  - `MID`
  - `LENGTH`
  - `LCASE`
  - `UCASE`
  - `INT`
  - `RAND`
- object-oriented subset:
  - `CLASS ... ENDCLASS`
  - `INHERITS`
  - constructors as `PROCEDURE NEW(...)`
  - object creation with `NEW ClassName(...)`
  - method calls using dot notation
  - superclass calls using `SUPER.MethodName(...)`

Not implemented yet:

- sets
- pointers

## File handling notes

`run_source()` uses an in-memory file system by default. This keeps tests and
REPL-style execution deterministic and avoids writing temporary files to the
project directory.

`run_file()` uses a local file system rooted at the directory containing the
pseudocode source file, so relative file names are resolved beside the program
being run.

Text file example:

```text
DECLARE LineOfText : STRING

OPENFILE "FileA.txt" FOR READ
WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE
CLOSEFILE "FileA.txt"
```

Random file example:

```text
OPENFILE "StudentFile.Dat" FOR RANDOM
SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", Pupil
SEEK "StudentFile.Dat", 10
GETRECORD "StudentFile.Dat", LoadedPupil
CLOSEFILE "StudentFile.Dat"
```

Random files store runtime values at integer addresses. With the local file
system implementation, random files are persisted as JSON using the
interpreter's explicit runtime-value serializer. Object instances are not
persisted in random files; store scalar values, arrays or records instead.

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
- file mode checks
- text file EOF checks
- random file address checks
- arithmetic errors such as division by zero
- Boolean condition checks for `IF`, `WHILE` and `REPEAT`
- procedure/function arity checks
- function return type checks
- `BYREF` argument lvalue and type checks

Run with strict mode:

```bash
pseudo run path/to/program.pseudo --strict
# or
python -m psei run path/to/program.pseudo --strict
```

## Development

Run tests:

```bash
python -m pytest -q
```

## Object-oriented pseudocode notes

The interpreter includes a practical subset of Cambridge-style object-oriented pseudocode:

```text
CLASS Pet
   PRIVATE Name : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING)
      Name ← GivenName
   ENDPROCEDURE

   PUBLIC FUNCTION GetName() RETURNS STRING
      RETURN Name
   ENDFUNCTION
ENDCLASS

CLASS Cat INHERITS Pet
   PRIVATE Breed : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING, GivenBreed : STRING)
      SUPER.NEW(GivenName)
      Breed ← GivenBreed
   ENDPROCEDURE

   PUBLIC FUNCTION GetBreed() RETURNS STRING
      RETURN Breed
   ENDFUNCTION
ENDCLASS

MyCat ← NEW Cat("Kitty", "Shorthaired")
OUTPUT MyCat.GetName()
OUTPUT MyCat.GetBreed()
```

A declared class variable is an object reference. `DECLARE P : Player` creates a
`NULL`/uninitialised reference; use `P ← NEW Player(...)` before accessing
properties or methods.

Supported OOP features:

- `CLASS ... ENDCLASS`
- `INHERITS`
- `PUBLIC` and `PRIVATE` modifiers are parsed and stored
- constructors as `PROCEDURE NEW(...)`
- object creation with `NEW ClassName(...)`
- method calls using dot notation, for example `Player.SetAttempts(5)`
- method functions inside expressions, for example `Player.GetAttempts()`
- superclass constructor/method calls using `SUPER.MethodName(...)`
- per-object properties with default values
- method bodies can access object properties by name

Access modifiers are currently informational only; runtime enforcement of
`PRIVATE` members is not implemented yet.
