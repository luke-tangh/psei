# psei

`psei` is a lightweight interpreter for Cambridge International AS & A Level Computer Science 9618-style pseudocode.

It implements a practical subset of Cambridge-style pseudocode and can be used for:

- running `.pseudo` files locally
- experimenting with pseudocode in a REPL
- executing pseudocode from Python tests or applications
- building teaching examples
- checking common runtime and type errors
- checking source against the Cambridge 2027-2029 pseudocode guide

> `psei` is not an official Cambridge tool. Its compliance profile checks
> plain-text source rules but cannot validate presentation details such as font
> choice. Its goal is to provide a useful, testable interpreter and checker for
> a Cambridge-style pseudocode subset.

## Quick start

Install as a CLI tool:

```bash
pipx install psei
```

Or install with pip:

```bash
python -m pip install psei
```

Create `hello.pseudo`:

```text
OUTPUT "Hello"
```

Run it:

```bash
pseudo run hello.pseudo
```

---

## Contents

- [Features](#features)
- [Installation](#installation)
- [Command-line usage](#command-line-usage)
- [REPL usage](#repl-usage)
- [Python API usage](#python-api-usage)
- [Pseudocode examples](#pseudocode-examples)
- [Strict mode](#strict-mode)
- [Cambridge 2027 compliance checking](#cambridge-2027-compliance-checking)
- [Resource limits](#resource-limits)
- [File handling](#file-handling)
- [User-defined types](#user-defined-types)
- [Procedures and functions](#procedures-and-functions)
- [Object-oriented pseudocode](#object-oriented-pseudocode)
- [Built-in functions](#built-in-functions)
- [Errors](#errors)
- [Development](#development)
- [Project structure](#project-structure)
- [Current limitations](#current-limitations)

---

## Features

### Basic language features

Supported:

- `DECLARE`
- `CONSTANT`
- assignment using `←`
- `INPUT`
- `OUTPUT`
- comments using `//`

### Basic data types

Supported data types:

- `INTEGER`
- `REAL`
- `CHAR`
- `STRING`
- `BOOLEAN`
- `DATE`

### Expressions and operators

Arithmetic operators:

- `+`
- `-`
- `*`
- `/`
- `DIV`
- `MOD`

Comparison operators:

- `=`
- `<>`
- `<`
- `<=`
- `>`
- `>=`

Logic operators:

- `AND`
- `OR`
- `NOT`

String concatenation:

- `&`

`AND` and `OR` use short-circuit evaluation.

### Selection and iteration

Supported control structures:

- `IF ... THEN ... ELSE ... ENDIF`
- `CASE OF ... OTHERWISE ... ENDCASE`
- `FOR ... TO ... STEP ... NEXT`
- `WHILE ... ENDWHILE`
- `REPEAT ... UNTIL`

### Arrays

Supported:

- one-dimensional arrays
- two-dimensional arrays
- explicit lower and upper bounds
- bounds checking
- whole-array assignment with copy semantics

### User-defined types

Supported:

- enumerated types
- pointer types
- set types
- record types
- class/object types

### Procedures and functions

Supported:

- `PROCEDURE`
- `FUNCTION`
- `CALL`
- `RETURN`
- `BYVAL`
- `BYREF`

### File handling

Supported text file operations:

- `OPENFILE ... FOR READ`
- `OPENFILE ... FOR WRITE`
- `OPENFILE ... FOR APPEND`
- `READFILE`
- `WRITEFILE`
- `CLOSEFILE`
- `EOF(...)`

Supported random file operations:

- `OPENFILE ... FOR RANDOM`
- `SEEK`
- `GETRECORD`
- `PUTRECORD`

### Object-oriented subset

Supported:

- `CLASS ... ENDCLASS`
- `PUBLIC`
- `PRIVATE`
- `INHERITS`
- `SUPER`
- constructors using `PROCEDURE NEW(...)`
- object creation using `NEW ClassName(...)`
- method calls using `Object.Method(...)`

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd psei
```

### 2. Create a virtual environment

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install the package

For normal use:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Python requirement:

```text
Python >= 3.10
```

---

## Command-line usage

The package provides two equivalent console commands:

```bash
pseudo
psei
```

### Run a pseudocode file

```bash
pseudo run path/to/program.pseudo
```

Example:

```bash
pseudo run examples/passing/declare_assign_output.pseudo
```

You can also run it as a Python module:

```bash
python -m psei run examples/passing/declare_assign_output.pseudo
```

### Run with strict mode

```bash
pseudo run path/to/program.pseudo --strict
```

Example:

```bash
pseudo run examples/errors/strict_ascii_assignment.pseudo --strict
```

### Check Cambridge 2027 compliance

Check syntax and presentation without executing the program:

```bash
pseudo check path/to/program.pseudo
```

The default profile covers the Cambridge pseudocode guide for examinations in
2027, 2028 and 2029:

```bash
pseudo check path/to/program.pseudo --profile cambridge-2027
```

Use JSON output for editors, CI or other tools:

```bash
pseudo check path/to/program.pseudo --format json
```

Examination line numbers are detected automatically. Override detection when
needed:

```bash
pseudo check path/to/program.pseudo --line-numbers present
pseudo check path/to/program.pseudo --line-numbers absent
```

### CLI error behavior

If a program produces a lexical, parse or runtime error:

- the error message is written to `stderr`
- the process exits with status code `1`

`pseudo check` exits with status code `1` when it reports any error or warning.
A compliant file exits with status code `0`.

---

## REPL usage

Start the REPL:

```bash
pseudo repl
```

Or:

```bash
python -m psei repl
```

Start the REPL in strict mode:

```bash
pseudo repl --strict
```

Available REPL commands:

```text
:help     show help
:vars     show variables in the current runtime
:reset    reset the runtime
:quit     exit
:exit     exit
```

Example session:

```text
pseudo> DECLARE X : INTEGER
pseudo> X ← 10
pseudo> OUTPUT X + 5
15
pseudo> :vars
X : INTEGER = 10
pseudo> :quit
```

For multi-line constructs such as `IF`, `WHILE`, `PROCEDURE`, `FUNCTION` and `CLASS`, the REPL waits until the block is complete.

---

## Python API usage

`psei` can also be used as a Python library.

### Run source code from a string

```python
from psei import run_source

source = """
DECLARE Counter : INTEGER
Counter ← 0
Counter ← Counter + 1
OUTPUT Counter
"""

run_source(source)
```

Output:

```text
1
```

### Capture `OUTPUT`

By default, `OUTPUT` uses Python's `print`. To capture output in tests, create a custom `Runtime`.

```python
from psei import Runtime, run_source

output = []

runtime = Runtime(output_writer=output.append)

run_source("""
OUTPUT "Hello"
OUTPUT "World"
""", runtime)

assert output == ["Hello", "World"]
```

### Provide `INPUT`

```python
from psei import Runtime, run_source

inputs = iter(["41"])
output = []

runtime = Runtime(
    input_provider=lambda: next(inputs),
    output_writer=output.append,
)

run_source("""
DECLARE X : INTEGER

INPUT X
OUTPUT X + 1
""", runtime)

assert output == ["42"]
```

### Run a file

```python
from psei import run_file

run_file("path/to/program.pseudo")
```

`run_file()` uses a local file system rooted at the directory containing the pseudocode file.

---

## Pseudocode examples

### Declaration, assignment and output

```text
DECLARE Counter : INTEGER

Counter ← 0
Counter ← Counter + 1

OUTPUT Counter
```

Output:

```text
1
```

---

### Arrays and loops

```text
DECLARE Values : ARRAY[1:4] OF INTEGER
DECLARE I : INTEGER
DECLARE Total : INTEGER

Total ← 0

FOR I ← 1 TO 4
   Values[I] ← I * 2
   Total ← Total + Values[I]
NEXT I

OUTPUT "Total=", Total
```

Output:

```text
Total=20
```

---

### `IF` statement

```text
DECLARE Score : INTEGER

Score ← 75

IF Score >= 50 THEN
   OUTPUT "Pass"
ELSE
   OUTPUT "Fail"
ENDIF
```

Output:

```text
Pass
```

---

### `CASE` statement

```text
DECLARE Mark : INTEGER

Mark ← 75

CASE OF Mark
   0 TO 49 : OUTPUT "Fail"
   50 TO 69 : OUTPUT "Pass"
   70 TO 100 : OUTPUT "Distinction"
   OTHERWISE : OUTPUT "Invalid"
ENDCASE
```

Output:

```text
Distinction
```

---

### `WHILE` loop

```text
DECLARE Number : INTEGER

Number ← 27

WHILE Number > 9
   Number ← Number - 9
ENDWHILE

OUTPUT Number
```

Output:

```text
9
```

---

### `REPEAT ... UNTIL` loop

```text
DECLARE Number : INTEGER

Number ← 0

REPEAT
   Number ← Number + 1
UNTIL Number = 3

OUTPUT Number
```

Output:

```text
3
```

---

## Strict mode

Strict mode is a runtime guardrail. Use `pseudo check` for Cambridge style and
exam-format validation without executing the program.

Enable strict mode from the command line:

```bash
pseudo run program.pseudo --strict
```

Enable strict mode from Python:

```python
from psei import Runtime, run_source

runtime = Runtime(strict=True)

run_source("""
DECLARE X : INTEGER
X ← 1
""", runtime, strict=True)
```

Strict mode currently enforces:

- assignment must use `←`
- ASCII assignment `<-` is rejected
- variables must be declared before assignment
- identifiers may contain only ASCII letters, digits and `_`
- identifiers must start with an ASCII letter

Non-strict mode currently allows:

- assignment using either `←` or `<-`
- assignment to undeclared variables, creating them with inferred types
- non-ASCII alphabetic characters in identifiers

Both modes still perform core runtime checks, including:

- assignment type checks
- constant immutability
- array bounds checks
- unknown type checks
- record field checks
- enumerated type checks
- file mode checks
- division by zero checks
- Boolean condition checks
- procedure/function arity checks
- function return type checks
- `BYREF` lvalue and type checks

---

## Cambridge 2027 compliance checking

The `cambridge-2027` profile checks source code against the Cambridge
International AS & A Level Computer Science 9618 pseudocode guide for
examinations in 2027, 2028 and 2029.

It performs static checking only. It parses the source but never executes it,
reads pseudocode input or opens pseudocode files.

The profile currently checks:

- upper-case Cambridge keywords and standard function names
- three-space structural indentation and tab usage
- the Cambridge `←` assignment operator
- ASCII identifier characters
- consistent case-insensitive identifier spelling
- lexer and parser compatibility with the formal guide syntax
- examination line numbers, including optional preprocessing before parsing
- uses of documented `psei` operations that are not defined by the guide
- the guide's page 19 `CALL Beep` inconsistency against the formal
  `CALL Beep()` grammar in section 8.1

Diagnostics have stable codes and either `error` or `warning` severity:

| Code | Meaning |
|---|---|
| `C2027-A001` | Non-Cambridge assignment operator |
| `C2027-C001` | Procedure call missing formal parentheses |
| `C2027-I001` | Tab used for indentation |
| `C2027-I002` | Structural indentation differs from three-space nesting |
| `C2027-ID001` | Inconsistent case-insensitive identifier spelling |
| `C2027-ID002` | Non-ASCII identifier character |
| `C2027-K001` | Keyword or standard function name is not upper-case |
| `C2027-L001` | Other lexical error |
| `C2027-N001` | Line numbers do not increase |
| `C2027-P001` | Parser error against the formal syntax |
| `C2027-X001` | Documented `psei` extension outside the guide |

Warnings are compliance failures but do not imply that normal, non-strict
execution would fail. For example, normal execution accepts lower-case
keywords while the compliance profile reports them.

Use the checker from Python:

```python
from psei import check_file, check_source

report = check_source("""
DECLARE Count : INTEGER
Count ← 1
OUTPUT Count
""")

assert report.compliant

file_report = check_file("program.pseudo")

for diagnostic in file_report.diagnostics:
    print(diagnostic.format("program.pseudo"))
```

`line_numbers` can be set to `"auto"`, `"present"` or `"absent"` in the
Python API. The default is `"auto"`.

The checker does not yet perform full compiler-style static analysis. It does
not, for example, prove that every variable is declared and initialized or
that every function path returns a value.

---

## Resource limits

`Runtime` applies conservative execution limits by default to protect the interpreter from runaway programs.

Default limits:

```python
Runtime(
    max_steps=1_000_000,
    max_array_elements=1_000_000,
    max_call_depth=1_000,
    max_output_chars=1_000_000,
)
```

| Option | Purpose |
|---|---|
| `max_steps` | Limits executed statements and loop iterations |
| `max_array_elements` | Limits the number of elements in a single array |
| `max_call_depth` | Limits procedure, function and method call depth |
| `max_output_chars` | Limits the total number of output characters |

Example:

```python
from psei import Runtime, run_source
from psei.errors import PseudoRuntimeError

runtime = Runtime(max_steps=1000)

try:
    run_source("""
WHILE TRUE
ENDWHILE
""", runtime)
except PseudoRuntimeError as error:
    print(error)
```

To disable a specific limit, pass `None`:

```python
runtime = Runtime(max_steps=None)
```

> These limits are not a full security sandbox. If you run untrusted code in production, also use process-level timeouts, memory limits, containers or operating-system sandboxing.

---

## File handling

### File handling with `run_source()`

`run_source()` uses an in-memory file system by default.

This means:

- no real files are created
- execution is deterministic
- tests and REPL usage are easier to manage

Example:

```text
DECLARE Line : STRING

OPENFILE "Log.txt" FOR WRITE
WRITEFILE "Log.txt", "Hello"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR READ
READFILE "Log.txt", Line
OUTPUT Line
CLOSEFILE "Log.txt"
```

---

### File handling with `run_file()`

`run_file()` uses a local file system.

Important behavior:

- relative paths are resolved beside the pseudocode source file
- absolute paths are rejected
- paths escaping the program directory are rejected
- text files are read and written as UTF-8
- random files are persisted as JSON

---

### Text file example

```text
DECLARE LineOfText : STRING

OPENFILE "FileA.txt" FOR WRITE
WRITEFILE "FileA.txt", "First"
WRITEFILE "FileA.txt", "Second"
CLOSEFILE "FileA.txt"

OPENFILE "FileA.txt" FOR READ

WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "FileA.txt"
```

Output:

```text
First
Second
```

---

### Random file example

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord
DECLARE Loaded : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.YearGroup ← 6

OPENFILE "StudentFile.Dat" FOR RANDOM

SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", Pupil

SEEK "StudentFile.Dat", 10
GETRECORD "StudentFile.Dat", Loaded

CLOSEFILE "StudentFile.Dat"

OUTPUT Loaded.LastName, ":", Loaded.YearGroup
```

Output:

```text
Johnson:6
```

Random files can store:

- scalar values
- arrays
- records
- sets

Random files cannot store:

- object instances
- pointer values

---

## User-defined types

### Enumerated types

```text
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE ThisSeason : Season

ThisSeason ← Summer

OUTPUT ThisSeason
```

Output:

```text
Summer
```

Enumerated values are case-insensitive.

If a variable has the same name as an enumerated value, the variable shadows the enumerated value.

---

### Record types

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE FirstName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.FirstName ← "Leroy"
Pupil.YearGroup ← 6

OUTPUT Pupil.LastName, ",", Pupil.FirstName, ",", Pupil.YearGroup
```

Output:

```text
Johnson,Leroy,6
```

---

### Record assignment

Record assignment uses copy semantics. Assigning one record to another does not alias their fields.

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil1 : StudentRecord
DECLARE Pupil2 : StudentRecord

Pupil1.LastName ← "Johnson"
Pupil1.YearGroup ← 6

Pupil2 ← Pupil1

Pupil1.YearGroup ← 7

OUTPUT Pupil2.YearGroup
OUTPUT Pupil1.YearGroup
```

Output:

```text
6
7
```

---

### Arrays of records

```text
TYPE StudentRecord
   DECLARE Name : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Form : ARRAY[1:2] OF StudentRecord

Form[1].Name ← "Ali"
Form[1].YearGroup ← 12

Form[2].Name ← "Mei"
Form[2].YearGroup ← 11

OUTPUT Form[1].Name, ":", Form[1].YearGroup
OUTPUT Form[2].Name, ":", Form[2].YearGroup
```

Output:

```text
Ali:12
Mei:11
```

---

### Pointer types

```text
TYPE TIntPointer = ^INTEGER

DECLARE X : INTEGER
DECLARE P : TIntPointer

X ← 10
P ← ^X

OUTPUT P^

P^ ← 20

OUTPUT X
```

Output:

```text
10
20
```

---

### Set types

```text
TYPE LetterSet = SET OF CHAR

DEFINE Vowels ('A','E','I','O','U') : LetterSet

OUTPUT Vowels
```

Output:

```text
{A, E, I, O, U}
```

`DEFINE` creates a constant set. Use `DECLARE` when the set needs to be
changed:

```text
DECLARE Selected : LetterSet

Selected ← Vowels
CALL SETADD(Selected, 'Y')
CALL SETREMOVE(Selected, 'A')
```

Set assignment uses copy semantics. The operations below return a new set and
do not change either operand:

```text
Combined ← UNION(SetA, SetB)
Shared ← INTERSECTION(SetA, SetB)
OnlyA ← DIFFERENCE(SetA, SetB)
EitherButNotBoth ← SYMMETRICDIFFERENCE(SetA, SetB)
```

Set query functions:

| Function | Result |
|---|---|
| `CONTAINS(SetValue, Element)` | Whether the element belongs to the set |
| `CARDINALITY(SetValue)` | Number of distinct elements |
| `ISEMPTY(SetValue)` | Whether the set is empty |
| `ISSUBSET(SetA, SetB)` | Whether every element of `SetA` is in `SetB` |
| `ISPROPERSUBSET(SetA, SetB)` | Whether `SetA` is a strict subset of `SetB` |
| `ISSUPERSET(SetA, SetB)` | Whether `SetA` contains every element of `SetB` |
| `ISPROPERSUPERSET(SetA, SetB)` | Whether `SetA` is a strict superset of `SetB` |
| `ISDISJOINT(SetA, SetB)` | Whether the sets have no elements in common |

Set mutation procedures:

| Procedure | Effect |
|---|---|
| `CALL SETADD(SetValue, Element)` | Adds an element; existing elements are unchanged |
| `CALL SETREMOVE(SetValue, Element)` | Removes an element, or raises an error if absent |
| `CALL SETDISCARD(SetValue, Element)` | Removes an element if present |
| `CALL SETCLEAR(SetValue)` | Removes all elements |

The Cambridge pseudocode guide does not define standard notation for these
operations. These named functions and procedures are a documented `psei`
extension.

---

## Procedures and functions

### Procedure without parameters

```text
PROCEDURE Hello()
   OUTPUT "Hello"
ENDPROCEDURE

CALL Hello()
```

Output:

```text
Hello
```

---

### Procedure with parameters

```text
PROCEDURE Square(Size : INTEGER)
   FOR Side ← 1 TO 4
      OUTPUT "Side length=", Size
   NEXT Side
ENDPROCEDURE

CALL Square(100)
```

---

### `BYVAL`

Parameters are passed by value by default.

```text
PROCEDURE AddOne(X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER

A ← 5

CALL AddOne(A)

OUTPUT A
```

Output:

```text
5
```

---

### `BYREF`

`BYREF` parameters modify the caller's variable, array element, record field, object property or pointer dereference.

```text
PROCEDURE AddOne(BYREF X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER

A ← 5

CALL AddOne(A)

OUTPUT A
```

Output:

```text
6
```

The current passing mode continues across comma-separated parameters until another `BYVAL` or `BYREF` keyword appears.

```text
PROCEDURE Swap(BYREF X : INTEGER, Y : INTEGER)
   DECLARE Temp : INTEGER

   Temp ← X
   X ← Y
   Y ← Temp
ENDPROCEDURE
```

In the example above, both `X` and `Y` are passed by reference.

To reset the mode explicitly:

```text
PROCEDURE Test(BYREF X : INTEGER, BYVAL Y : INTEGER)
   X ← 10
   Y ← 20
ENDPROCEDURE
```

---

### Functions

```text
FUNCTION Max(Number1 : INTEGER, Number2 : INTEGER) RETURNS INTEGER
   IF Number1 > Number2 THEN
      RETURN Number1
   ELSE
      RETURN Number2
   ENDIF
ENDFUNCTION

OUTPUT "Maximum=", Max(10, 20)
```

Output:

```text
Maximum=20
```

Function calls must be used as part of an expression.

Valid:

```text
OUTPUT Max(10, 20)
X ← Max(10, 20)
```

Invalid:

```text
Max(10, 20)
```

Function parameters cannot be passed `BYREF`.

---

## Object-oriented pseudocode

### Basic class

```text
CLASS Player
   PRIVATE Attempts : INTEGER

   Attempts ← 3

   PUBLIC PROCEDURE SetAttempts(Number : INTEGER)
      Attempts ← Number
   ENDPROCEDURE

   PUBLIC FUNCTION GetAttempts() RETURNS INTEGER
      RETURN Attempts
   ENDFUNCTION
ENDCLASS

DECLARE P : Player

P ← NEW Player()

OUTPUT P.GetAttempts()

P.SetAttempts(5)

OUTPUT P.GetAttempts()
```

Output:

```text
3
5
```

---

### Constructors

Constructors are procedures named `NEW`.

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

MyPet ← NEW Pet("Kitty")

OUTPUT MyPet.GetName()
```

Output:

```text
Kitty
```

---

### Inheritance and `SUPER`

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

Output:

```text
Kitty
Shorthaired
```

---

### `PUBLIC` and `PRIVATE`

`PUBLIC` members can be accessed from outside the object.

`PRIVATE` members can only be accessed from methods or initializers of the class that declares them.

Example:

```text
CLASS Account
   PRIVATE Balance : INTEGER

   PUBLIC PROCEDURE NEW(StartBalance : INTEGER)
      Balance ← StartBalance
   ENDPROCEDURE

   PUBLIC FUNCTION GetBalance() RETURNS INTEGER
      RETURN Balance
   ENDFUNCTION
ENDCLASS

A ← NEW Account(100)

OUTPUT A.GetBalance()
```

Output:

```text
100
```

This external access raises a runtime error:

```text
OUTPUT A.Balance
```

---

## Built-in functions

Supported built-in functions:

| Function | Description |
|---|---|
| `RIGHT(ThisString, x)` | Returns the rightmost `x` characters |
| `MID(ThisString, x, y)` | Returns a substring of length `y` starting at one-based position `x` |
| `LENGTH(ThisString)` | Returns the length of a string |
| `LCASE(ThisChar)` | Converts ASCII uppercase letters to lowercase; other characters are unchanged |
| `UCASE(ThisChar)` | Converts ASCII lowercase letters to uppercase; other characters are unchanged |
| `INT(x)` | Returns the integer part of a number |
| `RAND(x)` | Returns a random `REAL` in the range `[0, x)` |
| `EOF(file)` | Returns whether an open text file has reached end-of-file |
| `UNION(SetA, SetB)` | Returns the union of two sets |
| `INTERSECTION(SetA, SetB)` | Returns the intersection of two sets |
| `DIFFERENCE(SetA, SetB)` | Returns the elements in `SetA` but not `SetB` |
| `SYMMETRICDIFFERENCE(SetA, SetB)` | Returns elements in exactly one operand |
| `CONTAINS(SetValue, Element)` | Tests set membership |
| `CARDINALITY(SetValue)` | Returns the number of elements |
| `ISEMPTY(SetValue)` | Tests whether a set is empty |
| `ISSUBSET(SetA, SetB)` | Tests subset inclusion |
| `ISPROPERSUBSET(SetA, SetB)` | Tests strict subset inclusion |
| `ISSUPERSET(SetA, SetB)` | Tests superset inclusion |
| `ISPROPERSUPERSET(SetA, SetB)` | Tests strict superset inclusion |
| `ISDISJOINT(SetA, SetB)` | Tests whether two sets are disjoint |

Example:

```text
OUTPUT RIGHT("ABCDEFGH", 3)
OUTPUT MID("ABCDEFGH", 2, 3)
OUTPUT LENGTH("Happy Days")
OUTPUT UCASE('h')
OUTPUT LCASE('W')
OUTPUT INT(27.5415)
```

Output:

```text
FGH
BCD
10
H
w
27
```

---

## Errors

Error classes are available from `psei.errors`:

```python
from psei.errors import (
    PseudoError,
    LexError,
    ParseError,
    IncompleteInput,
    PseudoRuntimeError,
)
```

| Error type | Meaning |
|---|---|
| `LexError` | Lexical error, such as an invalid character or malformed literal |
| `ParseError` | Syntax error |
| `IncompleteInput` | Used by the REPL when a block is incomplete |
| `PseudoRuntimeError` | Runtime error, such as type mismatch, division by zero or array bounds error |

Example:

```python
from psei import run_source
from psei.errors import PseudoError

try:
    run_source("""
DECLARE X : INTEGER
X ← "not an integer"
""")
except PseudoError as error:
    print(error)
```

---

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest -q
```

The repository includes example programs:

```text
examples/passing/
examples/errors/
```

`examples/passing/` contains programs that should run successfully.

Each passing example has a matching `.out` file containing expected output.

`examples/errors/` contains programs that should raise errors.

`examples/errors/manifest.json` records the expected error type for each error example.

---

## Project structure

```text
psei/
├── examples/
│   ├── passing/
│   └── errors/
├── src/
│   └── psei/
│       ├── lexer.py
│       ├── parser.py
│       ├── ast_nodes.py
│       ├── compliance.py
│       ├── interpreter.py
│       ├── runner.py
│       ├── cli.py
│       ├── repl.py
│       ├── runtime/
│       │   ├── core.py
│       │   ├── environment.py
│       │   ├── files.py
│       │   ├── oop.py
│       │   ├── serialization.py
│       │   ├── types.py
│       │   └── values.py
│       ├── tokens.py
│       └── values.py
├── tests/
├── pyproject.toml
└── README.md
```

Main modules:

| File or directory | Purpose |
|---|---|
| `lexer.py` | Lexical analysis |
| `parser.py` | Parsing and AST construction |
| `ast_nodes.py` | AST node definitions |
| `compliance.py` | Cambridge compliance profiles and diagnostics |
| `interpreter.py` | AST execution |
| `runtime/core.py` | Runtime object, scopes and limits |
| `runtime/environment.py` | Variables, constants and references |
| `runtime/types.py` | Type system, coercion and cloning |
| `runtime/files.py` | Text and random file abstractions |
| `runtime/oop.py` | Class and object runtime structures |
| `runner.py` | `run_source()` and `run_file()` |
| `cli.py` | Command-line entry point |
| `repl.py` | Interactive REPL |

---

## Current limitations

`psei` implements a practical Cambridge-style pseudocode subset and a
Cambridge 2027-2029 source compliance profile. It is not an official Cambridge
tool or a complete programming language implementation.

Not fully implemented:

- the full ADT library mentioned by the Cambridge syllabus, including:
  - stack
  - queue
  - linked list
  - dictionary
  - binary tree
- presentation checks that cannot be inferred reliably from plain text, such
  as font choice and the alignment of wrapped continuation lines
- a prescriptive camelCase/PascalCase identifier-name checker; the current
  profile checks ASCII characters and consistent case-insensitive spelling
- full compiler-style static analysis
- process-level sandboxing

If you execute untrusted code, consider using:

- subprocess timeouts
- operating-system memory limits
- containers
- API-level request limits
- process isolation

---

## Minimal example

Create `hello.pseudo`:

```text
DECLARE Name : STRING

Name ← "Cambridge pseudocode"

OUTPUT "Hello, ", Name
```

Run it:

```bash
pseudo run hello.pseudo
```

Output:

```text
Hello, Cambridge pseudocode
```
