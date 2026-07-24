from __future__ import annotations

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .runtime import Runtime


def run_source(
    source: str,
    runtime: Runtime | None = None,
    *,
    strict: bool | None = None,
) -> Runtime:
    if runtime is None:
        runtime = Runtime(strict=bool(strict))

    if strict is None:
        strict = runtime.strict

    tokens = Lexer(source, strict=strict).scan_tokens()
    program = Parser(tokens).parse_program()
    Interpreter(runtime).execute_program(program)

    return runtime


def run_file(path: str, *, strict: bool = False):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    runtime = Runtime(strict=strict)
    run_source(source, runtime, strict=strict)
