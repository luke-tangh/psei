#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()

if not (ROOT / "interpreter").is_dir():
    raise SystemExit("Run this script from the repository root.")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)

    if not text.endswith("\n"):
        text += "\n"

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {rel}")


AST_NODES_PY = r'''from __future__ import annotations

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


@dataclass
class TypeDeclEnum:
    name: str
    values: list[str]
    span: SourceSpan | None = None


@dataclass
class TypeDeclRecord:
    name: str
    fields: list[RecordField]
    span: SourceSpan | None = None


@dataclass
class Param:
    name: str
    type_spec: Any
    passing: str


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
class ReturnStmt:
    expr: Any
    span: SourceSpan | None = None


@dataclass
class VarTarget:
    name: str


@dataclass
class ArrayTarget:
    name: str
    indices: list[Any]


@dataclass
class IndexTarget:
    array_expr: Any
    indices: list[Any]


@dataclass
class FieldTarget:
    record_expr: Any
    field_name: str


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
class FieldAccessExpr:
    record_expr: Any
    field_name: str


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
'''


TOKENS_PY = r'''from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class T:
    EOF = "EOF"
    NEWLINE = "NEWLINE"

    IDENT = "IDENT"
    INT_LIT = "INT_LIT"
    REAL_LIT = "REAL_LIT"
    STRING_LIT = "STRING_LIT"
    CHAR_LIT = "CHAR_LIT"
    DATE_LIT = "DATE_LIT"
    BOOL_LIT = "BOOL_LIT"

    DECLARE = "DECLARE"
    CONSTANT = "CONSTANT"
    ARRAY = "ARRAY"
    OF = "OF"

    INTEGER = "INTEGER"
    REAL = "REAL"
    CHAR = "CHAR"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"

    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    ENDIF = "ENDIF"

    CASE = "CASE"
    OTHERWISE = "OTHERWISE"
    ENDCASE = "ENDCASE"

    WHILE = "WHILE"
    ENDWHILE = "ENDWHILE"

    REPEAT = "REPEAT"
    UNTIL = "UNTIL"

    FOR = "FOR"
    TO = "TO"
    STEP = "STEP"
    NEXT = "NEXT"

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    OPENFILE = "OPENFILE"
    READFILE = "READFILE"
    WRITEFILE = "WRITEFILE"
    CLOSEFILE = "CLOSEFILE"

    READ = "READ"
    WRITE = "WRITE"
    APPEND = "APPEND"
    RANDOM = "RANDOM"

    SEEK = "SEEK"
    GETRECORD = "GETRECORD"
    PUTRECORD = "PUTRECORD"

    CALL = "CALL"
    PROCEDURE = "PROCEDURE"
    ENDPROCEDURE = "ENDPROCEDURE"
    FUNCTION = "FUNCTION"
    RETURNS = "RETURNS"
    ENDFUNCTION = "ENDFUNCTION"
    RETURN = "RETURN"
    BYVAL = "BYVAL"
    BYREF = "BYREF"

    TYPE = "TYPE"
    ENDTYPE = "ENDTYPE"

    CLASS = "CLASS"
    ENDCLASS = "ENDCLASS"

    ASSIGN = "ASSIGN"       # ← or <-
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    DIV = "DIV"
    MOD = "MOD"
    AMP = "AMP"             # &

    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS = "LESS"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER = "GREATER"
    GREATER_EQUAL = "GREATER_EQUAL"

    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    DOT = "DOT"


KEYWORDS = {
    "DECLARE": T.DECLARE,
    "CONSTANT": T.CONSTANT,
    "ARRAY": T.ARRAY,
    "OF": T.OF,

    "INTEGER": T.INTEGER,
    "REAL": T.REAL,
    "CHAR": T.CHAR,
    "STRING": T.STRING,
    "BOOLEAN": T.BOOLEAN,
    "DATE": T.DATE,

    "IF": T.IF,
    "THEN": T.THEN,
    "ELSE": T.ELSE,
    "ENDIF": T.ENDIF,

    "CASE": T.CASE,
    "OTHERWISE": T.OTHERWISE,
    "ENDCASE": T.ENDCASE,

    "WHILE": T.WHILE,
    "ENDWHILE": T.ENDWHILE,

    "REPEAT": T.REPEAT,
    "UNTIL": T.UNTIL,

    "FOR": T.FOR,
    "TO": T.TO,
    "STEP": T.STEP,
    "NEXT": T.NEXT,

    "INPUT": T.INPUT,
    "OUTPUT": T.OUTPUT,

    "OPENFILE": T.OPENFILE,
    "READFILE": T.READFILE,
    "WRITEFILE": T.WRITEFILE,
    "CLOSEFILE": T.CLOSEFILE,

    "READ": T.READ,
    "WRITE": T.WRITE,
    "APPEND": T.APPEND,
    "RANDOM": T.RANDOM,

    "SEEK": T.SEEK,
    "GETRECORD": T.GETRECORD,
    "PUTRECORD": T.PUTRECORD,

    "DIV": T.DIV,
    "MOD": T.MOD,
    "AND": T.AND,
    "OR": T.OR,
    "NOT": T.NOT,

    "CALL": T.CALL,
    "PROCEDURE": T.PROCEDURE,
    "ENDPROCEDURE": T.ENDPROCEDURE,
    "FUNCTION": T.FUNCTION,
    "RETURNS": T.RETURNS,
    "ENDFUNCTION": T.ENDFUNCTION,
    "RETURN": T.RETURN,
    "BYVAL": T.BYVAL,
    "BYREF": T.BYREF,

    "TYPE": T.TYPE,
    "ENDTYPE": T.ENDTYPE,

    "CLASS": T.CLASS,
    "ENDCLASS": T.ENDCLASS,
}


@dataclass
class Token:
    type: str
    lexeme: str
    literal: Any
    line: int
    col: int

    def __repr__(self):
        return (
            f"Token({self.type}, {self.lexeme!r}, "
            f"{self.literal!r}, {self.line}:{self.col})"
        )
'''


RUNTIME_PY = r'''from __future__ import annotations

import copy
import itertools
import pickle
import random
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ast_nodes import ArrayType, UserTypeRef
from .errors import PseudoRuntimeError
from .tokens import T
from .values import Char, DateValue


BASIC_TYPES = {
    T.INTEGER,
    T.REAL,
    T.CHAR,
    T.STRING,
    T.BOOLEAN,
    T.DATE,
}


def norm_identifier(name: str) -> str:
    return name.lower()


@dataclass
class EnumType:
    name: str
    values: tuple[str, ...]
    value_to_index: dict[str, int]

    def ordinal_of(self, value_name: str) -> int:
        key = norm_identifier(value_name)

        if key not in self.value_to_index:
            raise PseudoRuntimeError(
                f"{value_name!r} is not a value of enumerated type {self.name}"
            )

        return self.value_to_index[key]


@dataclass(frozen=True)
class EnumValue:
    type_spec: EnumType
    name: str
    ordinal: int

    def __str__(self) -> str:
        return self.name


@dataclass
class RecordFieldSpec:
    original_name: str
    type_spec: Any


@dataclass
class RecordType:
    name: str
    fields: dict[str, RecordFieldSpec]
    completed: bool = False

    def get_field(self, field_name: str) -> RecordFieldSpec:
        key = norm_identifier(field_name)

        if key not in self.fields:
            raise PseudoRuntimeError(
                f"Record type {self.name!r} has no field {field_name!r}"
            )

        return self.fields[key]


@dataclass
class RecordValue:
    type_spec: RecordType
    fields: dict[str, Any]

    @classmethod
    def create(cls, type_spec: RecordType) -> RecordValue:
        if not type_spec.completed:
            raise PseudoRuntimeError(
                f"Record type {type_spec.name!r} is not completely defined"
            )

        fields = {}

        for key, field in type_spec.fields.items():
            fields[key] = copy.deepcopy(default_value(field.type_spec))

        return cls(type_spec, fields)

    def clone(self) -> RecordValue:
        return RecordValue(self.type_spec, copy.deepcopy(self.fields))

    def get(self, field_name: str) -> Any:
        key = norm_identifier(field_name)
        self.type_spec.get_field(field_name)
        return self.fields[key]

    def set(self, field_name: str, value: Any):
        key = norm_identifier(field_name)
        field = self.type_spec.get_field(field_name)
        self.fields[key] = coerce_value(value, field.type_spec)

    def field_type(self, field_name: str) -> Any:
        return self.type_spec.get_field(field_name).type_spec


@dataclass
class ArrayValue:
    type_spec: ArrayType
    data: dict[tuple[int, ...], Any]

    @classmethod
    def create(cls, type_spec: ArrayType) -> ArrayValue:
        ranges = [
            range(lower, upper + 1)
            for lower, upper in type_spec.bounds
        ]

        data = {}

        for index_tuple in itertools.product(*ranges):
            data[index_tuple] = copy.deepcopy(
                default_value(type_spec.element_type)
            )

        return cls(type_spec, data)

    def clone(self):
        return ArrayValue(self.type_spec, copy.deepcopy(self.data))

    def validate_indices(self, indices: list[int]) -> tuple[int, ...]:
        if len(indices) != len(self.type_spec.bounds):
            raise PseudoRuntimeError(
                f"Array expects {len(self.type_spec.bounds)} index(es), "
                f"got {len(indices)}"
            )

        for i, value in enumerate(indices):
            lower, upper = self.type_spec.bounds[i]

            if value < lower or value > upper:
                raise PseudoRuntimeError(
                    f"Array index {value} out of bounds. "
                    f"Expected {lower} to {upper}."
                )

        return tuple(indices)

    def get(self, indices: list[int]) -> Any:
        key = self.validate_indices(indices)
        return self.data[key]

    def set(self, indices: list[int], value: Any):
        key = self.validate_indices(indices)
        self.data[key] = coerce_value(value, self.type_spec.element_type)


@dataclass
class FileHandle:
    file_id: str
    mode: str
    text_pointer: int = 0
    random_pointer: int = 0


class InMemoryFileSystem:
    """
    Small deterministic file-system abstraction used by run_source() by default.

    Text files are stored as lists of lines. Random files are stored as a mapping
    from integer address to a deep-copied runtime value.
    """

    def __init__(self):
        self.text_files: dict[str, list[str]] = {}
        self.random_files: dict[str, dict[int, Any]] = {}
        self.open_files: dict[str, FileHandle] = {}

    def _normalise(self, file_id: str) -> str:
        return str(file_id)

    def _handle(self, file_id: str) -> FileHandle:
        key = self._normalise(file_id)

        if key not in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is not open")

        return self.open_files[key]

    def _require_mode(self, file_id: str, allowed: set[str]) -> FileHandle:
        handle = self._handle(file_id)

        if handle.mode not in allowed:
            modes = ", ".join(sorted(allowed))
            raise PseudoRuntimeError(
                f"File {file_id!r} is open for {handle.mode}, "
                f"expected one of {modes}"
            )

        return handle

    def open_file(self, file_id: str, mode: str):
        key = self._normalise(file_id)

        if key in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is already open")

        if mode == T.READ:
            if key not in self.text_files:
                raise PseudoRuntimeError(f"Text file {file_id!r} does not exist")

        elif mode == T.WRITE:
            self.text_files[key] = []

        elif mode == T.APPEND:
            self.text_files.setdefault(key, [])

        elif mode == T.RANDOM:
            self.random_files.setdefault(key, {})

        else:
            raise PseudoRuntimeError(f"Unsupported file mode {mode!r}")

        self.open_files[key] = FileHandle(file_id=key, mode=mode)

    def close_file(self, file_id: str):
        key = self._normalise(file_id)

        if key not in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is not open")

        del self.open_files[key]

    def read_file(self, file_id: str) -> str:
        handle = self._require_mode(file_id, {T.READ})
        lines = self.text_files[handle.file_id]

        if handle.text_pointer >= len(lines):
            raise PseudoRuntimeError(f"Cannot READFILE past EOF for {file_id!r}")

        line = lines[handle.text_pointer]
        handle.text_pointer += 1
        return line

    def write_file(self, file_id: str, data: str):
        handle = self._require_mode(file_id, {T.WRITE, T.APPEND})
        self.text_files[handle.file_id].append(str(data))

    def eof(self, file_id: str) -> bool:
        handle = self._require_mode(file_id, {T.READ})
        return handle.text_pointer >= len(self.text_files[handle.file_id])

    def seek(self, file_id: str, address: int):
        handle = self._require_mode(file_id, {T.RANDOM})

        if address < 0:
            raise PseudoRuntimeError("Random file address cannot be negative")

        handle.random_pointer = address

    def get_record(self, file_id: str) -> Any:
        handle = self._require_mode(file_id, {T.RANDOM})
        records = self.random_files[handle.file_id]
        address = handle.random_pointer

        if address not in records:
            raise PseudoRuntimeError(
                f"No record exists at address {address} in {file_id!r}"
            )

        return copy.deepcopy(records[address])

    def put_record(self, file_id: str, value: Any):
        handle = self._require_mode(file_id, {T.RANDOM})
        self.random_files[handle.file_id][handle.random_pointer] = copy.deepcopy(value)


class LocalFileSystem(InMemoryFileSystem):
    """
    File-system abstraction used by run_file().

    Text files are written as UTF-8 text. Random files are persisted with pickle,
    which is a pragmatic interpreter implementation detail rather than a
    Cambridge pseudocode concept.
    """

    def __init__(self, base_dir: str | Path | None = None):
        super().__init__()
        self.base_dir = Path.cwd() if base_dir is None else Path(base_dir)

    def _path(self, file_id: str) -> Path:
        path = Path(str(file_id))

        if not path.is_absolute():
            path = self.base_dir / path

        return path

    def _normalise(self, file_id: str) -> str:
        return str(self._path(file_id).resolve())

    def open_file(self, file_id: str, mode: str):
        key = self._normalise(file_id)
        path = Path(key)

        if key in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is already open")

        if mode == T.READ:
            if not path.exists():
                raise PseudoRuntimeError(f"Text file {file_id!r} does not exist")

            self.text_files[key] = path.read_text(encoding="utf-8").splitlines()

        elif mode == T.WRITE:
            self.text_files[key] = []

        elif mode == T.APPEND:
            if path.exists():
                self.text_files[key] = path.read_text(encoding="utf-8").splitlines()
            else:
                self.text_files[key] = []

        elif mode == T.RANDOM:
            if path.exists():
                with path.open("rb") as f:
                    data = pickle.load(f)

                if not isinstance(data, dict):
                    raise PseudoRuntimeError(
                        f"Random file {file_id!r} does not contain record data"
                    )

                self.random_files[key] = data
            else:
                self.random_files[key] = {}

        else:
            raise PseudoRuntimeError(f"Unsupported file mode {mode!r}")

        self.open_files[key] = FileHandle(file_id=key, mode=mode)

    def close_file(self, file_id: str):
        handle = self._handle(file_id)
        key = handle.file_id
        path = Path(key)

        if handle.mode in {T.WRITE, T.APPEND}:
            path.parent.mkdir(parents=True, exist_ok=True)

            lines = self.text_files.get(key, [])
            text = "\n".join(lines)

            if lines:
                text += "\n"

            path.write_text(text, encoding="utf-8", newline="\n")

        elif handle.mode == T.RANDOM:
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("wb") as f:
                pickle.dump(self.random_files.get(key, {}), f)

        super().close_file(file_id)


@dataclass
class Reference:
    type_spec: Any
    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    description: str = ""

    def get(self) -> Any:
        return self.getter()

    def set(self, value: Any):
        self.setter(coerce_value(value, self.type_spec))


@dataclass
class Binding:
    original_name: str
    type_spec: Any
    value: Any
    constant: bool = False
    reference: Reference | None = None

    def read(self) -> Any:
        if self.reference is not None:
            return self.reference.get()

        return self.value

    def write(self, value: Any):
        if self.constant:
            raise PseudoRuntimeError(
                f"Cannot assign to constant {self.original_name!r}"
            )

        if self.reference is not None:
            self.reference.set(value)
            return

        self.value = coerce_value(value, self.type_spec)


class Environment:
    def __init__(
        self,
        *,
        strict: bool = False,
        parent: Environment | None = None,
        name: str = "scope",
    ):
        self.strict = strict
        self.parent = parent
        self.name = name
        self.bindings: dict[str, Binding] = {}

    @staticmethod
    def norm(name: str) -> str:
        return norm_identifier(name)

    def exists_local(self, name: str) -> bool:
        return self.norm(name) in self.bindings

    def exists(self, name: str) -> bool:
        return self.resolve_env(name) is not None

    def resolve_env(self, name: str) -> Environment | None:
        key = self.norm(name)

        if key in self.bindings:
            return self

        if self.parent is not None:
            return self.parent.resolve_env(name)

        return None

    def define(
        self,
        name: str,
        type_spec: Any,
        value: Any = None,
        *,
        constant: bool = False,
    ):
        key = self.norm(name)

        if key in self.bindings:
            old = self.bindings[key].original_name
            raise PseudoRuntimeError(
                f"Identifier {name!r} already declared as {old!r}"
            )

        if value is None:
            value = default_value(type_spec)
        else:
            value = coerce_value(value, type_spec)

        self.bindings[key] = Binding(
            original_name=name,
            type_spec=type_spec,
            value=value,
            constant=constant,
        )

    def define_reference(
        self,
        name: str,
        type_spec: Any,
        reference: Reference,
    ):
        key = self.norm(name)

        if key in self.bindings:
            old = self.bindings[key].original_name
            raise PseudoRuntimeError(
                f"Identifier {name!r} already declared as {old!r}"
            )

        self.bindings[key] = Binding(
            original_name=name,
            type_spec=type_spec,
            value=None,
            constant=False,
            reference=reference,
        )

    def define_constant(self, name: str, value: Any):
        type_spec = infer_type(value)
        self.define(name, type_spec, value, constant=True)

    def assign(self, name: str, value: Any):
        env = self.resolve_env(name)

        if env is None:
            if self.strict:
                raise PseudoRuntimeError(f"Undefined variable {name!r}")

            inferred = infer_type(value)
            self.define(name, inferred, value)
            return

        binding = env.bindings[self.norm(name)]
        binding.write(value)

    def get(self, name: str) -> Any:
        return self.get_binding(name).read()

    def get_binding(self, name: str) -> Binding:
        env = self.resolve_env(name)

        if env is None:
            raise PseudoRuntimeError(f"Undefined variable {name!r}")

        return env.bindings[self.norm(name)]

    def dump(self, *, include_parents: bool = False) -> str:
        envs = [self]

        if include_parents:
            parent = self.parent

            while parent is not None:
                envs.append(parent)
                parent = parent.parent

        lines = []
        seen: set[str] = set()

        for env in envs:
            for key, binding in env.bindings.items():
                if key in seen:
                    continue

                seen.add(key)
                lines.append(self._format_binding(binding))

        if not lines:
            return "(no variables)"

        return "\n".join(lines)

    @staticmethod
    def _format_binding(binding: Binding) -> str:
        const = "CONSTANT " if binding.constant else ""

        return (
            f"{const}{binding.original_name} : "
            f"{type_to_str(binding.type_spec)} = "
            f"{debug_value(binding.read())}"
        )


class Runtime:
    def __init__(
        self,
        *,
        strict: bool = False,
        input_provider: Callable[[], str] | None = None,
        output_writer: Callable[[str], Any] | None = None,
        rng: random.Random | None = None,
        file_system: InMemoryFileSystem | None = None,
    ):
        self.strict = strict
        self.global_env = Environment(strict=strict, name="global")
        self._env_stack: list[Environment] = [self.global_env]

        self.types: dict[str, Any] = {}
        self.enum_values: dict[str, EnumValue] = {}

        self.procedures: dict[str, Any] = {}
        self.functions: dict[str, Any] = {}

        self.file_system = file_system if file_system is not None else InMemoryFileSystem()

        self.input_provider = input_provider if input_provider is not None else input
        self.output_writer = output_writer if output_writer is not None else print
        self.rng = rng if rng is not None else random.Random()

    @property
    def env(self) -> Environment:
        return self._env_stack[-1]

    def push_scope(self, name: str = "local") -> Environment:
        env = Environment(
            strict=self.strict,
            parent=self.env,
            name=name,
        )
        self._env_stack.append(env)
        return env

    def pop_scope(self) -> Environment:
        if len(self._env_stack) == 1:
            raise PseudoRuntimeError("Cannot pop the global scope")

        return self._env_stack.pop()

    @contextmanager
    def scope(self, name: str = "local"):
        self.push_scope(name)

        try:
            yield self.env
        finally:
            self.pop_scope()

    def resolve_type_spec(self, type_spec: Any) -> Any:
        if isinstance(type_spec, ArrayType):
            return ArrayType(
                type_spec.bounds,
                self.resolve_type_spec(type_spec.element_type),
            )

        if isinstance(type_spec, UserTypeRef):
            key = norm_identifier(type_spec.name)

            if key not in self.types:
                raise PseudoRuntimeError(f"Unknown type {type_spec.name!r}")

            return self.types[key]

        return type_spec

    def reserve_record_type(self, name: str):
        key = norm_identifier(name)

        if key in self.types:
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        self.types[key] = RecordType(name=name, fields={}, completed=False)

    def register_enum_type(self, name: str, values: list[str]):
        key = norm_identifier(name)

        if key in self.types:
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        if not values:
            raise PseudoRuntimeError("Enumerated TYPE must have at least one value")

        seen_values: set[str] = set()
        value_to_index: dict[str, int] = {}

        for index, value in enumerate(values):
            value_key = norm_identifier(value)

            if value_key in seen_values:
                raise PseudoRuntimeError(
                    f"Duplicate enumerated value {value!r} in TYPE {name!r}"
                )

            if value_key in self.enum_values:
                old = self.enum_values[value_key]
                raise PseudoRuntimeError(
                    f"Enumerated value {value!r} is already defined "
                    f"by TYPE {old.type_spec.name!r}"
                )

            seen_values.add(value_key)
            value_to_index[value_key] = index

        enum_type = EnumType(
            name=name,
            values=tuple(values),
            value_to_index=value_to_index,
        )

        self.types[key] = enum_type

        for value in values:
            ordinal = enum_type.ordinal_of(value)
            self.enum_values[norm_identifier(value)] = EnumValue(
                type_spec=enum_type,
                name=value,
                ordinal=ordinal,
            )

    def register_record_type(self, name: str, fields: list[Any]):
        key = norm_identifier(name)

        if key not in self.types:
            self.types[key] = RecordType(name=name, fields={}, completed=False)

        record_type = self.types[key]

        if not isinstance(record_type, RecordType):
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        if record_type.completed:
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        field_specs: dict[str, RecordFieldSpec] = {}

        for field in fields:
            field_key = norm_identifier(field.name)

            if field_key in field_specs:
                raise PseudoRuntimeError(
                    f"Duplicate field {field.name!r} in record TYPE {name!r}"
                )

            field_specs[field_key] = RecordFieldSpec(
                original_name=field.name,
                type_spec=self.resolve_type_spec(field.type_spec),
            )

        record_type.fields = field_specs
        record_type.completed = True

    def has_enum_value(self, name: str) -> bool:
        return norm_identifier(name) in self.enum_values

    def get_enum_value(self, name: str) -> EnumValue:
        key = norm_identifier(name)

        if key not in self.enum_values:
            raise PseudoRuntimeError(f"Unknown enumerated value {name!r}")

        return self.enum_values[key]

    def register_procedure(self, decl: Any):
        key = Environment.norm(decl.name)

        if key in self.procedures:
            raise PseudoRuntimeError(f"PROCEDURE {decl.name!r} is already defined")

        if key in self.functions:
            raise PseudoRuntimeError(
                f"Identifier {decl.name!r} is already defined as a FUNCTION"
            )

        self.procedures[key] = decl

    def register_function(self, decl: Any):
        key = Environment.norm(decl.name)

        if key in self.functions:
            raise PseudoRuntimeError(f"FUNCTION {decl.name!r} is already defined")

        if key in self.procedures:
            raise PseudoRuntimeError(
                f"Identifier {decl.name!r} is already defined as a PROCEDURE"
            )

        self.functions[key] = decl

    def has_procedure(self, name: str) -> bool:
        return Environment.norm(name) in self.procedures

    def has_function(self, name: str) -> bool:
        return Environment.norm(name) in self.functions

    def get_procedure(self, name: str) -> Any:
        key = Environment.norm(name)

        if key in self.procedures:
            return self.procedures[key]

        if key in self.functions:
            raise PseudoRuntimeError(f"{name!r} is a FUNCTION, not a PROCEDURE")

        raise PseudoRuntimeError(f"Unknown PROCEDURE {name!r}")

    def get_function(self, name: str) -> Any:
        key = Environment.norm(name)

        if key in self.functions:
            return self.functions[key]

        if key in self.procedures:
            raise PseudoRuntimeError(f"{name!r} is a PROCEDURE, not a FUNCTION")

        raise PseudoRuntimeError(f"Unknown FUNCTION {name!r}")


def type_to_str(type_spec: Any) -> str:
    if isinstance(type_spec, ArrayType):
        bounds = ",".join(
            f"{lower}:{upper}"
            for lower, upper in type_spec.bounds
        )

        return f"ARRAY[{bounds}] OF {type_to_str(type_spec.element_type)}"

    if isinstance(type_spec, UserTypeRef):
        return type_spec.name

    if isinstance(type_spec, EnumType):
        return type_spec.name

    if isinstance(type_spec, RecordType):
        return type_spec.name

    return str(type_spec).upper()


def same_type(a: Any, b: Any) -> bool:
    if isinstance(a, ArrayType) and isinstance(b, ArrayType):
        return (
            a.bounds == b.bounds
            and same_type(a.element_type, b.element_type)
        )

    if isinstance(a, EnumType) and isinstance(b, EnumType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, RecordType) and isinstance(b, RecordType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, UserTypeRef) and isinstance(b, UserTypeRef):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, UserTypeRef) and isinstance(b, (EnumType, RecordType)):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(b, UserTypeRef) and isinstance(a, (EnumType, RecordType)):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, str) and isinstance(b, str):
        return a.upper() == b.upper()

    return False


def default_value(type_spec: Any) -> Any:
    if isinstance(type_spec, UserTypeRef):
        raise PseudoRuntimeError(
            f"Cannot create value for unresolved type {type_spec.name!r}"
        )

    if isinstance(type_spec, ArrayType):
        return ArrayValue.create(type_spec)

    if isinstance(type_spec, EnumType):
        if not type_spec.values:
            raise PseudoRuntimeError(
                f"Enumerated type {type_spec.name!r} has no values"
            )

        first = type_spec.values[0]
        return EnumValue(type_spec, first, type_spec.ordinal_of(first))

    if isinstance(type_spec, RecordType):
        return RecordValue.create(type_spec)

    t = type_to_str(type_spec)

    if t == T.INTEGER:
        return 0

    if t == T.REAL:
        return 0.0

    if t == T.CHAR:
        return Char("\0")

    if t == T.STRING:
        return ""

    if t == T.BOOLEAN:
        return False

    if t == T.DATE:
        return DateValue(1, 1, 1970)

    raise PseudoRuntimeError(f"Unsupported type {type_spec!r}")


def infer_type(value: Any) -> Any:
    if isinstance(value, ArrayValue):
        return value.type_spec

    if isinstance(value, EnumValue):
        return value.type_spec

    if isinstance(value, RecordValue):
        return value.type_spec

    if type(value) is bool:
        return T.BOOLEAN

    if type(value) is int:
        return T.INTEGER

    if type(value) is float:
        return T.REAL

    if isinstance(value, Char):
        return T.CHAR

    if isinstance(value, str):
        return T.STRING

    if isinstance(value, DateValue):
        return T.DATE

    raise PseudoRuntimeError(f"Cannot infer type of value {value!r}")


def coerce_value(value: Any, type_spec: Any) -> Any:
    if isinstance(type_spec, UserTypeRef):
        raise PseudoRuntimeError(
            f"Cannot assign value to unresolved type {type_spec.name!r}"
        )

    if isinstance(type_spec, ArrayType):
        if not isinstance(value, ArrayValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not same_type(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return value.clone()

    if isinstance(type_spec, EnumType):
        if not isinstance(value, EnumValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not same_type(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return EnumValue(type_spec, value.name, value.ordinal)

    if isinstance(type_spec, RecordType):
        if not isinstance(value, RecordValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not same_type(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return RecordValue(type_spec, copy.deepcopy(value.fields))

    t = type_to_str(type_spec)

    if t == T.INTEGER:
        if type(value) is int:
            return value

        raise PseudoRuntimeError(
            f"Expected INTEGER, got {runtime_type_name(value)}"
        )

    if t == T.REAL:
        if type(value) is int or type(value) is float:
            return float(value)

        raise PseudoRuntimeError(
            f"Expected REAL, got {runtime_type_name(value)}"
        )

    if t == T.CHAR:
        if isinstance(value, Char):
            return value

        if isinstance(value, str) and len(value) == 1:
            return Char(value)

        raise PseudoRuntimeError(
            f"Expected CHAR, got {runtime_type_name(value)}"
        )

    if t == T.STRING:
        if isinstance(value, str):
            return str(value)

        raise PseudoRuntimeError(
            f"Expected STRING, got {runtime_type_name(value)}"
        )

    if t == T.BOOLEAN:
        if type(value) is bool:
            return value

        raise PseudoRuntimeError(
            f"Expected BOOLEAN, got {runtime_type_name(value)}"
        )

    if t == T.DATE:
        if isinstance(value, DateValue):
            return value

        raise PseudoRuntimeError(
            f"Expected DATE, got {runtime_type_name(value)}"
        )

    raise PseudoRuntimeError(f"Unsupported type {type_spec!r}")


def runtime_type_name(value: Any) -> str:
    return type_to_str(infer_type(value))


def debug_value(value: Any) -> str:
    if isinstance(value, ArrayValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, EnumValue):
        return value.name

    if isinstance(value, RecordValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, Char):
        if value == "\0":
            return "'\\0'"

        return f"'{value}'"

    if isinstance(value, str):
        return repr(value)

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    return str(value)


def output_value(value: Any) -> str:
    if isinstance(value, ArrayValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, EnumValue):
        return value.name

    if isinstance(value, RecordValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, Char):
        if value == "\0":
            return ""

        return str(value)

    return str(value)
'''


PARSER_PY = r'''from __future__ import annotations

from .ast_nodes import (
    ArrayAccessExpr,
    ArrayTarget,
    ArrayType,
    AssignStmt,
    BinaryExpr,
    CallExpr,
    CallStmt,
    CaseClause,
    CaseStmt,
    CloseFileStmt,
    ConstantStmt,
    DeclareStmt,
    FieldAccessExpr,
    FieldTarget,
    ForStmt,
    FunctionDecl,
    GetRecordStmt,
    IfStmt,
    IndexTarget,
    InputStmt,
    LiteralExpr,
    OpenFileStmt,
    OutputStmt,
    Param,
    ProcedureDecl,
    Program,
    PutRecordStmt,
    ReadFileStmt,
    RecordField,
    RepeatStmt,
    ReturnStmt,
    SeekStmt,
    SourceSpan,
    TypeDeclEnum,
    TypeDeclRecord,
    UnaryExpr,
    UserTypeRef,
    VariableExpr,
    VarTarget,
    WhileStmt,
    WriteFileStmt,
)
from .errors import IncompleteInput, ParseError
from .tokens import T, Token


class Parser:
    BASIC_TYPE_TOKENS = {
        T.INTEGER,
        T.REAL,
        T.CHAR,
        T.STRING,
        T.BOOLEAN,
        T.DATE,
    }

    FILE_MODE_TOKENS = {
        T.READ,
        T.WRITE,
        T.APPEND,
        T.RANDOM,
    }

    BLOCK_TERMINATORS = {
        T.ELSE,
        T.ENDIF,
        T.OTHERWISE,
        T.ENDCASE,
        T.ENDWHILE,
        T.UNTIL,
        T.NEXT,
        T.ENDPROCEDURE,
        T.ENDFUNCTION,
        T.ENDTYPE,
        T.ENDCLASS,
    }

    CASE_LABEL_STARTERS = {
        T.IDENT,
        T.INT_LIT,
        T.REAL_LIT,
        T.STRING_LIT,
        T.CHAR_LIT,
        T.DATE_LIT,
        T.BOOL_LIT,
        T.MINUS,
    }

    PRECEDENCE = {
        T.OR: 1,
        T.AND: 2,

        T.EQUAL: 3,
        T.NOT_EQUAL: 3,
        T.LESS: 3,
        T.LESS_EQUAL: 3,
        T.GREATER: 3,
        T.GREATER_EQUAL: 3,

        T.PLUS: 4,
        T.MINUS: 4,
        T.AMP: 4,

        T.STAR: 5,
        T.SLASH: 5,
        T.DIV: 5,
        T.MOD: 5,
    }

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse_program(self) -> Program:
        statements = []
        self.skip_newlines()

        while not self.check(T.EOF):
            if self.check_any(self.BLOCK_TERMINATORS):
                tok = self.peek()
                raise self.err(tok, f"Unexpected block terminator {tok.lexeme!r}")

            statements.append(self.parse_statement())
            self.skip_newlines()

        return Program(statements)

    def parse_block(self, terminators: set[str]) -> list:
        statements = []
        self.skip_newlines()

        while not self.check(T.EOF) and not self.check_any(terminators):
            statements.append(self.parse_statement())
            self.skip_newlines()

        if self.check(T.EOF):
            names = ", ".join(sorted(terminators))
            raise IncompleteInput(f"Unexpected EOF: expected one of {names}")

        return statements

    def parse_statement(self):
        start_tok = self.peek()

        if self.match(T.DECLARE):
            return self.with_span(self.parse_declare(), start_tok)

        if self.match(T.CONSTANT):
            return self.with_span(self.parse_constant(), start_tok)

        if self.match(T.TYPE):
            return self.with_span(self.parse_type_decl(), start_tok)

        if self.match(T.INPUT):
            target = self.parse_lvalue()
            return self.with_span(InputStmt(target), start_tok)

        if self.match(T.OUTPUT):
            exprs = []

            if (
                not self.check(T.NEWLINE)
                and not self.check(T.EOF)
                and not self.check_any(self.BLOCK_TERMINATORS)
            ):
                exprs.append(self.parse_expression())

                while self.match(T.COMMA):
                    exprs.append(self.parse_expression())

            return self.with_span(OutputStmt(exprs), start_tok)

        if self.match(T.OPENFILE):
            file_expr = self.parse_expression()
            self.consume(T.FOR, "Expected FOR in OPENFILE statement")
            mode = self.parse_file_mode()
            return self.with_span(OpenFileStmt(file_expr, mode), start_tok)

        if self.match(T.READFILE):
            file_expr = self.parse_expression()
            self.consume(T.COMMA, "Expected ',' after READFILE file identifier")
            target = self.parse_lvalue()
            return self.with_span(ReadFileStmt(file_expr, target), start_tok)

        if self.match(T.WRITEFILE):
            file_expr = self.parse_expression()
            self.consume(T.COMMA, "Expected ',' after WRITEFILE file identifier")
            data_expr = self.parse_expression()
            return self.with_span(WriteFileStmt(file_expr, data_expr), start_tok)

        if self.match(T.CLOSEFILE):
            file_expr = self.parse_expression()
            return self.with_span(CloseFileStmt(file_expr), start_tok)

        if self.match(T.SEEK):
            file_expr = self.parse_expression()
            self.consume(T.COMMA, "Expected ',' after SEEK file identifier")
            address_expr = self.parse_expression()
            return self.with_span(SeekStmt(file_expr, address_expr), start_tok)

        if self.match(T.GETRECORD):
            file_expr = self.parse_expression()
            self.consume(T.COMMA, "Expected ',' after GETRECORD file identifier")
            target = self.parse_lvalue()
            return self.with_span(GetRecordStmt(file_expr, target), start_tok)

        if self.match(T.PUTRECORD):
            file_expr = self.parse_expression()
            self.consume(T.COMMA, "Expected ',' after PUTRECORD file identifier")
            value_expr = self.parse_expression()
            return self.with_span(PutRecordStmt(file_expr, value_expr), start_tok)

        if self.match(T.IF):
            condition = self.parse_expression()
            self.consume(T.THEN, "Expected THEN after IF condition")

            then_body = self.parse_block({T.ELSE, T.ENDIF})

            else_body = []
            if self.match(T.ELSE):
                else_body = self.parse_block({T.ENDIF})

            self.consume(T.ENDIF, "Expected ENDIF")
            return self.with_span(IfStmt(condition, then_body, else_body), start_tok)

        if self.match(T.CASE):
            return self.with_span(self.parse_case(), start_tok)

        if self.match(T.WHILE):
            condition = self.parse_expression()
            body = self.parse_block({T.ENDWHILE})
            self.consume(T.ENDWHILE, "Expected ENDWHILE")
            return self.with_span(WhileStmt(condition, body), start_tok)

        if self.match(T.REPEAT):
            body = self.parse_block({T.UNTIL})
            self.consume(T.UNTIL, "Expected UNTIL")
            condition = self.parse_expression()
            return self.with_span(RepeatStmt(body, condition), start_tok)

        if self.match(T.FOR):
            name_tok = self.consume(T.IDENT, "Expected loop variable after FOR")
            self.consume(T.ASSIGN, "Expected ← after loop variable")

            start = self.parse_expression()

            self.consume(T.TO, "Expected TO in FOR statement")

            end = self.parse_expression()

            step = None
            if self.match(T.STEP):
                step = self.parse_expression()

            body = self.parse_block({T.NEXT})
            self.consume(T.NEXT, "Expected NEXT")

            if self.check(T.IDENT):
                next_tok = self.advance()

                if next_tok.lexeme.lower() != name_tok.lexeme.lower():
                    raise self.err(
                        next_tok,
                        f"NEXT variable {next_tok.lexeme!r} does not match "
                        f"FOR variable {name_tok.lexeme!r}",
                    )

            return self.with_span(
                ForStmt(name_tok.lexeme, start, end, step, body),
                start_tok,
            )

        if self.match(T.PROCEDURE):
            return self.with_span(self.parse_procedure_decl(), start_tok)

        if self.match(T.FUNCTION):
            return self.with_span(self.parse_function_decl(), start_tok)

        if self.match(T.CALL):
            name = self.consume(T.IDENT, "Expected procedure name after CALL").lexeme
            self.consume(T.LPAREN, "Expected '(' after procedure name")
            args = self.parse_arguments_after_lparen()
            return self.with_span(CallStmt(name, args), start_tok)

        if self.match(T.RETURN):
            expr = self.parse_expression()
            return self.with_span(ReturnStmt(expr), start_tok)

        if self.check(T.CLASS):
            raise self.err(
                self.peek(),
                "CLASS is not implemented in this minimal prototype",
            )

        if self.check(T.IDENT):
            save = self.current
            target = self.parse_lvalue()

            if self.match(T.ASSIGN):
                expr = self.parse_expression()
                return self.with_span(AssignStmt(target, expr), start_tok)

            self.current = save

        tok = self.peek()
        raise self.err(tok, f"Expected statement, got {tok.lexeme!r}")

    def parse_declare(self):
        name = self.consume(T.IDENT, "Expected identifier after DECLARE").lexeme
        self.consume(T.COLON, "Expected ':' after identifier in DECLARE")
        type_spec = self.parse_type()
        return DeclareStmt(name, type_spec)

    def parse_constant(self):
        name = self.consume(T.IDENT, "Expected identifier after CONSTANT").lexeme
        self.consume(T.EQUAL, "Expected '=' after constant name")
        expr = self.parse_literal_only()
        return ConstantStmt(name, expr)

    def parse_file_mode(self) -> str:
        if self.check_any(self.FILE_MODE_TOKENS):
            return self.advance().type

        tok = self.peek()
        raise self.err(tok, "Expected file mode READ, WRITE, APPEND or RANDOM")

    def parse_type_decl(self):
        name = self.consume(T.IDENT, "Expected type name after TYPE").lexeme

        if self.match(T.EQUAL):
            self.consume(T.LPAREN, "Expected '(' before enumerated values")

            values = [
                self.consume(
                    T.IDENT,
                    "Expected enumerated value name",
                ).lexeme
            ]

            while self.match(T.COMMA):
                values.append(
                    self.consume(
                        T.IDENT,
                        "Expected enumerated value name",
                    ).lexeme
                )

            self.consume(T.RPAREN, "Expected ')' after enumerated values")
            return TypeDeclEnum(name, values)

        fields = []
        self.skip_newlines()

        while not self.check(T.ENDTYPE):
            if self.check(T.EOF):
                raise IncompleteInput("Unexpected EOF: expected ENDTYPE")

            self.consume(T.DECLARE, "Expected DECLARE in record TYPE")
            field_name = self.consume(
                T.IDENT,
                "Expected field name in record TYPE",
            ).lexeme
            self.consume(T.COLON, "Expected ':' after record field name")
            field_type = self.parse_type()

            fields.append(RecordField(field_name, field_type))
            self.skip_newlines()

        self.consume(T.ENDTYPE, "Expected ENDTYPE")
        return TypeDeclRecord(name, fields)

    def parse_procedure_decl(self):
        name = self.consume(T.IDENT, "Expected procedure name").lexeme
        self.consume(T.LPAREN, "Expected '(' after procedure name")
        params = self.parse_params()
        self.consume(T.RPAREN, "Expected ')' after procedure parameters")

        body = self.parse_block({T.ENDPROCEDURE})
        self.consume(T.ENDPROCEDURE, "Expected ENDPROCEDURE")

        return ProcedureDecl(name, params, body)

    def parse_function_decl(self):
        name_tok = self.consume(T.IDENT, "Expected function name")
        self.consume(T.LPAREN, "Expected '(' after function name")
        params = self.parse_params()
        self.consume(T.RPAREN, "Expected ')' after function parameters")

        self.consume(T.RETURNS, "Expected RETURNS after function parameters")
        return_type = self.parse_type()

        for param in params:
            if param.passing == T.BYREF:
                raise self.err(
                    name_tok,
                    "FUNCTION parameters cannot be passed BYREF",
                )

        body = self.parse_block({T.ENDFUNCTION})
        self.consume(T.ENDFUNCTION, "Expected ENDFUNCTION")

        return FunctionDecl(name_tok.lexeme, params, return_type, body)

    def parse_params(self) -> list[Param]:
        params = []

        if self.check(T.RPAREN):
            return params

        passing = T.BYVAL

        while True:
            if self.match(T.BYVAL):
                passing = T.BYVAL
            elif self.match(T.BYREF):
                passing = T.BYREF

            name = self.consume(T.IDENT, "Expected parameter name").lexeme
            self.consume(T.COLON, "Expected ':' after parameter name")
            type_spec = self.parse_type()

            params.append(Param(name, type_spec, passing))

            if not self.match(T.COMMA):
                break

        return params

    def parse_case(self):
        self.consume(T.OF, "Expected OF after CASE")
        selector = self.parse_expression()

        clauses = []
        otherwise_body = []

        self.skip_newlines()

        while not self.check(T.EOF) and not self.check(T.ENDCASE):
            if self.match(T.OTHERWISE):
                self.consume(T.COLON, "Expected ':' after OTHERWISE")
                otherwise_body = self.parse_block({T.ENDCASE})
                break

            start = self.parse_expression()

            end = None
            if self.match(T.TO):
                end = self.parse_expression()

            self.consume(T.COLON, "Expected ':' after CASE value")

            body = self.parse_case_clause_body()
            clauses.append(CaseClause(start, end, body))

            self.skip_newlines()

        self.consume(T.ENDCASE, "Expected ENDCASE")
        return CaseStmt(selector, clauses, otherwise_body)

    def parse_case_clause_body(self) -> list:
        statements = []

        while True:
            self.skip_newlines()

            if self.check(T.EOF):
                raise IncompleteInput("Unexpected EOF: expected ENDCASE")

            if self.check(T.ENDCASE) or self.check(T.OTHERWISE):
                break

            if self.is_case_clause_start():
                break

            statements.append(self.parse_statement())

        return statements

    def is_case_clause_start(self) -> bool:
        if self.peek().type not in self.CASE_LABEL_STARTERS:
            return False

        i = self.current
        depth = 0

        while True:
            tok = self.tokens[i]

            if tok.type in {T.EOF, T.NEWLINE, T.ENDCASE, T.OTHERWISE}:
                return False

            if tok.type in {T.LPAREN, T.LBRACKET}:
                depth += 1

            elif tok.type in {T.RPAREN, T.RBRACKET}:
                depth = max(0, depth - 1)

            elif tok.type == T.COLON and depth == 0:
                return True

            i += 1

    def parse_type(self):
        if self.match(T.ARRAY):
            self.consume(T.LBRACKET, "Expected '[' after ARRAY")
            bounds = []

            while True:
                lower = self.parse_const_int()
                self.consume(T.COLON, "Expected ':' in array bounds")
                upper = self.parse_const_int()

                if lower > upper:
                    raise self.err(
                        self.previous(),
                        "Array lower bound cannot be greater than upper bound",
                    )

                bounds.append((lower, upper))

                if not self.match(T.COMMA):
                    break

            self.consume(T.RBRACKET, "Expected ']' after array bounds")
            self.consume(T.OF, "Expected OF after ARRAY[...]")

            element_type = self.parse_type()
            return ArrayType(tuple(bounds), element_type)

        if self.check_any(self.BASIC_TYPE_TOKENS):
            return self.advance().type

        if self.match(T.IDENT):
            return UserTypeRef(self.previous().lexeme)

        tok = self.peek()
        raise self.err(tok, "Expected data type")

    def parse_const_int(self) -> int:
        sign = 1

        if self.match(T.MINUS):
            sign = -1

        tok = self.consume(T.INT_LIT, "Expected integer literal")
        return sign * tok.literal

    def parse_literal_only(self):
        if self.match(T.MINUS):
            if self.match(T.INT_LIT):
                return LiteralExpr(-self.previous().literal)

            if self.match(T.REAL_LIT):
                return LiteralExpr(-self.previous().literal)

            raise self.err(self.peek(), "Expected numeric literal after '-'")

        if self.match(T.INT_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.REAL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.STRING_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.CHAR_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.DATE_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.BOOL_LIT):
            return LiteralExpr(self.previous().literal)

        raise self.err(self.peek(), "CONSTANT value must be a literal")

    def parse_lvalue(self):
        name_tok = self.consume(T.IDENT, "Expected variable name")
        expr = VariableExpr(name_tok.lexeme)
        target = VarTarget(name_tok.lexeme)

        while True:
            if self.match(T.LBRACKET):
                indices = self.parse_index_list_after_lbracket()

                if isinstance(expr, VariableExpr) and isinstance(target, VarTarget):
                    target = ArrayTarget(expr.name, indices)
                else:
                    target = IndexTarget(expr, indices)

                expr = ArrayAccessExpr(expr, indices)
                continue

            if self.match(T.DOT):
                field_name = self.consume(
                    T.IDENT,
                    "Expected field name after '.'",
                ).lexeme
                target = FieldTarget(expr, field_name)
                expr = FieldAccessExpr(expr, field_name)
                continue

            break

        return target

    def parse_expression(self, min_prec: int = 1):
        left = self.parse_unary()

        while True:
            tok = self.peek()
            prec = self.PRECEDENCE.get(tok.type)

            if prec is None or prec < min_prec:
                break

            op = self.advance()
            right = self.parse_expression(prec + 1)
            left = BinaryExpr(left, op, right)

        return left

    def parse_unary(self):
        if self.match(T.MINUS) or self.match(T.NOT):
            op = self.previous()
            right = self.parse_unary()
            return UnaryExpr(op, right)

        return self.parse_primary()

    def parse_primary(self):
        if self.match(T.INT_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.REAL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.STRING_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.CHAR_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.DATE_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.BOOL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.IDENT):
            name = self.previous().lexeme

            if self.match(T.LPAREN):
                args = self.parse_arguments_after_lparen()
                expr = CallExpr(name, args)
            else:
                expr = VariableExpr(name)

            while True:
                if self.match(T.LBRACKET):
                    indices = self.parse_index_list_after_lbracket()
                    expr = ArrayAccessExpr(expr, indices)
                    continue

                if self.match(T.DOT):
                    field_name = self.consume(
                        T.IDENT,
                        "Expected field name after '.'",
                    ).lexeme
                    expr = FieldAccessExpr(expr, field_name)
                    continue

                break

            return expr

        if self.match(T.LPAREN):
            expr = self.parse_expression()
            self.consume(T.RPAREN, "Expected ')' after expression")
            return expr

        tok = self.peek()

        if tok.type == T.EOF:
            raise IncompleteInput("Unexpected EOF: expected expression")

        raise self.err(tok, f"Expected expression, got {tok.lexeme!r}")

    def parse_arguments_after_lparen(self) -> list:
        args = []

        if not self.check(T.RPAREN):
            args.append(self.parse_expression())

            while self.match(T.COMMA):
                args.append(self.parse_expression())

        self.consume(T.RPAREN, "Expected ')' after arguments")
        return args

    def parse_index_list_after_lbracket(self) -> list:
        indices = [self.parse_expression()]

        while self.match(T.COMMA):
            indices.append(self.parse_expression())

        self.consume(T.RBRACKET, "Expected ']' after array index")
        return indices

    def skip_newlines(self):
        while self.match(T.NEWLINE):
            pass

    def match(self, *types: str) -> bool:
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True

        return False

    def consume(self, type_: str, message: str) -> Token:
        if self.check(type_):
            return self.advance()

        if self.check(T.EOF):
            raise IncompleteInput(message)

        raise self.err(self.peek(), message)

    def check(self, type_: str) -> bool:
        if self.is_at_end() and type_ != T.EOF:
            return False

        return self.peek().type == type_

    def check_any(self, types: set[str]) -> bool:
        return self.peek().type in types

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == T.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    @staticmethod
    def with_span(stmt, tok: Token):
        if hasattr(stmt, "span"):
            stmt.span = SourceSpan(tok.line, tok.col)

        return stmt

    @staticmethod
    def err(tok: Token, message: str) -> ParseError:
        return ParseError(
            f"ParseError at line {tok.line}, column {tok.col}: {message}"
        )
'''


INTERPRETER_PY = r'''from __future__ import annotations

import re
from typing import Any

from .ast_nodes import (
    ArrayAccessExpr,
    ArrayTarget,
    ArrayType,
    AssignStmt,
    BinaryExpr,
    CallExpr,
    CallStmt,
    CaseStmt,
    CloseFileStmt,
    ConstantStmt,
    DeclareStmt,
    FieldAccessExpr,
    FieldTarget,
    ForStmt,
    FunctionDecl,
    GetRecordStmt,
    IfStmt,
    IndexTarget,
    InputStmt,
    LiteralExpr,
    OpenFileStmt,
    OutputStmt,
    ProcedureDecl,
    Program,
    PutRecordStmt,
    ReadFileStmt,
    RepeatStmt,
    ReturnStmt,
    SeekStmt,
    TypeDeclEnum,
    TypeDeclRecord,
    UnaryExpr,
    VariableExpr,
    VarTarget,
    WhileStmt,
    WriteFileStmt,
)
from .errors import PseudoRuntimeError
from .runtime import (
    ArrayValue,
    EnumValue,
    RecordValue,
    Reference,
    Runtime,
    coerce_value,
    output_value,
    runtime_type_name,
    same_type,
    type_to_str,
)
from .tokens import T
from .values import Char, DateValue, make_date


class ReturnSignal(Exception):
    def __init__(self, value: Any, span: Any = None):
        super().__init__()
        self.value = value
        self.span = span


class Interpreter:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    @property
    def env(self):
        return self.runtime.env

    def execute_program(self, program: Program):
        for stmt in program.statements:
            if isinstance(stmt, TypeDeclRecord):
                self.runtime.reserve_record_type(stmt.name)

        for stmt in program.statements:
            if isinstance(stmt, TypeDeclEnum):
                self.execute(stmt)

        for stmt in program.statements:
            if isinstance(stmt, TypeDeclRecord):
                self.execute(stmt)

        for stmt in program.statements:
            if isinstance(stmt, (ProcedureDecl, FunctionDecl)):
                self.execute(stmt)

        for stmt in program.statements:
            if isinstance(
                stmt,
                (TypeDeclEnum, TypeDeclRecord, ProcedureDecl, FunctionDecl),
            ):
                continue

            try:
                self.execute(stmt)

            except ReturnSignal as signal:
                err = PseudoRuntimeError("RETURN can only be used inside FUNCTION")

                if signal.span is not None:
                    raise err.with_location(signal.span.line, signal.span.col) from None

                raise err from None

    def execute_block(self, statements: list[Any]):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt: Any):
        try:
            return self._execute(stmt)

        except PseudoRuntimeError as err:
            if err.line is None:
                span = getattr(stmt, "span", None)

                if span is not None:
                    raise err.with_location(span.line, span.col) from None

            raise

    def _execute(self, stmt: Any):
        if isinstance(stmt, TypeDeclEnum):
            self.runtime.register_enum_type(stmt.name, stmt.values)
            return

        if isinstance(stmt, TypeDeclRecord):
            self.runtime.register_record_type(stmt.name, stmt.fields)
            return

        if isinstance(stmt, DeclareStmt):
            type_spec = self.runtime.resolve_type_spec(stmt.type_spec)
            self.env.define(stmt.name, type_spec)
            return

        if isinstance(stmt, ConstantStmt):
            value = self.eval(stmt.expr)
            self.env.define_constant(stmt.name, value)
            return

        if isinstance(stmt, AssignStmt):
            value = self.eval(stmt.expr)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, InputStmt):
            type_spec = self.target_type(stmt.target)
            text = self.runtime.input_provider()
            value = parse_input_value(text, type_spec)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, OutputStmt):
            values = [
                output_value(self.eval(expr))
                for expr in stmt.exprs
            ]

            self.runtime.output_writer("".join(values))
            return

        if isinstance(stmt, OpenFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            self.runtime.file_system.open_file(file_id, stmt.mode)
            return

        if isinstance(stmt, ReadFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            type_spec = self.target_type(stmt.target)

            if not same_type(type_spec, T.STRING):
                raise PseudoRuntimeError(
                    f"READFILE target must be STRING, got {type_to_str(type_spec)}"
                )

            line = self.runtime.file_system.read_file(file_id)
            self.assign_target(stmt.target, line)
            return

        if isinstance(stmt, WriteFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            data = output_value(self.eval(stmt.data_expr))
            self.runtime.file_system.write_file(file_id, data)
            return

        if isinstance(stmt, CloseFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            self.runtime.file_system.close_file(file_id)
            return

        if isinstance(stmt, SeekStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            address = self.require_int(self.eval(stmt.address_expr))
            self.runtime.file_system.seek(file_id, address)
            return

        if isinstance(stmt, GetRecordStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            value = self.runtime.file_system.get_record(file_id)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, PutRecordStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            value = self.eval(stmt.value_expr)
            self.runtime.file_system.put_record(file_id, value)
            return

        if isinstance(stmt, IfStmt):
            condition = self.require_bool(self.eval(stmt.condition))

            if condition:
                self.execute_block(stmt.then_body)
            else:
                self.execute_block(stmt.else_body)

            return

        if isinstance(stmt, CaseStmt):
            self.execute_case(stmt)
            return

        if isinstance(stmt, WhileStmt):
            while self.require_bool(self.eval(stmt.condition)):
                self.execute_block(stmt.body)

            return

        if isinstance(stmt, RepeatStmt):
            while True:
                self.execute_block(stmt.body)

                if self.require_bool(self.eval(stmt.condition)):
                    break

            return

        if isinstance(stmt, ForStmt):
            self.execute_for(stmt)
            return

        if isinstance(stmt, ProcedureDecl):
            self.runtime.register_procedure(stmt)
            return

        if isinstance(stmt, FunctionDecl):
            self.runtime.register_function(stmt)
            return

        if isinstance(stmt, CallStmt):
            self.call_procedure(stmt.name, stmt.args)
            return

        if isinstance(stmt, ReturnStmt):
            value = self.eval(stmt.expr)
            raise ReturnSignal(value, stmt.span)

        raise PseudoRuntimeError(f"Unknown statement type: {stmt!r}")

    def eval_file_identifier(self, expr: Any) -> str:
        return self.require_string(self.eval(expr))

    def execute_case(self, stmt: CaseStmt):
        selector = self.eval(stmt.selector)

        for clause in stmt.clauses:
            start = self.eval(clause.start)
            end = self.eval(clause.end) if clause.end is not None else None

            if self.case_matches(selector, start, end):
                self.execute_block(clause.body)
                return

        self.execute_block(stmt.otherwise_body)

    def case_matches(self, selector: Any, start: Any, end: Any | None) -> bool:
        if end is None:
            return selector == start

        return (
            self.compare_values(start, T.LESS_EQUAL, selector)
            and self.compare_values(selector, T.LESS_EQUAL, end)
        )

    def execute_for(self, stmt: ForStmt):
        start = self.require_int(self.eval(stmt.start))
        end = self.require_int(self.eval(stmt.end))
        step = self.require_int(self.eval(stmt.step)) if stmt.step is not None else 1

        if step == 0:
            raise PseudoRuntimeError("FOR loop STEP cannot be 0")

        if self.env.exists(stmt.var_name):
            binding = self.env.get_binding(stmt.var_name)

            if not same_type(binding.type_spec, T.INTEGER):
                raise PseudoRuntimeError("FOR loop variable must be INTEGER")
        else:
            if self.runtime.strict:
                raise PseudoRuntimeError(
                    f"Undefined FOR loop variable {stmt.var_name!r}"
                )

            self.env.define(stmt.var_name, T.INTEGER, 0)

        i = start

        def keep_going():
            return i <= end if step > 0 else i >= end

        while keep_going():
            self.env.assign(stmt.var_name, i)
            self.execute_block(stmt.body)
            i += step

    def call_procedure(self, name: str, arg_exprs: list[Any]):
        decl = self.runtime.get_procedure(name)
        prepared = self.prepare_arguments(
            decl.params,
            arg_exprs,
            f"PROCEDURE {decl.name}",
        )

        with self.runtime.scope(f"PROCEDURE {decl.name}"):
            self.bind_prepared_arguments(prepared)

            try:
                self.execute_block(decl.body)

            except ReturnSignal as signal:
                err = PseudoRuntimeError("RETURN cannot be used in a PROCEDURE")

                if signal.span is not None:
                    raise err.with_location(signal.span.line, signal.span.col) from None

                raise err from None

    def call_function(self, name: str, arg_exprs: list[Any]) -> Any:
        decl = self.runtime.get_function(name)
        prepared = self.prepare_arguments(
            decl.params,
            arg_exprs,
            f"FUNCTION {decl.name}",
        )
        return_type = self.runtime.resolve_type_spec(decl.return_type)

        with self.runtime.scope(f"FUNCTION {decl.name}"):
            self.bind_prepared_arguments(prepared)

            try:
                self.execute_block(decl.body)

            except ReturnSignal as signal:
                return coerce_value(signal.value, return_type)

        raise PseudoRuntimeError(f"FUNCTION {decl.name!r} did not RETURN a value")

    def prepare_arguments(
        self,
        params: list[Any],
        arg_exprs: list[Any],
        context: str,
    ) -> list[tuple[str, str, Any, Any]]:
        if len(arg_exprs) != len(params):
            raise PseudoRuntimeError(
                f"{context} expects {len(params)} argument(s), "
                f"got {len(arg_exprs)}"
            )

        prepared = []

        for param, arg_expr in zip(params, arg_exprs):
            param_type = self.runtime.resolve_type_spec(param.type_spec)

            if param.passing == T.BYREF:
                reference = self.make_reference(arg_expr)

                if not same_type(reference.type_spec, param_type):
                    raise PseudoRuntimeError(
                        f"BYREF parameter {param.name!r} expects "
                        f"{type_to_str(param_type)}, "
                        f"got {type_to_str(reference.type_spec)}"
                    )

                prepared.append((param.name, T.BYREF, param_type, reference))

            else:
                value = self.eval(arg_expr)
                value = coerce_value(value, param_type)
                prepared.append((param.name, T.BYVAL, param_type, value))

        return prepared

    def bind_prepared_arguments(self, prepared: list[tuple[str, str, Any, Any]]):
        for name, passing, type_spec, payload in prepared:
            if passing == T.BYREF:
                self.env.define_reference(name, type_spec, payload)
            else:
                self.env.define(name, type_spec, payload)

    def make_reference(self, expr: Any) -> Reference:
        if isinstance(expr, VariableExpr):
            binding = self.env.get_binding(expr.name)

            if binding.constant:
                raise PseudoRuntimeError(
                    f"Cannot pass constant {binding.original_name!r} BYREF"
                )

            return Reference(
                type_spec=binding.type_spec,
                getter=binding.read,
                setter=binding.write,
                description=expr.name,
            )

        if isinstance(expr, ArrayAccessExpr):
            arr = self.eval(expr.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("BYREF indexed argument is not an ARRAY")

            indices = [
                self.require_int(self.eval(e))
                for e in expr.indices
            ]

            arr.validate_indices(indices)

            return Reference(
                type_spec=arr.type_spec.element_type,
                getter=lambda arr=arr, indices=indices: arr.get(indices),
                setter=lambda value, arr=arr, indices=indices: arr.set(indices, value),
                description="ARRAY element",
            )

        if isinstance(expr, FieldAccessExpr):
            record = self.eval(expr.record_expr)

            if not isinstance(record, RecordValue):
                raise PseudoRuntimeError("BYREF field argument is not a record")

            field_type = record.field_type(expr.field_name)

            return Reference(
                type_spec=field_type,
                getter=lambda record=record, name=expr.field_name: record.get(name),
                setter=lambda value, record=record, name=expr.field_name: record.set(
                    name,
                    value,
                ),
                description="record field",
            )

        raise PseudoRuntimeError("BYREF argument must be a variable, ARRAY element or record field")

    def assign_target(self, target: Any, value: Any):
        if isinstance(target, VarTarget):
            self.env.assign(target.name, value)
            return

        if isinstance(target, ArrayTarget):
            arr = self.env.get(target.name)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError(f"{target.name!r} is not an ARRAY")

            indices = [
                self.require_int(self.eval(expr))
                for expr in target.indices
            ]

            arr.set(indices, value)
            return

        if isinstance(target, IndexTarget):
            arr = self.eval(target.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed assignment target is not an ARRAY")

            indices = [
                self.require_int(self.eval(expr))
                for expr in target.indices
            ]

            arr.set(indices, value)
            return

        if isinstance(target, FieldTarget):
            record = self.eval(target.record_expr)

            if not isinstance(record, RecordValue):
                raise PseudoRuntimeError("Field assignment target is not a record")

            record.set(target.field_name, value)
            return

        raise PseudoRuntimeError(f"Invalid assignment target {target!r}")

    def target_type(self, target: Any) -> Any:
        if isinstance(target, VarTarget):
            if self.env.exists(target.name):
                return self.env.get_binding(target.name).type_spec

            if self.runtime.strict:
                raise PseudoRuntimeError(f"Undefined variable {target.name!r}")

            return T.STRING

        if isinstance(target, ArrayTarget):
            arr = self.env.get(target.name)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError(f"{target.name!r} is not an ARRAY")

            return arr.type_spec.element_type

        if isinstance(target, IndexTarget):
            arr = self.eval(target.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed target is not an ARRAY")

            return arr.type_spec.element_type

        if isinstance(target, FieldTarget):
            record = self.eval(target.record_expr)

            if not isinstance(record, RecordValue):
                raise PseudoRuntimeError("Field target is not a record")

            return record.field_type(target.field_name)

        raise PseudoRuntimeError(f"Invalid target {target!r}")

    def eval(self, expr: Any) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, VariableExpr):
            if self.env.exists(expr.name):
                return self.env.get(expr.name)

            if self.runtime.has_enum_value(expr.name):
                return self.runtime.get_enum_value(expr.name)

            raise PseudoRuntimeError(f"Undefined variable {expr.name!r}")

        if isinstance(expr, ArrayAccessExpr):
            arr = self.eval(expr.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed value is not an ARRAY")

            indices = [
                self.require_int(self.eval(e))
                for e in expr.indices
            ]

            return arr.get(indices)

        if isinstance(expr, FieldAccessExpr):
            record = self.eval(expr.record_expr)

            if not isinstance(record, RecordValue):
                raise PseudoRuntimeError("Field access target is not a record")

            return record.get(expr.field_name)

        if isinstance(expr, UnaryExpr):
            right = self.eval(expr.right)

            if expr.op.type == T.MINUS:
                self.require_number(right)
                return -right

            if expr.op.type == T.NOT:
                return not self.require_bool(right)

            raise PseudoRuntimeError(f"Unknown unary operator {expr.op.lexeme!r}")

        if isinstance(expr, BinaryExpr):
            if expr.op.type == T.AND:
                left = self.require_bool(self.eval(expr.left))

                if not left:
                    return False

                return self.require_bool(self.eval(expr.right))

            if expr.op.type == T.OR:
                left = self.require_bool(self.eval(expr.left))

                if left:
                    return True

                return self.require_bool(self.eval(expr.right))

            left = self.eval(expr.left)
            right = self.eval(expr.right)
            return self.eval_binary(left, expr.op, right)

        if isinstance(expr, CallExpr):
            if self.runtime.has_function(expr.name):
                return self.call_function(expr.name, expr.args)

            if self.runtime.has_procedure(expr.name):
                raise PseudoRuntimeError(
                    f"PROCEDURE {expr.name!r} cannot be used as a FUNCTION"
                )

            args = [
                self.eval(arg)
                for arg in expr.args
            ]

            return self.call_builtin(expr.name, args)

        raise PseudoRuntimeError(f"Unknown expression type: {expr!r}")

    def eval_binary(self, left: Any, op: Any, right: Any):
        t = op.type

        if t == T.PLUS:
            self.require_number(left)
            self.require_number(right)
            return left + right

        if t == T.MINUS:
            self.require_number(left)
            self.require_number(right)
            return left - right

        if t == T.STAR:
            self.require_number(left)
            self.require_number(right)
            return left * right

        if t == T.SLASH:
            self.require_number(left)
            self.require_number(right)

            if right == 0:
                raise PseudoRuntimeError("Division by zero")

            return float(left) / float(right)

        if t == T.DIV:
            left_i = self.require_int(left)
            right_i = self.require_int(right)

            if right_i == 0:
                raise PseudoRuntimeError("Division by zero")

            return int(left_i / right_i)

        if t == T.MOD:
            left_i = self.require_int(left)
            right_i = self.require_int(right)

            if right_i == 0:
                raise PseudoRuntimeError("Modulo by zero")

            return left_i % right_i

        if t == T.AMP:
            if not isinstance(left, str) or not isinstance(right, str):
                raise PseudoRuntimeError("& requires STRING or CHAR operands")

            return str(left) + str(right)

        if t == T.EQUAL:
            return left == right

        if t == T.NOT_EQUAL:
            return left != right

        if t in {
            T.LESS,
            T.LESS_EQUAL,
            T.GREATER,
            T.GREATER_EQUAL,
        }:
            return self.compare_values(left, t, right)

        if t == T.AND:
            return self.require_bool(left) and self.require_bool(right)

        if t == T.OR:
            return self.require_bool(left) or self.require_bool(right)

        raise PseudoRuntimeError(f"Unknown binary operator {op.lexeme!r}")

    def compare_values(self, left: Any, op_type: str, right: Any) -> bool:
        if self.is_number(left) and self.is_number(right):
            a, b = left, right

        elif isinstance(left, str) and isinstance(right, str):
            a, b = str(left), str(right)

        elif isinstance(left, DateValue) and isinstance(right, DateValue):
            a, b = left.key(), right.key()

        elif (
            isinstance(left, EnumValue)
            and isinstance(right, EnumValue)
            and same_type(left.type_spec, right.type_spec)
        ):
            a, b = left.ordinal, right.ordinal

        else:
            raise PseudoRuntimeError(
                f"Cannot compare {runtime_type_name(left)} "
                f"with {runtime_type_name(right)}"
            )

        if op_type == T.LESS:
            return a < b

        if op_type == T.LESS_EQUAL:
            return a <= b

        if op_type == T.GREATER:
            return a > b

        if op_type == T.GREATER_EQUAL:
            return a >= b

        raise PseudoRuntimeError(f"Unknown comparison operator {op_type}")

    def call_builtin(self, name: str, args: list[Any]) -> Any:
        upper = name.upper()

        if upper == "EOF":
            self.require_arg_count(upper, args, 1)
            file_id = self.require_string(args[0])
            return self.runtime.file_system.eof(file_id)

        if upper == "LENGTH":
            self.require_arg_count(upper, args, 1)
            s = self.require_string(args[0])
            return len(s)

        if upper == "RIGHT":
            self.require_arg_count(upper, args, 2)
            s = self.require_string(args[0])
            x = self.require_int(args[1])

            if x < 0:
                raise PseudoRuntimeError("RIGHT length cannot be negative")

            if x == 0:
                return ""

            return s[-x:]

        if upper == "MID":
            self.require_arg_count(upper, args, 3)
            s = self.require_string(args[0])
            x = self.require_int(args[1])
            y = self.require_int(args[2])

            if x < 1:
                raise PseudoRuntimeError(
                    "MID start position is 1-based and must be >= 1"
                )

            if y < 0:
                raise PseudoRuntimeError("MID length cannot be negative")

            start = x - 1
            return s[start:start + y]

        if upper == "LCASE":
            self.require_arg_count(upper, args, 1)
            c = self.require_char(args[0])
            return Char(c.lower())

        if upper == "UCASE":
            self.require_arg_count(upper, args, 1)
            c = self.require_char(args[0])
            return Char(c.upper())

        if upper == "INT":
            self.require_arg_count(upper, args, 1)
            self.require_number(args[0])
            return int(args[0])

        if upper == "RAND":
            self.require_arg_count(upper, args, 1)
            x = self.require_int(args[0])

            if x <= 0:
                raise PseudoRuntimeError("RAND argument must be positive")

            return self.runtime.rng.random() * x

        raise PseudoRuntimeError(f"Unknown function {name!r}")

    @staticmethod
    def require_arg_count(name: str, args: list[Any], count: int):
        if len(args) != count:
            raise PseudoRuntimeError(
                f"{name} expects {count} argument(s), got {len(args)}"
            )

    @staticmethod
    def is_number(value: Any) -> bool:
        return type(value) is int or type(value) is float

    def require_number(self, value: Any):
        if not self.is_number(value):
            raise PseudoRuntimeError(
                f"Expected number, got {runtime_type_name(value)}"
            )

    @staticmethod
    def require_int(value: Any) -> int:
        if type(value) is int:
            return value

        raise PseudoRuntimeError(
            f"Expected INTEGER, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_bool(value: Any) -> bool:
        if type(value) is bool:
            return value

        raise PseudoRuntimeError(
            f"Expected BOOLEAN, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_string(value: Any) -> str:
        if isinstance(value, str):
            return str(value)

        raise PseudoRuntimeError(
            f"Expected STRING, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_char(value: Any) -> Char:
        if isinstance(value, Char):
            return value

        if isinstance(value, str) and len(value) == 1:
            return Char(value)

        raise PseudoRuntimeError(
            f"Expected CHAR, got {runtime_type_name(value)}"
        )


def parse_input_value(text: str, type_spec: Any) -> Any:
    if isinstance(type_spec, ArrayType):
        raise PseudoRuntimeError("Cannot INPUT a whole ARRAY")

    t = type_to_str(type_spec)

    try:
        if t == T.INTEGER:
            return int(text)

        if t == T.REAL:
            return float(text)

        if t == T.CHAR:
            if len(text) != 1:
                raise PseudoRuntimeError(
                    "CHAR input must contain exactly one character"
                )

            return Char(text)

        if t == T.STRING:
            return text

        if t == T.BOOLEAN:
            upper = text.strip().upper()

            if upper == "TRUE":
                return True

            if upper == "FALSE":
                return False

            raise PseudoRuntimeError("BOOLEAN input must be TRUE or FALSE")

        if t == T.DATE:
            match = re.fullmatch(
                r"(\d{1,2})/(\d{1,2})/(\d{4})",
                text.strip(),
            )

            if not match:
                raise PseudoRuntimeError(
                    "DATE input must use dd/mm/yyyy format"
                )

            day, month, year = map(int, match.groups())
            return make_date(day, month, year)

    except ValueError as e:
        raise PseudoRuntimeError(f"Invalid input for {t}: {text!r}") from e

    raise PseudoRuntimeError(f"Unsupported INPUT type {type_to_str(type_spec)}")
'''


RUNNER_PY = r'''from __future__ import annotations

from pathlib import Path

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .runtime import LocalFileSystem, Runtime


def run_source(
    source: str,
    runtime: Runtime | None = None,
    *,
    strict: bool | None = None,
) -> Runtime:
    if runtime is None:
        runtime = Runtime(strict=bool(strict))

    if strict is None:
        strict = runtime.strict

    tokens = Lexer(source, strict=strict).scan_tokens()
    program = Parser(tokens).parse_program()
    Interpreter(runtime).execute_program(program)

    return runtime


def run_file(path: str, *, strict: bool = False):
    program_path = Path(path)

    with program_path.open("r", encoding="utf-8") as f:
        source = f.read()

    runtime = Runtime(
        strict=strict,
        file_system=LocalFileSystem(program_path.resolve().parent),
    )
    run_source(source, runtime, strict=strict)
'''


README_MD = r'''# psei

Minimal Cambridge-style pseudocode interpreter.

This project implements a practical subset of Cambridge International AS & A Level
Computer Science 9618-style pseudocode.

## Current supported subset

Supported:

- basic declarations:
  - `INTEGER`
  - `REAL`
  - `CHAR`
  - `STRING`
  - `BOOLEAN`
  - `DATE`
- constants with literal values
- assignment using `←`
- one-dimensional and two-dimensional arrays
- whole-array assignment with cloning semantics
- user-defined enumerated types:
  - `TYPE Season = (Spring, Summer, Autumn, Winter)`
- user-defined record types:
  - `TYPE ... ENDTYPE`
  - field access using dot notation, for example `Pupil.LastName`
  - record assignment with cloning semantics
  - arrays of records
- `INPUT`
- `OUTPUT`
- text file handling:
  - `OPENFILE ... FOR READ`
  - `OPENFILE ... FOR WRITE`
  - `OPENFILE ... FOR APPEND`
  - `READFILE`
  - `WRITEFILE`
  - `CLOSEFILE`
  - `EOF(...)`
- random file handling:
  - `OPENFILE ... FOR RANDOM`
  - `SEEK`
  - `GETRECORD`
  - `PUTRECORD`
- arithmetic:
  - `+`
  - `-`
  - `*`
  - `/`
  - `DIV`
  - `MOD`
- comparisons:
  - `=`
  - `<>`
  - `<`
  - `<=`
  - `>`
  - `>=`
- logic:
  - `AND`
  - `OR`
  - `NOT`
  - `AND` and `OR` use short-circuit evaluation
- selection:
  - `IF ... THEN ... ELSE ... ENDIF`
  - `CASE OF ... OTHERWISE ... ENDCASE`
- loops:
  - `FOR ... TO ... STEP ... NEXT`
  - `WHILE ... ENDWHILE`
  - `REPEAT ... UNTIL`
- procedures:
  - `PROCEDURE ... ENDPROCEDURE`
  - `CALL ProcedureName(...)`
  - `BYVAL`
  - `BYREF`
- functions:
  - `FUNCTION ... RETURNS ... ENDFUNCTION`
  - `RETURN`
  - function calls inside expressions
- built-in functions:
  - `EOF`
  - `RIGHT`
  - `MID`
  - `LENGTH`
  - `LCASE`
  - `UCASE`
  - `INT`
  - `RAND`

Not implemented yet:

- sets
- pointers
- object-oriented pseudocode

## File handling notes

`run_source()` uses an in-memory file system by default. This keeps tests and
REPL-style execution deterministic and avoids writing temporary files to the
project directory.

`run_file()` uses a local file system rooted at the directory containing the
pseudocode source file, so relative file names are resolved beside the program
being run.

Text file example:

```text
DECLARE LineOfText : STRING

OPENFILE "FileA.txt" FOR READ
WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE
CLOSEFILE "FileA.txt"
```

Random file example:

```text
OPENFILE "StudentFile.Dat" FOR RANDOM
SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", Pupil
SEEK "StudentFile.Dat", 10
GETRECORD "StudentFile.Dat", LoadedPupil
CLOSEFILE "StudentFile.Dat"
```

Random files store runtime values at integer addresses. With the local file
system implementation, random files are persisted using Python pickle. That is
an interpreter implementation detail, not part of Cambridge pseudocode.

## User-defined type notes

Enumerated types:

```text
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE ThisSeason : Season
ThisSeason ← Spring
```

Enumerated values are case-insensitive identifiers. If a variable has the same
name as an enumerated value, the variable shadows the enumerated value.

Record types:

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE FirstName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.YearGroup ← 6
```

Record fields are accessed using dot notation. Record values are copied on
assignment, so assigning one record variable to another does not alias their
field storage.

Arrays of records are supported:

```text
DECLARE Form : ARRAY[1:30] OF StudentRecord

Form[1].LastName ← "Ali"
Form[1].YearGroup ← 12
```

Record fields and array elements can be passed `BYREF`.

## Procedure and function notes

Parameters are passed by value by default.

```text
PROCEDURE AddOne(X : INTEGER)
```

`BYVAL` and `BYREF` can be used explicitly:

```text
PROCEDURE Swap(BYREF X : INTEGER, Y : INTEGER)
```

The passing mode persists across comma-separated parameters until another
`BYVAL` or `BYREF` keyword appears. In the example above, both `X` and `Y` are
passed by reference.

Functions cannot have `BYREF` parameters.

`RETURN` is valid only inside a function. It immediately exits the function and
returns its value.

Top-level type, procedure and function declarations are registered before normal
statements are executed, so forward calls are supported.

## Strict mode semantics

Strict mode is intentionally limited and explicit. It is a Cambridge-style
guardrail, not yet a complete validator for every presentation rule in the
pseudocode guide.

Strict mode currently guarantees:

- assignment must use `←`; ASCII `<-` is rejected
- variables must be declared before assignment
- identifiers are restricted to ASCII letters, digits and `_`
- identifiers must start with an ASCII letter

Non-strict mode currently allows:

- assignment using either `←` or ASCII `<-`
- assignment to an undeclared variable, creating it with an inferred type
- non-ASCII alphabetic characters in identifiers

Both modes still perform core runtime checks, including:

- declared assignment type checks
- constant immutability
- constant values must be literals
- array bounds checks
- unknown user-defined type checks
- record field checks
- enumerated type assignment checks
- file mode checks
- text file EOF checks
- random file address checks
- arithmetic errors such as division by zero
- Boolean condition checks for `IF`, `WHILE` and `REPEAT`
- procedure/function arity checks
- function return type checks
- `BYREF` argument lvalue and type checks

Run with strict mode:

```bash
python -m interpreter run path/to/program.pseudo --strict
```

## Development

Run tests:

```bash
python -m pytest -q
```
'''


TEXT_FILE_COPY_PSEUDO = r'''DECLARE LineOfText : STRING

OPENFILE "FileA.txt" FOR WRITE
WRITEFILE "FileA.txt", "First"
WRITEFILE "FileA.txt", ""
WRITEFILE "FileA.txt", "Last"
CLOSEFILE "FileA.txt"

OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE

WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText

   IF LineOfText = "" THEN
      WRITEFILE "FileB.txt", "----------------"
   ELSE
      WRITEFILE "FileB.txt", LineOfText
   ENDIF
ENDWHILE

CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"

OPENFILE "FileB.txt" FOR READ

WHILE NOT EOF("FileB.txt")
   READFILE "FileB.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "FileB.txt"
'''

TEXT_FILE_COPY_OUT = r'''First
----------------
Last
'''


TEXT_FILE_APPEND_PSEUDO = r'''DECLARE LineOfText : STRING

OPENFILE "Log.txt" FOR WRITE
WRITEFILE "Log.txt", "A"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR APPEND
WRITEFILE "Log.txt", "B"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR READ

WHILE NOT EOF("Log.txt")
   READFILE "Log.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "Log.txt"
'''

TEXT_FILE_APPEND_OUT = r'''A
B
'''


RANDOM_FILE_RECORD_PSEUDO = r'''TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord
DECLARE LoadedPupil : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.YearGroup ← 6

OPENFILE "StudentFile.Dat" FOR RANDOM

SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", Pupil

Pupil.LastName ← "Changed"
Pupil.YearGroup ← 99

SEEK "StudentFile.Dat", 10
GETRECORD "StudentFile.Dat", LoadedPupil

CLOSEFILE "StudentFile.Dat"

OUTPUT LoadedPupil.LastName, ":", LoadedPupil.YearGroup
OUTPUT Pupil.LastName, ":", Pupil.YearGroup
'''

RANDOM_FILE_RECORD_OUT = r'''Johnson:6
Changed:99
'''


TEST_PHASE3_PY = r'''import pytest

from interpreter.errors import PseudoRuntimeError
from interpreter.runner import run_source
from interpreter.runtime import Runtime


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_text_file_write_read_and_eof():
    source = """
DECLARE LineOfText : STRING

OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "one"
WRITEFILE "A.txt", "two"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ

WHILE NOT EOF("A.txt")
   READFILE "A.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "A.txt"
"""

    assert run_capture(source) == ["one", "two"]


def test_text_file_append():
    source = """
DECLARE LineOfText : STRING

OPENFILE "Log.txt" FOR WRITE
WRITEFILE "Log.txt", "A"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR APPEND
WRITEFILE "Log.txt", "B"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR READ

WHILE NOT EOF("Log.txt")
   READFILE "Log.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "Log.txt"
"""

    assert run_capture(source) == ["A", "B"]


def test_random_file_record_put_and_get():
    source = """
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord
DECLARE Loaded : StudentRecord

Pupil.LastName ← "Ali"
Pupil.YearGroup ← 12

OPENFILE "Students.dat" FOR RANDOM
SEEK "Students.dat", 5
PUTRECORD "Students.dat", Pupil

Pupil.LastName ← "Changed"
Pupil.YearGroup ← 99

SEEK "Students.dat", 5
GETRECORD "Students.dat", Loaded
CLOSEFILE "Students.dat"

OUTPUT Loaded.LastName, ":", Loaded.YearGroup
OUTPUT Pupil.LastName, ":", Pupil.YearGroup
"""

    assert run_capture(source) == ["Ali:12", "Changed:99"]


def test_readfile_target_must_be_string():
    source = """
DECLARE N : INTEGER

OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "text"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ
READFILE "A.txt", N
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_eof_requires_open_read_file():
    source = """
OUTPUT EOF("Missing.txt")
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_writefile_requires_write_or_append_mode():
    source = """
OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "text"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ
WRITEFILE "A.txt", "bad"
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_random_get_missing_record_is_error():
    source = """
DECLARE X : INTEGER

OPENFILE "Data.dat" FOR RANDOM
SEEK "Data.dat", 10
GETRECORD "Data.dat", X
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)
'''


def main() -> None:
    write("interpreter/ast_nodes.py", AST_NODES_PY)
    write("interpreter/tokens.py", TOKENS_PY)
    write("interpreter/runtime.py", RUNTIME_PY)
    write("interpreter/parser.py", PARSER_PY)
    write("interpreter/interpreter.py", INTERPRETER_PY)
    write("interpreter/runner.py", RUNNER_PY)
    write("README.md", README_MD)

    write("examples/passing/text_file_copy.pseudo", TEXT_FILE_COPY_PSEUDO)
    write("examples/passing/text_file_copy.out", TEXT_FILE_COPY_OUT)

    write("examples/passing/text_file_append.pseudo", TEXT_FILE_APPEND_PSEUDO)
    write("examples/passing/text_file_append.out", TEXT_FILE_APPEND_OUT)

    write("examples/passing/random_file_record.pseudo", RANDOM_FILE_RECORD_PSEUDO)
    write("examples/passing/random_file_record.out", RANDOM_FILE_RECORD_OUT)

    write("tests/test_phase3.py", TEST_PHASE3_PY)

    print("Phase 3 file handling patch complete.")


if __name__ == "__main__":
    main()
