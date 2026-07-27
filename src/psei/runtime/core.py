from __future__ import annotations

import copy
import random
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from psei.ast_nodes import (
    ArrayType,
    ClassFieldDecl,
    Param,
    PointerType,
    SetTypeSpec,
    UserTypeRef,
)
from psei.errors import PseudoRuntimeError
from psei.tokens import T

from .environment import Environment
from .files import InMemoryFileSystem
from .oop import ClassFieldSpec, ClassType
from .types import (
    DEFAULT_MAX_ARRAY_ELEMENTS,
    EnumType,
    EnumValue,
    RecordFieldSpec,
    RecordType,
    SetType,
    ensure_set_element_type_supported,
    norm_identifier,
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
        max_steps: int | None = 1_000_000,
        max_array_elements: int | None = DEFAULT_MAX_ARRAY_ELEMENTS,
        max_call_depth: int | None = 1_000,
        max_output_chars: int | None = 1_000_000,
    ):
        for limit_name, limit_value in {
            "max_steps": max_steps,
            "max_array_elements": max_array_elements,
            "max_call_depth": max_call_depth,
            "max_output_chars": max_output_chars,
        }.items():
            if limit_value is not None and limit_value < 0:
                raise ValueError(f"{limit_name} must be non-negative or None")

        self.strict = strict

        self.max_steps = max_steps
        self.steps_executed = 0

        self.max_array_elements = max_array_elements

        self.max_call_depth = max_call_depth
        self.call_depth = 0

        self.max_output_chars = max_output_chars
        self.output_chars_written = 0

        self.global_env = Environment(
            strict=strict,
            name="global",
            max_array_elements=max_array_elements,
        )
        self._env_stack: list[Environment] = [self.global_env]

        self.types: dict[str, Any] = {}
        self.enum_values: dict[str, EnumValue] = {}
        self.classes: dict[str, ClassType] = {}

        self.procedures: dict[str, Any] = {}
        self.functions: dict[str, Any] = {}

        self.file_system = (
            file_system
            if file_system is not None
            else InMemoryFileSystem()
        )

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
            max_array_elements=self.max_array_elements,
        )
        self._env_stack.append(env)
        return env

    def pop_scope(self) -> Environment:
        if len(self._env_stack) == 1:
            raise PseudoRuntimeError("Cannot pop the global scope")

        return self._env_stack.pop()

    def tick(self, amount: int = 1):
        if amount <= 0:
            return

        self.steps_executed += amount

        if (
            self.max_steps is not None
            and self.steps_executed > self.max_steps
        ):
            raise PseudoRuntimeError(
                f"Execution step limit exceeded "
                f"({self.max_steps} step(s))"
            )

    @contextmanager
    def call_frame(self, name: str = "call"):
        self.call_depth += 1

        try:
            if (
                self.max_call_depth is not None
                and self.call_depth > self.max_call_depth
            ):
                raise PseudoRuntimeError(
                    f"Call depth limit exceeded during {name} "
                    f"({self.max_call_depth} call(s))"
                )

            yield

        finally:
            self.call_depth -= 1

    def output(self, text: str):
        text = str(text)
        new_total = self.output_chars_written + len(text)

        if (
            self.max_output_chars is not None
            and new_total > self.max_output_chars
        ):
            raise PseudoRuntimeError(
                f"OUTPUT limit exceeded "
                f"({self.max_output_chars} character(s))"
            )

        self.output_chars_written = new_total
        self.output_writer(text)

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

        if isinstance(type_spec, PointerType):
            return PointerType(
                self.resolve_type_spec(type_spec.target_type),
            )

        if isinstance(type_spec, SetTypeSpec):
            element_type = self.resolve_type_spec(type_spec.element_type)
            ensure_set_element_type_supported(element_type)
            return SetType(name="", element_type=element_type)

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

    def register_pointer_type(self, name: str, target_type: Any):
        key = norm_identifier(name)

        if key in self.types:
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        self.types[key] = PointerType(self.resolve_type_spec(target_type))

    def register_set_type(self, name: str, element_type: Any):
        key = norm_identifier(name)

        if key in self.types:
            raise PseudoRuntimeError(f"TYPE {name!r} is already defined")

        resolved_element_type = self.resolve_type_spec(element_type)
        ensure_set_element_type_supported(resolved_element_type)

        self.types[key] = SetType(
            name=name,
            element_type=resolved_element_type,
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

            # A pointer to a record is allowed; this is how linked structures are
            # normally modelled.
            if isinstance(type_spec, PointerType):
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

            if not class_type.parent.completed:
                raise PseudoRuntimeError(
                    f"Superclass {class_type.parent_name!r} is not completely defined"
                )

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
                    owner_name=decl.name,
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

                method = copy.copy(member)
                method.params = self.resolve_params(
                    member.params,
                    f"METHOD {decl.name}.{member.name}",
                )

                if method.return_type is not None:
                    method.return_type = self.resolve_type_spec(method.return_type)

                methods[method_key] = method

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

    def resolve_params(self, params: list[Any], context: str) -> list[Param]:
        resolved = []
        seen: set[str] = set()

        for param in params:
            key = norm_identifier(param.name)

            if key in seen:
                raise PseudoRuntimeError(
                    f"Duplicate parameter {param.name!r} in {context}"
                )

            seen.add(key)
            resolved.append(
                Param(
                    name=param.name,
                    type_spec=self.resolve_type_spec(param.type_spec),
                    passing=param.passing,
                )
            )

        return resolved

    def register_procedure(self, decl: Any):
        key = Environment.norm(decl.name)

        if key in self.procedures:
            raise PseudoRuntimeError(f"PROCEDURE {decl.name!r} is already defined")

        if key in self.functions:
            raise PseudoRuntimeError(
                f"Identifier {decl.name!r} is already defined as a FUNCTION"
            )

        resolved = copy.copy(decl)
        resolved.params = self.resolve_params(
            decl.params,
            f"PROCEDURE {decl.name}",
        )

        self.procedures[key] = resolved

    def register_function(self, decl: Any):
        key = Environment.norm(decl.name)

        if key in self.functions:
            raise PseudoRuntimeError(f"FUNCTION {decl.name!r} is already defined")

        if key in self.procedures:
            raise PseudoRuntimeError(
                f"Identifier {decl.name!r} is already defined as a PROCEDURE"
            )

        resolved = copy.copy(decl)
        resolved.params = self.resolve_params(
            decl.params,
            f"FUNCTION {decl.name}",
        )
        resolved.return_type = self.resolve_type_spec(decl.return_type)

        self.functions[key] = resolved

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


__all__ = [
    "Runtime",
]
