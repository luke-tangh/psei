from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from psei.ast_nodes import ArrayType, PointerType
from psei.errors import PseudoRuntimeError
from psei.tokens import T


@dataclass
class Reference:
    type_spec: Any
    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    description: str = ""

    def get(self) -> Any:
        return self.getter()

    def set(self, value: Any):
        # Local import avoids circular import with runtime.types.
        from .types import coerce_value

        self.setter(coerce_value(value, self.type_spec))


@dataclass(frozen=True)
class PointerValue:
    type_spec: PointerType
    reference: Reference | None = None

    def __str__(self) -> str:
        if self.reference is None:
            return "NULL"

        from .types import type_to_str

        return f"<{type_to_str(self.type_spec)}>"


@dataclass
class ArrayValue:
    type_spec: ArrayType
    data: dict[tuple[int, ...], Any]

    @classmethod
    def create(cls, type_spec: ArrayType) -> ArrayValue:
        # Local import avoids circular import with runtime.types.
        from .types import clone_value, default_value

        ranges = [
            range(lower, upper + 1)
            for lower, upper in type_spec.bounds
        ]

        data = {}

        for index_tuple in itertools.product(*ranges):
            data[index_tuple] = clone_value(default_value(type_spec.element_type))

        return cls(type_spec, data)

    def clone(self):
        from .types import clone_value

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
        from .types import coerce_value

        key = self.validate_indices(indices)
        self.data[key] = coerce_value(value, self.type_spec.element_type)


__all__ = [
    "ArrayValue",
    "PointerValue",
    "Reference",
]
