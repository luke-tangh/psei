from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


@dataclass
class ConstantStmt:
    name: str
    expr: Any


@dataclass
class AssignStmt:
    target: Any
    expr: Any


@dataclass
class InputStmt:
    target: Any


@dataclass
class OutputStmt:
    exprs: list[Any]


@dataclass
class IfStmt:
    condition: Any
    then_body: list[Any]
    else_body: list[Any]


@dataclass
class CaseStmt:
    selector: Any
    clauses: list[Any]
    otherwise_body: list[Any]


@dataclass
class CaseClause:
    start: Any
    end: Any | None
    body: list[Any]


@dataclass
class WhileStmt:
    condition: Any
    body: list[Any]


@dataclass
class RepeatStmt:
    body: list[Any]
    condition: Any


@dataclass
class ForStmt:
    var_name: str
    start: Any
    end: Any
    step: Any | None
    body: list[Any]


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
