#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()

if not (ROOT / "interpreter").is_dir():
    raise SystemExit("Run this script from the repository root.")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)

    if not text.endswith("\n"):
        text += "\n"

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {rel}")


def replace_exact(rel: str, old: str, new: str, label: str) -> None:
    text = read(rel)

    if old in text:
        text = text.replace(old, new, 1)
        write(rel, text)
        print(f"patched {label}")
        return

    if new in text:
        print(f"skipped {label}: already applied")
        return

    raise SystemExit(
        f"Could not patch {label} in {rel}.\n"
        f"Expected old snippet was not found."
    )
