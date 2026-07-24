from __future__ import annotations

import copy
import itertools
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .ast_nodes import ArrayType
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
class Binding:
    original_name: str
    type_spec: Any
    value: Any
    constant: bool = False


class Environment:
    def __init__(self, *, strict: bool = False):
        self.strict = strict
        self.bindings: dict[str, Binding] = {}

    @staticmethod
    def norm(name: str) -> str:
        return name.lower()

    def exists(self, name: str) -> bool:
        return self.norm(name) in self.bindings

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

    def define_constant(self, name: str, value: Any):
        type_spec = infer_type(value)
        self.define(name, type_spec, value, constant=True)

    def assign(self, name: str, value: Any):
        key = self.norm(name)

        if key not in self.bindings:
            if self.strict:
                raise PseudoRuntimeError(f"Undefined variable {name!r}")

            inferred = infer_type(value)
            self.define(name, inferred, value)
            return

        binding = self.bindings[key]

        if binding.constant:
            raise PseudoRuntimeError(
                f"Cannot assign to constant {binding.original_name!r}"
            )

        binding.value = coerce_value(value, binding.type_spec)

    def get(self, name: str) -> Any:
        return self.get_binding(name).value

    def get_binding(self, name: str) -> Binding:
        key = self.norm(name)

        if key not in self.bindings:
            raise PseudoRuntimeError(f"Undefined variable {name!r}")

        return self.bindings[key]

    def dump(self) -> str:
        if not self.bindings:
            return "(no variables)"

        lines = []

        for binding in self.bindings.values():
            const = "CONSTANT " if binding.constant else ""

            lines.append(
                f"{const}{binding.original_name} : "
                f"{type_to_str(binding.type_spec)} = "
                f"{debug_value(binding.value)}"
            )

        return "\n".join(lines)


class Runtime:
    def __init__(
        self,
        *,
        strict: bool = False,
        input_provider: Callable[[], str] | None = None,
        output_writer: Callable[[str], Any] | None = None,
        rng: random.Random | None = None,
    ):
        self.strict = strict
        self.env = Environment(strict=strict)
        self.input_provider = input_provider if input_provider is not None else input
        self.output_writer = output_writer if output_writer is not None else print
        self.rng = rng if rng is not None else random.Random()


def type_to_str(type_spec: Any) -> str:
    if isinstance(type_spec, ArrayType):
        bounds = ",".join(
            f"{lower}:{upper}"
            for lower, upper in type_spec.bounds
        )

        return f"ARRAY[{bounds}] OF {type_to_str(type_spec.element_type)}"

    return str(type_spec).upper()


def same_type(a: Any, b: Any) -> bool:
    if isinstance(a, ArrayType) and isinstance(b, ArrayType):
        return (
            a.bounds == b.bounds
            and same_type(a.element_type, b.element_type)
        )

    if isinstance(a, str) and isinstance(b, str):
        return a.upper() == b.upper()

    return False


def default_value(type_spec: Any) -> Any:
    if isinstance(type_spec, ArrayType):
        return ArrayValue.create(type_spec)

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

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, Char):
        if value == "\0":
            return ""

        return str(value)

    return str(value)
