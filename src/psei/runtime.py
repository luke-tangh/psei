from __future__ import annotations

import copy
import itertools
import json
import random
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from .ast_nodes import ArrayType, ClassFieldDecl, UserTypeRef
from .errors import PseudoRuntimeError
from .tokens import T
from .values import Char, DateValue, make_date


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
            fields[key] = clone_value(default_value(field.type_spec))

        return cls(type_spec, fields)

    def clone(self) -> RecordValue:
        return RecordValue(
            self.type_spec,
            {
                key: clone_value(value)
                for key, value in self.fields.items()
            },
        )

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
class ClassFieldSpec:
    original_name: str
    type_spec: Any
    access: str = T.PUBLIC


@dataclass
class ClassType:
    name: str
    parent_name: str | None = None
    parent: ClassType | None = None
    fields: dict[str, ClassFieldSpec] = dc_field(default_factory=dict)
    methods: dict[str, Any] = dc_field(default_factory=dict)
    initializers: list[Any] = dc_field(default_factory=list)
    completed: bool = False

    def all_fields(self) -> dict[str, ClassFieldSpec]:
        fields = {}

        if self.parent is not None:
            fields.update(self.parent.all_fields())

        fields.update(self.fields)
        return fields

    def get_field(self, field_name: str) -> ClassFieldSpec:
        key = norm_identifier(field_name)
        fields = self.all_fields()

        if key not in fields:
            raise PseudoRuntimeError(
                f"Class {self.name!r} has no property {field_name!r}"
            )

        return fields[key]

    def find_method(self, method_name: str) -> tuple[Any | None, ClassType | None]:
        key = norm_identifier(method_name)

        if key in self.methods:
            return self.methods[key], self

        if self.parent is not None:
            return self.parent.find_method(method_name)

        return None, None

    def has_method(self, method_name: str) -> bool:
        method, _owner = self.find_method(method_name)
        return method is not None


@dataclass
class ObjectValue:
    type_spec: ClassType
    fields: dict[str, Any]

    @classmethod
    def create(cls, type_spec: ClassType) -> ObjectValue:
        if not type_spec.completed:
            raise PseudoRuntimeError(
                f"Class {type_spec.name!r} is not completely defined"
            )

        fields = {}

        for key, spec in type_spec.all_fields().items():
            fields[key] = clone_value(default_value(spec.type_spec))

        return cls(type_spec, fields)

    def get(self, field_name: str) -> Any:
        key = norm_identifier(field_name)
        self.type_spec.get_field(field_name)
        return self.fields[key]

    def set(self, field_name: str, value: Any):
        key = norm_identifier(field_name)
        spec = self.type_spec.get_field(field_name)
        self.fields[key] = coerce_value(value, spec.type_spec)

    def field_type(self, field_name: str) -> Any:
        return self.type_spec.get_field(field_name).type_spec


@dataclass(frozen=True)
class NullObjectValue:
    type_spec: ClassType

    def __str__(self) -> str:
        return "NULL"


@dataclass
class SuperProxy:
    object_value: ObjectValue
    start_class: ClassType

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
            data[index_tuple] = clone_value(default_value(type_spec.element_type))

        return cls(type_spec, data)

    def clone(self):
        return ArrayValue(
            self.type_spec,
            {
                key: clone_value(value)
                for key, value in self.data.items()
            },
        )

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
    from integer address to a cloned runtime value.
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

        return clone_value(records[address])

    def put_record(self, file_id: str, value: Any):
        handle = self._require_mode(file_id, {T.RANDOM})
        self.random_files[handle.file_id][handle.random_pointer] = clone_value(value)


class LocalFileSystem(InMemoryFileSystem):
    """
    File-system abstraction used by run_file().

    Text files are written as UTF-8 text. Random files are persisted as JSON
    using an explicit runtime-value serializer. This avoids loading arbitrary
    Python pickle data from pseudocode-controlled file paths.
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
                try:
                    raw = path.read_text(encoding="utf-8")

                    if raw.strip():
                        data = json.loads(raw)
                        self.random_files[key] = deserialize_random_file(data)
                    else:
                        self.random_files[key] = {}

                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    KeyError,
                    ValueError,
                    TypeError,
                ) as e:
                    raise PseudoRuntimeError(
                        f"Random file {file_id!r} is not a valid psei random file"
                    ) from e
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

            data = serialize_random_file(self.random_files.get(key, {}))
            text = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            path.write_text(text + "\n", encoding="utf-8", newline="\n")

        super().close_file(file_id)


RANDOM_FILE_FORMAT = "psei-random-v1"


def serialize_random_file(records: dict[int, Any]) -> dict[str, Any]:
    return {
        "format": RANDOM_FILE_FORMAT,
        "records": {
            str(address): serialize_value(value)
            for address, value in sorted(records.items())
        },
    }


def deserialize_random_file(data: Any) -> dict[int, Any]:
    if not isinstance(data, dict) or data.get("format") != RANDOM_FILE_FORMAT:
        raise PseudoRuntimeError("Random file is not a valid psei random file")

    records_data = data.get("records")

    if not isinstance(records_data, dict):
        raise PseudoRuntimeError("Random file records must be an object")

    records: dict[int, Any] = {}

    for address_text, value_data in records_data.items():
        address = int(address_text)

        if address < 0:
            raise PseudoRuntimeError("Random file address cannot be negative")

        records[address] = deserialize_value(value_data)

    return records


def serialize_type_spec(type_spec: Any) -> dict[str, Any]:
    if isinstance(type_spec, ArrayType):
        return {
            "kind": "array",
            "bounds": [
                [lower, upper]
                for lower, upper in type_spec.bounds
            ],
            "element_type": serialize_type_spec(type_spec.element_type),
        }

    if isinstance(type_spec, EnumType):
        return {
            "kind": "enum",
            "name": type_spec.name,
            "values": list(type_spec.values),
        }

    if isinstance(type_spec, RecordType):
        return {
            "kind": "record",
            "name": type_spec.name,
            "fields": [
                {
                    "name": field.original_name,
                    "type": serialize_type_spec(field.type_spec),
                }
                for field in type_spec.fields.values()
            ],
        }

    if isinstance(type_spec, ClassType):
        return {
            "kind": "class",
            "name": type_spec.name,
        }

    t = type_to_str(type_spec)

    if t in BASIC_TYPES:
        return {
            "kind": "basic",
            "name": t,
        }

    raise PseudoRuntimeError(
        f"Cannot serialise type {type_to_str(type_spec)!r}"
    )


def deserialize_type_spec(data: Any) -> Any:
    if not isinstance(data, dict):
        raise PseudoRuntimeError("Serialized type must be an object")

    kind = data.get("kind")

    if kind == "basic":
        name = str(data["name"]).upper()

        if name not in BASIC_TYPES:
            raise PseudoRuntimeError(f"Unknown serialized basic type {name!r}")

        return name

    if kind == "array":
        bounds = []

        for item in data["bounds"]:
            if not isinstance(item, list) or len(item) != 2:
                raise PseudoRuntimeError("Serialized array bound is invalid")

            lower = int(item[0])
            upper = int(item[1])

            if lower > upper:
                raise PseudoRuntimeError(
                    "Serialized array lower bound exceeds upper bound"
                )

            bounds.append((lower, upper))

        return ArrayType(
            tuple(bounds),
            deserialize_type_spec(data["element_type"]),
        )

    if kind == "enum":
        values = tuple(str(value) for value in data["values"])

        if not values:
            raise PseudoRuntimeError("Serialized enum has no values")

        return EnumType(
            name=str(data["name"]),
            values=values,
            value_to_index={
                norm_identifier(value): index
                for index, value in enumerate(values)
            },
        )

    if kind == "record":
        field_specs: dict[str, RecordFieldSpec] = {}

        for field in data["fields"]:
            field_name = str(field["name"])
            field_specs[norm_identifier(field_name)] = RecordFieldSpec(
                original_name=field_name,
                type_spec=deserialize_type_spec(field["type"]),
            )

        return RecordType(
            name=str(data["name"]),
            fields=field_specs,
            completed=True,
        )

    if kind == "class":
        return ClassType(
            name=str(data["name"]),
            completed=True,
        )

    raise PseudoRuntimeError(f"Unknown serialized type kind {kind!r}")


def serialize_value(value: Any) -> dict[str, Any]:
    if type(value) is bool:
        return {
            "kind": "boolean",
            "value": value,
        }

    if type(value) is int:
        return {
            "kind": "integer",
            "value": value,
        }

    if type(value) is float:
        return {
            "kind": "real",
            "value": value,
        }

    if isinstance(value, Char):
        return {
            "kind": "char",
            "value": str(value),
        }

    if type(value) is str:
        return {
            "kind": "string",
            "value": value,
        }

    if isinstance(value, DateValue):
        return {
            "kind": "date",
            "day": value.day,
            "month": value.month,
            "year": value.year,
        }

    if isinstance(value, EnumValue):
        return {
            "kind": "enum",
            "type": serialize_type_spec(value.type_spec),
            "name": value.name,
        }

    if isinstance(value, RecordValue):
        return {
            "kind": "record",
            "type": serialize_type_spec(value.type_spec),
            "fields": {
                (
                    value.type_spec.fields[key].original_name
                    if key in value.type_spec.fields
                    else key
                ): serialize_value(field_value)
                for key, field_value in value.fields.items()
            },
        }

    if isinstance(value, ArrayValue):
        return {
            "kind": "array",
            "type": serialize_type_spec(value.type_spec),
            "data": [
                {
                    "indices": list(indices),
                    "value": serialize_value(element),
                }
                for indices, element in sorted(value.data.items())
            ],
        }

    if isinstance(value, NullObjectValue):
        return {
            "kind": "null_object",
            "type": serialize_type_spec(value.type_spec),
        }

    if isinstance(value, ObjectValue):
        raise PseudoRuntimeError(
            "Object values cannot be persisted in RANDOM files; "
            "store records or scalar values instead"
        )

    raise PseudoRuntimeError(
        f"Cannot serialise value of type {runtime_type_name(value)}"
    )


def deserialize_value(data: Any) -> Any:
    if not isinstance(data, dict):
        raise PseudoRuntimeError("Serialized value must be an object")

    kind = data.get("kind")

    if kind == "boolean":
        value = data["value"]

        if type(value) is not bool:
            raise PseudoRuntimeError("Serialized BOOLEAN value is invalid")

        return value

    if kind == "integer":
        value = data["value"]

        if type(value) is not int:
            raise PseudoRuntimeError("Serialized INTEGER value is invalid")

        return value

    if kind == "real":
        value = data["value"]

        if type(value) is not int and type(value) is not float:
            raise PseudoRuntimeError("Serialized REAL value is invalid")

        return float(value)

    if kind == "char":
        return Char(str(data["value"]))

    if kind == "string":
        value = data["value"]

        if type(value) is not str:
            raise PseudoRuntimeError("Serialized STRING value is invalid")

        return value

    if kind == "date":
        return make_date(
            int(data["day"]),
            int(data["month"]),
            int(data["year"]),
        )

    if kind == "enum":
        type_spec = deserialize_type_spec(data["type"])

        if not isinstance(type_spec, EnumType):
            raise PseudoRuntimeError("Serialized enum type is invalid")

        name = str(data["name"])
        return EnumValue(type_spec, name, type_spec.ordinal_of(name))

    if kind == "record":
        type_spec = deserialize_type_spec(data["type"])

        if not isinstance(type_spec, RecordType):
            raise PseudoRuntimeError("Serialized record type is invalid")

        fields_data = data["fields"]

        if not isinstance(fields_data, dict):
            raise PseudoRuntimeError("Serialized record fields are invalid")

        return RecordValue(
            type_spec,
            {
                norm_identifier(field_name): deserialize_value(field_value)
                for field_name, field_value in fields_data.items()
            },
        )

    if kind == "array":
        type_spec = deserialize_type_spec(data["type"])

        if not isinstance(type_spec, ArrayType):
            raise PseudoRuntimeError("Serialized array type is invalid")

        values: dict[tuple[int, ...], Any] = {}

        for item in data["data"]:
            indices = tuple(int(index) for index in item["indices"])
            values[indices] = deserialize_value(item["value"])

        return ArrayValue(type_spec, values)

    if kind == "null_object":
        type_spec = deserialize_type_spec(data["type"])

        if not isinstance(type_spec, ClassType):
            raise PseudoRuntimeError("Serialized NULL object type is invalid")

        return NullObjectValue(type_spec)

    raise PseudoRuntimeError(f"Unknown serialized value kind {kind!r}")


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
        self.classes: dict[str, ClassType] = {}

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
        self.ensure_no_recursive_record_type(record_type)
        record_type.completed = True

    def ensure_no_recursive_record_type(self, record_type: RecordType):
        target_key = norm_identifier(record_type.name)

        def visit_type(type_spec: Any, seen: set[str]):
            if isinstance(type_spec, ArrayType):
                visit_type(type_spec.element_type, seen)
                return

            if not isinstance(type_spec, RecordType):
                return

            key = norm_identifier(type_spec.name)

            if key == target_key:
                raise PseudoRuntimeError(
                    f"Recursive record TYPE {record_type.name!r} "
                    "is not supported"
                )

            if key in seen:
                return

            next_seen = seen | {key}

            for nested_field in type_spec.fields.values():
                visit_type(nested_field.type_spec, next_seen)

        for field in record_type.fields.values():
            visit_type(field.type_spec, set())

    def reserve_class_type(self, name: str, parent_name: str | None):
        key = norm_identifier(name)

        if key in self.types or key in self.classes:
            raise PseudoRuntimeError(f"CLASS {name!r} is already defined")

        class_type = ClassType(name=name, parent_name=parent_name)
        self.classes[key] = class_type
        self.types[key] = class_type

    def register_class_type(self, decl: Any):
        key = norm_identifier(decl.name)

        if key not in self.classes:
            self.reserve_class_type(decl.name, decl.parent_name)

        class_type = self.classes[key]

        if class_type.completed:
            raise PseudoRuntimeError(f"CLASS {decl.name!r} is already defined")

        if class_type.parent_name is not None:
            parent_key = norm_identifier(class_type.parent_name)

            if parent_key not in self.classes:
                raise PseudoRuntimeError(
                    f"Unknown superclass {class_type.parent_name!r}"
                )

            if parent_key == key:
                raise PseudoRuntimeError(
                    f"CLASS {decl.name!r} cannot inherit from itself"
                )

            class_type.parent = self.classes[parent_key]

        self.ensure_no_inheritance_cycle(class_type)

        fields: dict[str, ClassFieldSpec] = {}
        methods: dict[str, Any] = {}

        inherited_fields = (
            class_type.parent.all_fields()
            if class_type.parent is not None
            else {}
        )

        for member in decl.members:
            if isinstance(member, ClassFieldDecl):
                field_key = norm_identifier(member.name)

                if field_key in fields:
                    raise PseudoRuntimeError(
                        f"Duplicate property {member.name!r} in CLASS {decl.name!r}"
                    )

                if field_key in inherited_fields:
                    raise PseudoRuntimeError(
                        f"Property {member.name!r} in CLASS {decl.name!r} "
                        "duplicates an inherited property"
                    )

                fields[field_key] = ClassFieldSpec(
                    original_name=member.name,
                    type_spec=self.resolve_type_spec(member.type_spec),
                    access=member.access,
                )

            else:
                method_key = norm_identifier(member.name)

                if (
                    method_key == norm_identifier("NEW")
                    and member.kind != T.PROCEDURE
                ):
                    raise PseudoRuntimeError(
                        "Constructor NEW must be a PROCEDURE"
                    )

                if method_key in methods:
                    raise PseudoRuntimeError(
                        f"Duplicate method {member.name!r} in CLASS {decl.name!r}"
                    )

                methods[method_key] = member

        class_type.fields = fields
        class_type.methods = methods
        class_type.initializers = decl.initializers
        class_type.completed = True
        self.ensure_no_inheritance_cycle(class_type)

    def ensure_no_inheritance_cycle(self, class_type: ClassType):
        target_key = norm_identifier(class_type.name)
        seen = {target_key}
        current = class_type.parent

        while current is not None:
            key = norm_identifier(current.name)

            if key == target_key or key in seen:
                raise PseudoRuntimeError(
                    f"Inheritance cycle detected involving CLASS "
                    f"{class_type.name!r}"
                )

            seen.add(key)
            current = current.parent

    def get_class(self, name: str) -> ClassType:
        key = norm_identifier(name)

        if key not in self.classes:
            raise PseudoRuntimeError(f"Unknown CLASS {name!r}")

        class_type = self.classes[key]

        if not class_type.completed:
            raise PseudoRuntimeError(f"CLASS {name!r} is not completely defined")

        return class_type

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

    if isinstance(type_spec, ClassType):
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

    if isinstance(a, ClassType) and isinstance(b, ClassType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, UserTypeRef) and isinstance(b, UserTypeRef):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, UserTypeRef) and isinstance(b, (EnumType, RecordType, ClassType)):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(b, UserTypeRef) and isinstance(a, (EnumType, RecordType, ClassType)):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, str) and isinstance(b, str):
        return a.upper() == b.upper()

    return False


def is_class_assignable(source: ClassType, target: ClassType) -> bool:
    current: ClassType | None = source

    while current is not None:
        if same_type(current, target):
            return True

        current = current.parent

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

    if isinstance(type_spec, ClassType):
        return NullObjectValue(type_spec)

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


def clone_value(value: Any) -> Any:
    if isinstance(value, ArrayValue):
        return value.clone()

    if isinstance(value, RecordValue):
        return value.clone()

    if isinstance(value, EnumValue):
        return EnumValue(value.type_spec, value.name, value.ordinal)

    if isinstance(value, ObjectValue):
        return value

    if isinstance(value, NullObjectValue):
        return NullObjectValue(value.type_spec)

    if isinstance(value, Char):
        return Char(str(value))

    return value


def infer_type(value: Any) -> Any:
    if isinstance(value, ArrayValue):
        return value.type_spec

    if isinstance(value, EnumValue):
        return value.type_spec

    if isinstance(value, RecordValue):
        return value.type_spec

    if isinstance(value, ObjectValue):
        return value.type_spec

    if isinstance(value, NullObjectValue):
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

        return ArrayValue(
            type_spec,
            {
                key: coerce_value(element, type_spec.element_type)
                for key, element in value.data.items()
            },
        )

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

        fields = {}

        for key, field in type_spec.fields.items():
            if key not in value.fields:
                raise PseudoRuntimeError(
                    f"Record value for {type_to_str(type_spec)} "
                    f"is missing field {field.original_name!r}"
                )

            fields[key] = coerce_value(value.fields[key], field.type_spec)

        return RecordValue(type_spec, fields)

    if isinstance(type_spec, ClassType):
        if isinstance(value, NullObjectValue):
            if not is_class_assignable(value.type_spec, type_spec):
                raise PseudoRuntimeError(
                    f"Cannot assign {type_to_str(value.type_spec)} "
                    f"to {type_to_str(type_spec)}"
                )

            return NullObjectValue(type_spec)

        if not isinstance(value, ObjectValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not is_class_assignable(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return value

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

    if isinstance(value, ObjectValue):
        return f"<{type_to_str(value.type_spec)} object>"

    if isinstance(value, NullObjectValue):
        return "NULL"

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

    if isinstance(value, ObjectValue):
        return f"<{type_to_str(value.type_spec)} object>"

    if isinstance(value, NullObjectValue):
        return "NULL"

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, Char):
        if value == "\0":
            return ""

        return str(value)

    return str(value)
