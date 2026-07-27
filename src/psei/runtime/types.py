from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psei.ast_nodes import ArrayType, PointerType, SetTypeSpec, UserTypeRef
from psei.errors import PseudoRuntimeError
from psei.tokens import T
from psei.values import Char, DateValue

from .oop import ClassType, NullObjectValue, ObjectValue
from .values import ArrayValue, PointerValue


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
class SetType:
    name: str
    element_type: Any
    completed: bool = True


@dataclass
class SetValue:
    type_spec: SetType
    elements: dict[Any, Any]

    @classmethod
    def create(cls, type_spec: SetType) -> SetValue:
        return cls(type_spec, {})

    def clone(self) -> SetValue:
        return SetValue(
            self.type_spec,
            {
                key: clone_value(value)
                for key, value in self.elements.items()
            },
        )


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


def type_to_str(type_spec: Any) -> str:
    if isinstance(type_spec, ArrayType):
        bounds = ",".join(
            f"{lower}:{upper}"
            for lower, upper in type_spec.bounds
        )

        return f"ARRAY[{bounds}] OF {type_to_str(type_spec.element_type)}"

    if isinstance(type_spec, PointerType):
        return f"^{type_to_str(type_spec.target_type)}"

    if isinstance(type_spec, SetTypeSpec):
        return f"SET OF {type_to_str(type_spec.element_type)}"

    if isinstance(type_spec, SetType):
        if type_spec.name:
            return type_spec.name

        return f"SET OF {type_to_str(type_spec.element_type)}"

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

    if isinstance(a, PointerType) and isinstance(b, PointerType):
        return same_type(a.target_type, b.target_type)

    if isinstance(a, (SetType, SetTypeSpec)) and isinstance(
        b,
        (SetType, SetTypeSpec),
    ):
        name_a = getattr(a, "name", "")
        name_b = getattr(b, "name", "")

        if name_a and name_b:
            return norm_identifier(name_a) == norm_identifier(name_b)

        return same_type(a.element_type, b.element_type)

    if isinstance(a, EnumType) and isinstance(b, EnumType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, RecordType) and isinstance(b, RecordType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, ClassType) and isinstance(b, ClassType):
        return norm_identifier(a.name) == norm_identifier(b.name)

    user_types = (EnumType, RecordType, ClassType, SetType)

    if isinstance(a, UserTypeRef) and isinstance(b, UserTypeRef):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, UserTypeRef) and isinstance(b, user_types):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(b, UserTypeRef) and isinstance(a, user_types):
        return norm_identifier(a.name) == norm_identifier(b.name)

    if isinstance(a, str) and isinstance(b, str):
        return a.upper() == b.upper()

    return False


def ensure_set_element_type_supported(type_spec: Any):
    if isinstance(
        type_spec,
        (ArrayType, PointerType, SetType, SetTypeSpec, RecordType, ClassType),
    ):
        raise PseudoRuntimeError(
            f"SET element type cannot be {type_to_str(type_spec)}"
        )


def set_element_key(value: Any) -> tuple[Any, ...]:
    if type(value) is bool:
        return (T.BOOLEAN, value)

    if type(value) is int:
        return (T.INTEGER, value)

    if type(value) is float:
        return (T.REAL, value)

    if isinstance(value, Char):
        return (T.CHAR, str(value))

    if type(value) is str:
        return (T.STRING, value)

    if isinstance(value, DateValue):
        return (T.DATE, value.key())

    if isinstance(value, EnumValue):
        return (
            "ENUM",
            norm_identifier(value.type_spec.name),
            value.ordinal,
        )

    raise PseudoRuntimeError(
        f"SET elements must be scalar values, got {runtime_type_name(value)}"
    )


def make_set_value(set_type: SetType, values: list[Any]) -> SetValue:
    elements = {}

    for value in values:
        coerced = coerce_value(value, set_type.element_type)
        elements[set_element_key(coerced)] = clone_value(coerced)

    return SetValue(set_type, elements)


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

    if isinstance(type_spec, PointerType):
        return PointerValue(type_spec)

    if isinstance(type_spec, SetTypeSpec):
        return SetValue.create(
            SetType(name="", element_type=type_spec.element_type)
        )

    if isinstance(type_spec, SetType):
        return SetValue.create(type_spec)

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

    if isinstance(value, SetValue):
        return value.clone()

    if isinstance(value, PointerValue):
        return PointerValue(value.type_spec, value.reference)

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

    if isinstance(value, SetValue):
        return value.type_spec

    if isinstance(value, PointerValue):
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

    if type(value) is str:
        return T.STRING

    if isinstance(value, DateValue):
        return T.DATE

    raise PseudoRuntimeError(f"Cannot infer type of value {value!r}")


def coerce_value(value: Any, type_spec: Any) -> Any:
    if isinstance(type_spec, UserTypeRef):
        raise PseudoRuntimeError(
            f"Cannot assign value to unresolved type {type_spec.name!r}"
        )

    if isinstance(type_spec, PointerType):
        if not isinstance(value, PointerValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not same_type(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return PointerValue(type_spec, value.reference)

    if isinstance(type_spec, SetTypeSpec):
        type_spec = SetType(name="", element_type=type_spec.element_type)

    if isinstance(type_spec, SetType):
        if not isinstance(value, SetValue):
            raise PseudoRuntimeError(
                f"Expected {type_to_str(type_spec)}, "
                f"got {runtime_type_name(value)}"
            )

        if not same_type(value.type_spec, type_spec):
            raise PseudoRuntimeError(
                f"Cannot assign {type_to_str(value.type_spec)} "
                f"to {type_to_str(type_spec)}"
            )

        return make_set_value(type_spec, list(value.elements.values()))

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

        raise PseudoRuntimeError(
            f"Expected CHAR, got {runtime_type_name(value)}"
        )

    if t == T.STRING:
        if type(value) is str:
            return value

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

    if isinstance(value, SetValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, PointerValue):
        return str(value)

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

    if type(value) is str:
        return repr(value)

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    return str(value)


def output_value(value: Any) -> str:
    if isinstance(value, ArrayValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, EnumValue):
        return value.name

    if isinstance(value, SetValue):
        return f"<{type_to_str(value.type_spec)}>"

    if isinstance(value, PointerValue):
        return str(value)

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


__all__ = [
    "BASIC_TYPES",
    "EnumType",
    "EnumValue",
    "RecordFieldSpec",
    "RecordType",
    "RecordValue",
    "SetType",
    "SetValue",
    "clone_value",
    "coerce_value",
    "debug_value",
    "default_value",
    "ensure_set_element_type_supported",
    "infer_type",
    "is_class_assignable",
    "make_set_value",
    "norm_identifier",
    "output_value",
    "runtime_type_name",
    "same_type",
    "type_to_str",
]
