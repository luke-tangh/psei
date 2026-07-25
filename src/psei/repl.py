from __future__ import annotations

import sys

from .errors import IncompleteInput, PseudoError
from .runner import run_source
from .runtime import Runtime


def start_repl(*, strict: bool = False):
    print("Cambridge pseudocode REPL prototype")
    print("Type :help for commands. Type :quit to exit.")

    runtime = Runtime(strict=strict)
    buffer: list[str] = []

    while True:
        prompt = "pseudo> " if not buffer else "... "

        try:
            line = input(prompt)
        except EOFError:
            print()
            break

        stripped = line.strip()

        if not buffer and stripped.startswith(":"):
            if stripped in {":quit", ":exit"}:
                break

            if stripped == ":help":
                print(":help    show help")
                print(":vars    show variables")
                print(":reset   reset runtime")
                print(":quit    exit")
                continue

            if stripped == ":vars":
                print(runtime.env.dump())
                continue

            if stripped == ":reset":
                runtime = Runtime(strict=strict)
                print("Runtime reset.")
                continue

            print(f"Unknown REPL command: {stripped}")
            continue

        if not buffer and stripped == "":
            continue

        buffer.append(line)
        source = "\n".join(buffer)

        try:
            run_source(source, runtime, strict=strict)
            buffer.clear()

        except IncompleteInput:
            continue

        except PseudoError as e:
            print(e, file=sys.stderr)
            buffer.clear()
