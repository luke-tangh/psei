from __future__ import annotations

import argparse
import json
import sys

from .analyzer import analyze_file
from .compliance import (
    CAMBRIDGE_2027,
    LINE_NUMBER_MODES,
    SUPPORTED_PROFILES,
    check_file,
)
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

    analyze_cmd = sub.add_parser(
        "analyze",
        help="statically analyze a pseudocode file without executing it",
    )
    analyze_cmd.add_argument("file")
    analyze_cmd.add_argument("--strict", action="store_true")
    analyze_cmd.add_argument(
        "--recommendations",
        action="store_true",
        help="also report reads before explicit initialization",
    )
    analyze_cmd.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
    )

    check_cmd = sub.add_parser(
        "check",
        help="check a pseudocode file against a compliance profile",
    )
    check_cmd.add_argument("file")
    check_cmd.add_argument(
        "--profile",
        choices=SUPPORTED_PROFILES,
        default=CAMBRIDGE_2027,
    )
    check_cmd.add_argument(
        "--line-numbers",
        choices=LINE_NUMBER_MODES,
        default="auto",
        help="how to treat examination line numbers (default: auto)",
    )
    check_cmd.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
    )

    repl_cmd = sub.add_parser("repl", help="start REPL")
    repl_cmd.add_argument("--strict", action="store_true")

    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            run_file(args.file, strict=args.strict)

        elif args.command == "analyze":
            report = analyze_file(
                args.file,
                strict=args.strict,
                recommendations=args.recommendations,
            )

            if args.output_format == "json":
                payload = {"file": args.file, **report.to_dict()}
                print(json.dumps(payload, indent=2))
            elif report.diagnostics:
                for diagnostic in report.diagnostics:
                    print(diagnostic.format(args.file))
            else:
                print(f"{args.file}: no semantic issues found")

            if not report.valid:
                sys.exit(1)

        elif args.command == "check":
            report = check_file(
                args.file,
                profile=args.profile,
                line_numbers=args.line_numbers,
            )

            if args.output_format == "json":
                payload = {"file": args.file, **report.to_dict()}
                print(json.dumps(payload, indent=2))
            elif report.compliant:
                print(
                    f"{args.file}: compliant with profile "
                    f"{report.profile}"
                )
            else:
                for diagnostic in report.diagnostics:
                    print(diagnostic.format(args.file))

            if not report.compliant:
                sys.exit(1)

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
