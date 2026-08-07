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


@dataclass(frozen=True)
class PointerType:
    target_type: Any


@dataclass(frozen=True)
class SetTypeSpec:
    element_type: Any


@dataclass(frozen=True)
class UserTypeRef:
    name: str


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
class DefineSetStmt:
    name: str
    values: list[Any]
    type_spec: Any
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
class OpenFileStmt:
    file_expr: Any
    mode: str
    span: SourceSpan | None = None


@dataclass
class ReadFileStmt:
    file_expr: Any
    target: Any
    span: SourceSpan | None = None


@dataclass
class WriteFileStmt:
    file_expr: Any
    data_expr: Any
    span: SourceSpan | None = None


@dataclass
class CloseFileStmt:
    file_expr: Any
    span: SourceSpan | None = None


@dataclass
class SeekStmt:
    file_expr: Any
    address_expr: Any
    span: SourceSpan | None = None


@dataclass
class GetRecordStmt:
    file_expr: Any
    target: Any
    span: SourceSpan | None = None


@dataclass
class PutRecordStmt:
    file_expr: Any
    value_expr: Any
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
    span: SourceSpan | None = None


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
class RecordField:
    name: str
    type_spec: Any
    span: SourceSpan | None = None


@dataclass
class TypeDeclEnum:
    name: str
    values: list[str]
    span: SourceSpan | None = None


@dataclass
class TypeDeclPointer:
    name: str
    target_type: Any
    span: SourceSpan | None = None


@dataclass
class TypeDeclSet:
    name: str
    element_type: Any
    span: SourceSpan | None = None


@dataclass
class TypeDeclRecord:
    name: str
    fields: list[RecordField]
    span: SourceSpan | None = None


@dataclass
class ClassFieldDecl:
    access: str
    name: str
    type_spec: Any
    span: SourceSpan | None = None


@dataclass
class MethodDecl:
    access: str
    kind: str
    name: str
    params: list[Any]
    return_type: Any | None
    body: list[Any]
    span: SourceSpan | None = None


@dataclass
class ClassDecl:
    name: str
    parent_name: str | None
    members: list[Any]
    initializers: list[Any]
    span: SourceSpan | None = None


@dataclass
class Param:
    name: str
    type_spec: Any
    passing: str
    span: SourceSpan | None = None


@dataclass
class ProcedureDecl:
    name: str
    params: list[Param]
    body: list[Any]
    span: SourceSpan | None = None


@dataclass
class FunctionDecl:
    name: str
    params: list[Param]
    return_type: Any
    body: list[Any]
    span: SourceSpan | None = None


@dataclass
class CallStmt:
    name: str
    args: list[Any]
    span: SourceSpan | None = None


@dataclass
class MethodCallStmt:
    call: Any
    span: SourceSpan | None = None


@dataclass
class ReturnStmt:
    expr: Any
    span: SourceSpan | None = None


@dataclass
class VarTarget:
    name: str
    span: SourceSpan | None = None


@dataclass
class ArrayTarget:
    name: str
    indices: list[Any]
    span: SourceSpan | None = None


@dataclass
class IndexTarget:
    array_expr: Any
    indices: list[Any]
    span: SourceSpan | None = None


@dataclass
class FieldTarget:
    record_expr: Any
    field_name: str
    span: SourceSpan | None = None


@dataclass
class DerefTarget:
    pointer_expr: Any
    span: SourceSpan | None = None


@dataclass
class LiteralExpr:
    value: Any
    span: SourceSpan | None = None


@dataclass
class VariableExpr:
    name: str
    span: SourceSpan | None = None


@dataclass
class ArrayAccessExpr:
    array_expr: Any
    indices: list[Any]
    span: SourceSpan | None = None


@dataclass
class FieldAccessExpr:
    record_expr: Any
    field_name: str
    span: SourceSpan | None = None


@dataclass
class AddressOfExpr:
    target_expr: Any
    span: SourceSpan | None = None


@dataclass
class DerefExpr:
    pointer_expr: Any
    span: SourceSpan | None = None


@dataclass
class UnaryExpr:
    op: Any
    right: Any
    span: SourceSpan | None = None


@dataclass
class BinaryExpr:
    left: Any
    op: Any
    right: Any
    span: SourceSpan | None = None


@dataclass
class CallExpr:
    name: str
    args: list[Any]
    span: SourceSpan | None = None


@dataclass
class MethodCallExpr:
    object_expr: Any
    method_name: str
    args: list[Any]
    span: SourceSpan | None = None


@dataclass
class NewExpr:
    class_name: str
    args: list[Any]
    span: SourceSpan | None = None


@dataclass
class SuperExpr:
    span: SourceSpan | None = None
