from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from psei.errors import PseudoRuntimeError
from psei.tokens import T


def _norm_identifier(name: str) -> str:
    return name.lower()


@dataclass
class ClassFieldSpec:
    original_name: str
    type_spec: Any
    access: str = T.PUBLIC
    owner_name: str = ""


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
        key = _norm_identifier(field_name)
        fields = self.all_fields()

        if key not in fields:
            raise PseudoRuntimeError(
                f"Class {self.name!r} has no property {field_name!r}"
            )

        return fields[key]

    def find_method(self, method_name: str) -> tuple[Any | None, ClassType | None]:
        key = _norm_identifier(method_name)

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
    def create(
        cls,
        type_spec: ClassType,
        *,
        max_array_elements: int | None = None,
    ) -> ObjectValue:
        from .types import clone_value, default_value

        if not type_spec.completed:
            raise PseudoRuntimeError(
                f"Class {type_spec.name!r} is not completely defined"
            )

        fields = {}

        for key, spec in type_spec.all_fields().items():
            fields[key] = clone_value(
                default_value(
                    spec.type_spec,
                    max_array_elements=max_array_elements,
                )
            )

        return cls(type_spec, fields)

    def get(self, field_name: str) -> Any:
        key = _norm_identifier(field_name)
        self.type_spec.get_field(field_name)
        return self.fields[key]

    def set(self, field_name: str, value: Any):
        from .types import coerce_value

        key = _norm_identifier(field_name)
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


__all__ = [
    "ClassFieldSpec",
    "ClassType",
    "NullObjectValue",
    "ObjectValue",
    "SuperProxy",
]
