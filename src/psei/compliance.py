from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import LexError, ParseError
from .lexer import Lexer
from .parser import Parser
from .tokens import KEYWORDS, T, Token


CAMBRIDGE_2027 = "cambridge-2027"
SUPPORTED_PROFILES = (CAMBRIDGE_2027,)
LINE_NUMBER_MODES = ("auto", "present", "absent")

_KEYWORD_TYPES = frozenset(KEYWORDS.values())
_STANDARD_CALLABLES = frozenset(
    {
        "EOF",
        "INT",
        "LCASE",
        "LENGTH",
        "MID",
        "RAND",
        "RIGHT",
        "UCASE",
    }
)
_PSEI_EXTENSION_CALLABLES = frozenset(
    {
        "CARDINALITY",
        "CONTAINS",
        "DIFFERENCE",
        "INTERSECTION",
        "ISDISJOINT",
        "ISEMPTY",
        "ISPROPERSUBSET",
        "ISPROPERSUPERSET",
        "ISSUBSET",
        "ISSUPERSET",
        "SETADD",
        "SETCLEAR",
        "SETDISCARD",
        "SETREMOVE",
        "SYMMETRICDIFFERENCE",
        "UNION",
    }
)
_OPENING_WORDS = frozenset(
    {
        "CASE",
        "CLASS",
        "FOR",
        "FUNCTION",
        "IF",
        "PROCEDURE",
        "REPEAT",
        "WHILE",
    }
)
_CLOSING_WORDS = frozenset(
    {
        "ENDCASE",
        "ENDCLASS",
        "ENDFUNCTION",
        "ENDIF",
        "ENDPROCEDURE",
        "ENDTYPE",
        "ENDWHILE",
        "NEXT",
        "UNTIL",
    }
)
_NUMBERED_LINE_RE = re.compile(
    r"^(?P<leading>[ \t]*)(?P<number>\d+)(?P<gap>[ \t]+)(?P<body>.*)$"
)
_BARE_CALL_RE = re.compile(
    r"\bCALL[ \t]+(?P<name>[A-Za-z][A-Za-z0-9_]*)(?P<trailing>[ \t]*)$",
    re.IGNORECASE,
)
_LOCATION_RE = re.compile(
    r"^(?:LexError|ParseError) at line (?P<line>\d+), "
    r"column (?P<col>\d+): (?P<message>.*)$"
)


@dataclass(frozen=True)
class ComplianceDiagnostic:
    code: str
    severity: str
    message: str
    line: int
    col: int

    def format(self, filename: str | Path | None = None) -> str:
        location = f"{self.line}:{self.col}"

        if filename is not None:
            location = f"{filename}:{location}"

        return (
            f"{location}: {self.severity} {self.code}: "
            f"{self.message}"
        )

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceReport:
    profile: str
    diagnostics: tuple[ComplianceDiagnostic, ...]
    normalized_source: str
    line_numbers_detected: bool

    @property
    def compliant(self) -> bool:
        return not self.diagnostics

    @property
    def has_errors(self) -> bool:
        return any(item.severity == "error" for item in self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "compliant": self.compliant,
            "line_numbers_detected": self.line_numbers_detected,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def check_file(
    path: str | Path,
    *,
    profile: str = CAMBRIDGE_2027,
    line_numbers: str = "auto",
) -> ComplianceReport:
    source_path = Path(path)
    source = source_path.read_text(encoding="utf-8")
    return check_source(
        source,
        profile=profile,
        line_numbers=line_numbers,
    )


def check_source(
    source: str,
    *,
    profile: str = CAMBRIDGE_2027,
    line_numbers: str = "auto",
) -> ComplianceReport:
    if profile not in SUPPORTED_PROFILES:
        raise ValueError(f"Unsupported compliance profile {profile!r}")

    if line_numbers not in LINE_NUMBER_MODES:
        raise ValueError(f"Unsupported line-number mode {line_numbers!r}")

    normalized_source, numbered, diagnostics = _prepare_line_numbers(
        source,
        line_numbers,
    )

    if not numbered:
        diagnostics.extend(_check_indentation(source))

    permissive_tokens: list[Token] | None = None

    try:
        permissive_tokens = Lexer(
            normalized_source,
            strict=False,
        ).scan_tokens()
    except LexError:
        # The strict lexer below produces the authoritative lexical diagnostic.
        pass

    parse_source = normalized_source

    if permissive_tokens is not None:
        diagnostics.extend(_check_keyword_case(permissive_tokens))
        diagnostics.extend(_check_identifier_consistency(permissive_tokens))
        diagnostics.extend(_check_extensions(permissive_tokens))
        parse_source, call_diagnostics = _normalize_bare_calls(parse_source)
        diagnostics.extend(call_diagnostics)

    try:
        strict_tokens = Lexer(parse_source, strict=True).scan_tokens()
    except LexError as error:
        diagnostics.append(_diagnostic_from_error(error, source))
    else:
        try:
            Parser(strict_tokens).parse_program()
        except ParseError as error:
            diagnostics.append(_diagnostic_from_error(error, source))

    return ComplianceReport(
        profile=profile,
        diagnostics=tuple(_sort_and_deduplicate(diagnostics)),
        normalized_source=normalized_source,
        line_numbers_detected=numbered,
    )


def _prepare_line_numbers(
    source: str,
    mode: str,
) -> tuple[str, bool, list[ComplianceDiagnostic]]:
    lines = source.splitlines(keepends=True)
    matches = [_numbered_line_match(line) for line in lines]

    if mode == "present":
        numbered = any(match is not None for match in matches)
    elif mode == "absent":
        numbered = False
    else:
        numbered = _looks_line_numbered(lines, matches)

    if not numbered:
        return source, False, []

    normalized_lines = []
    diagnostics = []
    previous_number = None

    for physical_line, (line, match) in enumerate(
        zip(lines, matches),
        start=1,
    ):
        if match is None:
            normalized_lines.append(line)
            continue

        number = int(match.group("number"))

        if previous_number is not None and number <= previous_number:
            diagnostics.append(
                ComplianceDiagnostic(
                    code="C2027-N001",
                    severity="warning",
                    message=(
                        "line numbers should increase from one statement "
                        "to the next"
                    ),
                    line=physical_line,
                    col=len(match.group("leading")) + 1,
                )
            )

        previous_number = number
        prefix_length = match.end("gap")
        normalized_lines.append(" " * prefix_length + line[prefix_length:])

    return "".join(normalized_lines), True, diagnostics


def _numbered_line_match(line: str) -> re.Match[str] | None:
    content = line.rstrip("\r\n")

    if not content.strip():
        return None

    match = _NUMBERED_LINE_RE.match(content)

    if match is None or not match.group("body").strip():
        return None

    return match


def _looks_line_numbered(
    lines: list[str],
    matches: list[re.Match[str] | None],
) -> bool:
    first_content_index = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )

    if first_content_index is None:
        return False

    first_match = matches[first_content_index]

    if (
        first_match is not None
        and _looks_like_statement(first_match.group("body"))
    ):
        return True

    return False


def _looks_like_statement(text: str) -> bool:
    stripped = text.lstrip()

    if stripped.startswith("//"):
        return True

    match = re.match(r"(?P<word>[A-Za-z][A-Za-z0-9_]*)", stripped)

    if match is None:
        return False

    word = match.group("word").upper()
    non_statement_keywords = {
        "AND",
        "APPEND",
        "ARRAY",
        "BOOLEAN",
        "BYREF",
        "BYVAL",
        "CHAR",
        "DATE",
        "DIV",
        "INHERITS",
        "INTEGER",
        "MOD",
        "NEW",
        "NOT",
        "OF",
        "OR",
        "RANDOM",
        "READ",
        "REAL",
        "RETURNS",
        "SET",
        "STEP",
        "STRING",
        "THEN",
        "TO",
        "WRITE",
    }
    return word not in non_statement_keywords


def _check_indentation(source: str) -> list[ComplianceDiagnostic]:
    diagnostics = []
    depth = 0
    case_clause_depths: list[int] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        if not line.strip():
            continue

        leading = line[:len(line) - len(line.lstrip(" \t"))]
        code, _ = _split_comment(line[len(leading):])

        if "\t" in leading:
            diagnostics.append(
                ComplianceDiagnostic(
                    code="C2027-I001",
                    severity="warning",
                    message="use spaces instead of tabs for indentation",
                    line=line_number,
                    col=leading.index("\t") + 1,
                )
            )

        words = re.findall(r"[A-Za-z]+", code)
        upper_words = [word.upper() for word in words]
        first_word = upper_words[0] if upper_words else None
        actual_spaces = len(leading.expandtabs(3))
        case_clause = False
        end_case = first_word == "ENDCASE" and bool(case_clause_depths)

        if end_case:
            expected_depth = max(0, case_clause_depths[-1] - 1)
        elif (
            case_clause_depths
            and actual_spaces <= case_clause_depths[-1] * 3
            and _case_clause_parts(code) is not None
        ):
            case_clause = True
            expected_depth = case_clause_depths[-1]
        else:
            dedents = first_word in _CLOSING_WORDS or first_word == "ELSE"
            expected_depth = max(0, depth - 1) if dedents else depth

        expected_spaces = expected_depth * 3

        if actual_spaces != expected_spaces:
            diagnostics.append(
                ComplianceDiagnostic(
                    code="C2027-I002",
                    severity="warning",
                    message=(
                        f"expected {expected_spaces} leading space(s), "
                        f"found {actual_spaces}"
                    ),
                    line=line_number,
                    col=1,
                )
            )

        depth = expected_depth

        if end_case:
            case_clause_depths.pop()
            continue

        if case_clause:
            _, clause_body = _case_clause_parts(code) or ("", "")
            depth = expected_depth + 1
            clause_words = [
                word.upper()
                for word in re.findall(r"[A-Za-z]+", clause_body)
            ]

            if _line_opens_block(clause_body, clause_words):
                depth += 1

            continue

        opens = _line_opens_block(code, upper_words)

        if first_word == "ELSE" or opens:
            depth += 1

        if first_word == "CASE":
            case_clause_depths.append(depth)

    return diagnostics


def _case_clause_parts(code: str) -> tuple[str, str] | None:
    in_string = False
    char_quote = None
    char_quotes = Lexer.CHAR_QUOTES

    for index, char in enumerate(code):
        if char_quote is not None:
            if char in char_quotes:
                char_quote = None

            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string and char in char_quotes:
            char_quote = char
            continue

        if not in_string and char == ":":
            return code[:index], code[index + 1:]

    return None


def _line_opens_block(code: str, words: list[str]) -> bool:
    if not words:
        return False

    first_word = words[0]

    if first_word in {"PUBLIC", "PRIVATE"} and len(words) > 1:
        first_word = words[1]

    if first_word == "TYPE":
        return "=" not in code

    return first_word in _OPENING_WORDS


def _split_comment(line: str) -> tuple[str, str]:
    in_string = False
    char_quote = None
    char_quotes = Lexer.CHAR_QUOTES
    index = 0

    while index < len(line):
        char = line[index]

        if char_quote is not None:
            if char in char_quotes:
                char_quote = None

            index += 1
            continue

        if char == '"':
            in_string = not in_string
            index += 1
            continue

        if not in_string and char in char_quotes:
            char_quote = char
            index += 1
            continue

        if (
            not in_string
            and char == "/"
            and index + 1 < len(line)
            and line[index + 1] == "/"
        ):
            return line[:index], line[index:]

        index += 1

    return line, ""


def _check_keyword_case(
    tokens: list[Token],
) -> list[ComplianceDiagnostic]:
    diagnostics = []

    for token in tokens:
        expected = None

        if token.type in _KEYWORD_TYPES:
            expected = token.lexeme.upper()
        elif token.type == T.BOOL_LIT:
            expected = token.lexeme.upper()
        elif (
            token.type == T.IDENT
            and token.lexeme.upper() in _STANDARD_CALLABLES
        ):
            expected = token.lexeme.upper()

        if expected is not None and token.lexeme != expected:
            diagnostics.append(
                ComplianceDiagnostic(
                    code="C2027-K001",
                    severity="warning",
                    message=(
                        f"use upper-case {expected!r}, "
                        f"not {token.lexeme!r}"
                    ),
                    line=token.line,
                    col=token.col,
                )
            )

    return diagnostics


def _check_identifier_consistency(
    tokens: list[Token],
) -> list[ComplianceDiagnostic]:
    diagnostics = []
    first_spellings: dict[str, str] = {}
    reported: set[tuple[str, str]] = set()

    for token in tokens:
        if token.type != T.IDENT:
            continue

        key = token.lexeme.casefold()
        first = first_spellings.setdefault(key, token.lexeme)

        if token.lexeme == first:
            continue

        pair = (key, token.lexeme)

        if pair in reported:
            continue

        reported.add(pair)
        diagnostics.append(
            ComplianceDiagnostic(
                code="C2027-ID001",
                severity="warning",
                message=(
                    f"use consistent identifier spelling {first!r}; "
                    f"found {token.lexeme!r}"
                ),
                line=token.line,
                col=token.col,
            )
        )

    return diagnostics


def _check_extensions(
    tokens: list[Token],
) -> list[ComplianceDiagnostic]:
    diagnostics = []
    declared_callables = {
        tokens[index + 1].lexeme.casefold()
        for index, token in enumerate(tokens[:-1])
        if token.type in {T.PROCEDURE, T.FUNCTION}
        and tokens[index + 1].type in {T.IDENT, T.NEW}
    }

    for index, token in enumerate(tokens):
        if token.type != T.IDENT:
            continue

        name = token.lexeme.upper()

        if name not in _PSEI_EXTENSION_CALLABLES:
            continue

        if token.lexeme.casefold() in declared_callables:
            continue

        previous_type = tokens[index - 1].type if index > 0 else None
        next_type = (
            tokens[index + 1].type
            if index + 1 < len(tokens)
            else None
        )

        if previous_type != T.CALL and next_type != T.LPAREN:
            continue

        diagnostics.append(
            ComplianceDiagnostic(
                code="C2027-X001",
                severity="warning",
                message=(
                    f"{name} is a documented psei extension, "
                    "not a standard operation defined by the Cambridge guide"
                ),
                line=token.line,
                col=token.col,
            )
        )

    return diagnostics


def _normalize_bare_calls(
    source: str,
) -> tuple[str, list[ComplianceDiagnostic]]:
    normalized_lines = []
    diagnostics = []

    for line_number, line in enumerate(
        source.splitlines(keepends=True),
        start=1,
    ):
        content = line.rstrip("\r\n")
        ending = line[len(content):]
        code, comment = _split_comment(content)
        match = _BARE_CALL_RE.search(code)

        if match is None:
            normalized_lines.append(line)
            continue

        name = match.group("name")
        diagnostics.append(
            ComplianceDiagnostic(
                code="C2027-C001",
                severity="warning",
                message=(
                    f"use CALL {name}(); section 8.1 requires parentheses, "
                    "although the page 19 CASE example omits them"
                ),
                line=line_number,
                col=match.start("name") + 1,
            )
        )

        insert_at = match.end("name")
        normalized_lines.append(
            code[:insert_at]
            + "()"
            + code[insert_at:]
            + comment
            + ending
        )

    return "".join(normalized_lines), diagnostics


def _diagnostic_from_error(
    error: LexError | ParseError,
    source: str,
) -> ComplianceDiagnostic:
    text = str(error)
    match = _LOCATION_RE.match(text)

    if match is None:
        line = max(1, len(source.splitlines()))
        col = 1
        message = text
    else:
        line = int(match.group("line"))
        col = int(match.group("col"))
        message = match.group("message")

    code = "C2027-P001"

    if isinstance(error, LexError):
        code = "C2027-L001"

        if "Use ← for assignment" in message:
            code = "C2027-A001"

        unexpected = re.fullmatch(r"Unexpected character (?P<char>.+)", message)

        if unexpected is not None:
            try:
                char = ast.literal_eval(unexpected.group("char"))
            except (SyntaxError, ValueError):
                char = None

            if isinstance(char, str) and char.isalpha() and not char.isascii():
                code = "C2027-ID002"
                message = (
                    "identifiers may contain only ASCII letters, digits "
                    "and underscore"
                )

    return ComplianceDiagnostic(
        code=code,
        severity="error",
        message=message,
        line=line,
        col=col,
    )


def _sort_and_deduplicate(
    diagnostics: list[ComplianceDiagnostic],
) -> list[ComplianceDiagnostic]:
    unique = {
        (
            item.code,
            item.severity,
            item.message,
            item.line,
            item.col,
        ): item
        for item in diagnostics
    }
    severity_order = {"error": 0, "warning": 1}

    return sorted(
        unique.values(),
        key=lambda item: (
            item.line,
            item.col,
            severity_order.get(item.severity, 2),
            item.code,
        ),
    )
