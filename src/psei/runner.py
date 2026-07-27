from __future__ import annotations

from pathlib import Path

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .runtime import LocalFileSystem, Runtime


def run_source(
    source: str,
    runtime: Runtime | None = None,
    *,
    strict: bool | None = None,
) -> Runtime:
    if runtime is None:
        runtime = Runtime(strict=bool(strict))

    elif strict is not None and strict != runtime.strict:
        raise ValueError(
            "strict argument must match runtime.strict when runtime is provided"
        )

    if strict is None:
        strict = runtime.strict

    tokens = Lexer(source, strict=strict).scan_tokens()
    program = Parser(tokens).parse_program()
    Interpreter(runtime).execute_program(program)

    return runtime


def run_file(path: str, *, strict: bool = False):
    program_path = Path(path)

    with program_path.open("r", encoding="utf-8") as f:
        source = f.read()

    runtime = Runtime(
        strict=strict,
        file_system=LocalFileSystem(program_path.resolve().parent),
    )
    run_source(source, runtime, strict=strict)
