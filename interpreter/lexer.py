from __future__ import annotations

import re

from .errors import LexError
from .tokens import KEYWORDS, T, Token
from .values import Char, make_date


class Lexer:
    CHAR_QUOTES = {"'", "ꞌ", "‘", "’"}
    MINUS_CHARS = {"-", "–", "−"}

    def __init__(self, source: str, *, strict: bool = False):
        self.source = source
        self.strict = strict
        self.tokens: list[Token] = []

        self.start = 0
        self.current = 0

        self.line = 1
        self.col = 1
        self.token_line = 1
        self.token_col = 1

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.token_line = self.line
            self.token_col = self.col

            c = self.advance()

            if c in " \t\r":
                continue

            if c == "\n":
                self.add_token(T.NEWLINE)
                continue

            if c == "/" and self.match("/"):
                while not self.is_at_end() and self.peek() != "\n":
                    self.advance()
                continue

            if c == '"':
                self.scan_string()
                continue

            if c in self.CHAR_QUOTES:
                self.scan_char()
                continue

            if c.isdigit():
                self.scan_number_or_date()
                continue

            if self.is_identifier_start(c):
                self.scan_identifier()
                continue

            if c == "←":
                self.add_token(T.ASSIGN)

            elif c == "<":
                if self.match("-"):
                    if self.strict:
                        self.error("Use ← for assignment in strict mode, not <-")
                    self.add_token(T.ASSIGN)
                elif self.match(">"):
                    self.add_token(T.NOT_EQUAL)
                elif self.match("="):
                    self.add_token(T.LESS_EQUAL)
                else:
                    self.add_token(T.LESS)

            elif c == ">":
                if self.match("="):
                    self.add_token(T.GREATER_EQUAL)
                else:
                    self.add_token(T.GREATER)

            elif c == "=":
                self.add_token(T.EQUAL)

            elif c == "+":
                self.add_token(T.PLUS)

            elif c in self.MINUS_CHARS:
                self.add_token(T.MINUS)

            elif c == "*":
                self.add_token(T.STAR)

            elif c == "/":
                self.add_token(T.SLASH)

            elif c == "&":
                self.add_token(T.AMP)

            elif c == "(":
                self.add_token(T.LPAREN)

            elif c == ")":
                self.add_token(T.RPAREN)

            elif c == "[":
                self.add_token(T.LBRACKET)

            elif c == "]":
                self.add_token(T.RBRACKET)

            elif c == ",":
                self.add_token(T.COMMA)

            elif c == ":":
                self.add_token(T.COLON)

            elif c == ".":
                self.add_token(T.DOT)

            else:
                self.error(f"Unexpected character {c!r}")

        self.tokens.append(Token(T.EOF, "", None, self.line, self.col))
        return self.tokens

    def scan_string(self):
        value = ""

        while not self.is_at_end():
            c = self.peek()

            if c == '"':
                break

            if c == "\n":
                self.error("Unterminated string literal")

            if c == "\\":
                self.advance()

                if self.is_at_end():
                    self.error("Unterminated string escape")

                esc = self.advance()
                mapping = {
                    "n": "\n",
                    "t": "\t",
                    '"': '"',
                    "\\": "\\",
                }
                value += mapping.get(esc, esc)
            else:
                value += self.advance()

        if self.is_at_end():
            self.error("Unterminated string literal")

        self.advance()
        self.add_token(T.STRING_LIT, value)

    def scan_char(self):
        if self.is_at_end():
            self.error("Unterminated CHAR literal")

        if self.peek() == "\n":
            self.error("Unterminated CHAR literal")

        ch = self.advance()

        if ch in self.CHAR_QUOTES:
            self.error("CHAR literal must contain exactly one character")

        if self.is_at_end() or self.peek() not in self.CHAR_QUOTES:
            self.error("CHAR literal must contain exactly one character")

        self.advance()
        self.add_token(T.CHAR_LIT, Char(ch))

    def scan_number_or_date(self):
        rest = self.source[self.start:]
        match = re.match(r"\d{1,2}/\d{1,2}/\d{4}(?![\d/])", rest)

        if match:
            text = match.group(0)

            while self.current < self.start + len(text):
                self.advance()

            day, month, year = text.split("/")

            try:
                value = make_date(int(day), int(month), int(year))
            except Exception:
                self.error(f"Invalid DATE literal: {text}")

            self.add_token(T.DATE_LIT, value)
            return

        while self.peek().isdigit():
            self.advance()

        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()

            while self.peek().isdigit():
                self.advance()

            text = self.source[self.start:self.current]
            self.add_token(T.REAL_LIT, float(text))
        else:
            text = self.source[self.start:self.current]
            self.add_token(T.INT_LIT, int(text))

    def scan_identifier(self):
        while self.is_identifier_part(self.peek()):
            self.advance()

        text = self.source[self.start:self.current]
        upper = text.upper()

        if upper == "TRUE":
            self.add_token(T.BOOL_LIT, True)
        elif upper == "FALSE":
            self.add_token(T.BOOL_LIT, False)
        elif upper in KEYWORDS:
            self.add_token(KEYWORDS[upper])
        else:
            self.add_token(T.IDENT)

    def add_token(self, type_: str, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(
            Token(type_, text, literal, self.token_line, self.token_col)
        )

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1

        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        return c

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.advance()
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"

        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"

        return self.source[self.current + 1]

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    @staticmethod
    def is_identifier_start(c: str) -> bool:
        return c.isalpha()

    @staticmethod
    def is_identifier_part(c: str) -> bool:
        return c.isalpha() or c.isdigit() or c == "_"

    def error(self, message: str):
        raise LexError(
            f"LexError at line {self.token_line}, "
            f"column {self.token_col}: {message}"
        )
