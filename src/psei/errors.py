from __future__ import annotations


class PseudoError(Exception):
    """Base class for all interpreter errors."""


class LexError(PseudoError):
    """Raised during lexical analysis."""


class ParseError(PseudoError):
    """Raised during parsing."""


class IncompleteInput(ParseError):
    """Raised by the parser when REPL input appears incomplete."""


class PseudoRuntimeError(PseudoError):
    """Raised during execution."""

    def __init__(
        self,
        message: str,
        *,
        line: int | None = None,
        col: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col

    def with_location(self, line: int, col: int) -> PseudoRuntimeError:
        if self.line is not None:
            return self

        return PseudoRuntimeError(self.message, line=line, col=col)

    def __str__(self) -> str:
        if self.line is not None and self.col is not None:
            return (
                f"RuntimeError at line {self.line}, "
                f"column {self.col}: {self.message}"
            )

        return self.message
