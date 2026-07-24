from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceSpan:
    line: int
    col: int


@dataclass(frozen=True)
class ArrayType:
    bounds: tuple[tuple[int, int], ...]
    element_type: Any


@dataclass
class Program:
    statements: list[Any]


@dataclass
class DeclareStmt:
    name: str
    type_spec: Any
    span: SourceSpan | None = None


@dataclass
class ConstantStmt:
    name: str
    expr: Any
    span: SourceSpan | None = None


@dataclass
class AssignStmt:
    target: Any
    expr: Any
    span: SourceSpan | None = None


@dataclass
class InputStmt:
    target: Any
    span: SourceSpan | None = None


@dataclass
class OutputStmt:
    exprs: list[Any]
    span: SourceSpan | None = None


@dataclass
class IfStmt:
    condition: Any
    then_body: list[Any]
    else_body: list[Any]
    span: SourceSpan | None = None


@dataclass
class CaseStmt:
    selector: Any
    clauses: list[Any]
    otherwise_body: list[Any]
    span: SourceSpan | None = None


@dataclass
class CaseClause:
    start: Any
    end: Any | None
    body: list[Any]


@dataclass
class WhileStmt:
    condition: Any
    body: list[Any]
    span: SourceSpan | None = None


@dataclass
class RepeatStmt:
    body: list[Any]
    condition: Any
    span: SourceSpan | None = None


@dataclass
class ForStmt:
    var_name: str
    start: Any
    end: Any
    step: Any | None
    body: list[Any]
    span: SourceSpan | None = None


@dataclass
class VarTarget:
    name: str


@dataclass
class ArrayTarget:
    name: str
    indices: list[Any]


@dataclass
class LiteralExpr:
    value: Any


@dataclass
class VariableExpr:
    name: str


@dataclass
class ArrayAccessExpr:
    array_expr: Any
    indices: list[Any]


@dataclass
class UnaryExpr:
    op: Any
    right: Any


@dataclass
class BinaryExpr:
    left: Any
    op: Any
    right: Any


@dataclass
class CallExpr:
    name: str
    args: list[Any]
