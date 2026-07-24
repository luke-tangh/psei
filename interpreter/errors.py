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
