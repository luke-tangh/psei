from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psei.errors import PseudoRuntimeError

from .types import coerce_value, debug_value, infer_type, norm_identifier, type_to_str
from .values import Reference


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
        from .types import default_value

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


__all__ = [
    "Binding",
    "Environment",
]
