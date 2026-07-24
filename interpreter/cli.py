from __future__ import annotations

import argparse
import sys

from .errors import PseudoError
from .repl import start_repl
from .runner import run_file


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pseudo",
        description="Minimal Cambridge-style pseudocode interpreter",
    )

    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="run a pseudocode file")
    run_cmd.add_argument("file")
    run_cmd.add_argument("--strict", action="store_true")

    repl_cmd = sub.add_parser("repl", help="start REPL")
    repl_cmd.add_argument("--strict", action="store_true")

    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            run_file(args.file, strict=args.strict)

        elif args.command == "repl" or args.command is None:
            strict = getattr(args, "strict", False)
            start_repl(strict=strict)

        else:
            parser.print_help()

    except PseudoError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    except OSError as e:
        print(f"File error: {e}", file=sys.stderr)
        sys.exit(1)
