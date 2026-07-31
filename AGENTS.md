# AGENTS.md

## Scope

These instructions apply to the entire repository.

`psei` is a lightweight interpreter for Cambridge International AS & A Level
Computer Science 9618-style pseudocode. It is an independent teaching tool,
not an official Cambridge product and not yet a complete exam-format validator.

When the local file
`721401-2027-2029-pseudocode-guide.pdf` is available, use it as the primary
reference for Cambridge pseudocode syntax for examinations in 2027, 2028 and
2029. Use `README.md` for the currently documented `psei` behavior. If the two
differ, identify whether the behavior is:

- required Cambridge syntax;
- a deliberate compatibility allowance; or
- a documented `psei` extension.

Do not silently present a `psei` extension as official Cambridge syntax.

## Repository Map

- `src/psei/lexer.py`: source scanning, literals, identifiers and keywords.
- `src/psei/tokens.py`: token definitions and keyword table.
- `src/psei/ast_nodes.py`: AST node definitions.
- `src/psei/compliance.py`: Cambridge compliance profiles and diagnostics.
- `src/psei/parser.py`: grammar and AST construction.
- `src/psei/interpreter.py`: statement execution and expression evaluation.
- `src/psei/runtime/core.py`: runtime state, scopes, type registration and
  resource limits.
- `src/psei/runtime/environment.py`: variables, constants and references.
- `src/psei/runtime/types.py`: type resolution, checking, coercion and cloning.
- `src/psei/runtime/files.py`: in-memory and local file-system behavior.
- `src/psei/runtime/serialization.py`: random-file persistence format.
- `src/psei/runtime/oop.py`: class, method and object runtime structures.
- `src/psei/runner.py`: `run_source()` and `run_file()` entry points.
- `src/psei/cli.py`: command-line interface.
- `src/psei/repl.py`: interactive REPL.
- `tests/`: focused unit and regression tests.
- `examples/passing/`: executable examples with matching `.out` golden files.
- `examples/errors/`: failing examples described by `manifest.json`.

## Setup and Validation

Use Python 3.10 through 3.14. The default local development version is recorded
in `.python-version`.

```bash
uv sync --locked
uv run --locked pytest -q
```

In the Codex desktop sandbox, `~/.cache/uv` may be read-only. Put the uv cache
in `/tmp` and use copy mode:

```bash
UV_CACHE_DIR=/tmp/psei-uv-cache UV_LINK_MODE=copy uv sync --locked
UV_CACHE_DIR=/tmp/psei-uv-cache UV_LINK_MODE=copy uv run --locked pytest -q
```

The first synchronization may require sandbox network approval to download
locked packages from PyPI.

If pytest output capture is broken in that environment, add `-s`:

```bash
UV_CACHE_DIR=/tmp/psei-uv-cache UV_LINK_MODE=copy uv run --locked pytest -q -s
```

Run the narrowest relevant tests while iterating, then run the complete suite
before handing off a change. Useful targets include:

```bash
uv run --locked pytest -q tests/test_lexer_and_runtime.py
uv run --locked pytest -q tests/test_compliance.py
uv run --locked pytest -q tests/test_cambridge_2027_guide.py
uv run --locked pytest -q tests/test_user_defined_types.py
uv run --locked pytest -q tests/test_test_procedures_and_functions.py
uv run --locked pytest -q tests/test_file_handling.py
uv run --locked pytest -q tests/test_oop.py
uv run --locked pytest -q tests/test_set_operations.py
uv run --locked pytest -q tests/test_regressions.py
```

CI runs the full suite on Python 3.10 through 3.14. Keep changes compatible with
the whole declared range.

## Change Workflow

1. Inspect the relevant lexer, parser, interpreter and runtime path before
   editing. Language changes often cross several layers.
2. Add or update focused tests alongside every behavior change or bug fix.
3. Add a regression test for every fixed parser or runtime defect.
4. Run targeted tests, then the full test suite.
5. Update `README.md` for user-visible syntax, semantics, CLI or API changes.
6. Update `CHANGELOG.md` under `Unreleased` for user-visible changes.
7. Leave generated files, caches, temporary PDF renders and local data files
   out of the repository.

Do not rewrite unrelated code, generated outputs or user changes. Preserve the
existing public Python API unless the task explicitly authorizes a breaking
change.

## Language Invariants

Preserve these rules unless a requested language change explicitly supersedes
them:

- Keywords and identifiers are interpreted case-insensitively.
- Strict mode requires declared variables, ASCII identifiers and the `←`
  assignment operator. Non-strict mode also accepts `<-`, inferred variables
  and non-ASCII alphabetic identifiers.
- Do not make non-strict compatibility behavior stricter by accident.
- The scalar types are `INTEGER`, `REAL`, `CHAR`, `STRING`, `BOOLEAN` and
  `DATE`.
- Array bounds are explicit and inclusive. Whole-array assignment uses copy
  semantics.
- Records and sets use copy semantics. Pointer assignment preserves reference
  behavior.
- Constants are immutable. `DEFINE` creates a constant set.
- Conditions for `IF`, `WHILE` and `REPEAT` must evaluate to `BOOLEAN`.
- `AND` and `OR` short-circuit.
- `/` returns a `REAL`; `DIV` is integer division; `MOD` is the remainder.
- `MID` uses one-based positions.
- Procedure calls are statements and use `CALL`; functions are expressions.
- Function parameters cannot be `BYREF`.
- `BYREF` must reference a writable, type-compatible lvalue. Variables, array
  elements, record fields, object properties and pointer dereferences may be
  valid lvalues.
- `RETURN` exits a function immediately and cannot be used to return a value
  from a procedure.
- Object access control, constructor behavior, inheritance and `SUPER` must be
  checked at runtime.
- `run_source()` uses the in-memory file system by default. `run_file()` uses a
  local file system rooted beside the pseudocode source and must reject path
  escape and absolute paths.
- Random-file serialization must remain deterministic and versioned. Do not
  persist object instances or live pointer references.
- Execution must continue to honor configured step, array-size, call-depth and
  output limits.

Use the existing identifier normalization, type comparison, cloning, reference
and error helpers rather than creating parallel semantics.

## Parser and Runtime Changes

For new syntax, normally update all applicable layers:

1. tokens and keywords;
2. lexer behavior;
3. AST nodes;
4. parser grammar and incomplete-input handling;
5. interpreter execution;
6. runtime types or services;
7. tests, examples and documentation.

Keep parsing separate from execution. The parser should build explicit AST
nodes and report `ParseError` or `IncompleteInput`; it should not perform
runtime mutation.

Preserve source spans and useful line/column diagnostics. Raise the project
error types from `src/psei/errors.py` rather than leaking incidental Python
exceptions.

Do not add permissive syntax solely to accommodate one inconsistent guide
example without deciding whether it belongs in normal mode, a compatibility
profile or an exam-format preprocessing layer. In particular, the guide's
formal procedure-call grammar uses parentheses even though one CASE example
shows `CALL Beep` without them.

## Testing Expectations

Test both successful behavior and the closest invalid forms.

- Lexer changes need token, malformed-input and strict-mode tests.
- Parser changes need valid syntax, incomplete blocks and invalid syntax tests.
- Type changes need declaration, assignment, comparison, cloning and error
  tests.
- Control-flow changes need boundary cases and resource-limit behavior.
- `BYREF` changes need writable and non-writable lvalue cases.
- File changes need both in-memory and local-file-system coverage where
  applicable.
- OOP changes need access control, inheritance and method/procedure/function
  distinction tests.
- Serialization changes need round-trip and invalid-data tests.

For `examples/passing/<name>.pseudo`, maintain the corresponding
`examples/passing/<name>.out`. For a new error example, add its expected error
class to `examples/errors/manifest.json`.

Avoid nondeterministic tests. Inject or seed the runtime random-number generator
when exact random output matters, and use `tmp_path` for local file tests.

## Python Style

- Follow the existing formatting and naming style.
- Prefer small, focused helpers over duplicating interpreter logic.
- Add type annotations to new public functions and non-obvious internal APIs.
- Avoid broad exception handling.
- Avoid mutable module-level state.
- Keep user-facing error messages specific and stable enough for tests.
- There is currently no configured formatter, linter or type checker. Do not
  introduce one as an incidental part of an unrelated change.

## Known Gaps and Direction

The main known gaps are:

- presentation details that cannot be inferred reliably from plain text,
  including font choice and wrapped continuation-line alignment;
- a prescriptive camelCase/PascalCase identifier-name checker beyond the
  current ASCII and consistent-spelling rules;
- the syllabus-level ADTs stack, queue, linked list, dictionary and binary
  tree;
- compiler-style static analysis.

Keep presentation rules in `src/psei/compliance.py` rather than making the
execution lexer depend on indentation. Because the Cambridge guide does not
define standard operations for all ADTs, document ADT interfaces as `psei`
teaching-library extensions unless a primary source defines otherwise.

## Definition of Done

A change is complete when:

- behavior is covered by focused tests;
- the complete test suite passes;
- Cambridge behavior and `psei` extensions are clearly distinguished;
- user-visible changes are documented;
- relevant examples and golden outputs are synchronized;
- no temporary or generated artifacts remain; and
- the final diff contains only intentional changes.
