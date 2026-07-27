from __future__ import annotations

from typing import Any

from psei.ast_nodes import ArrayType, PointerType
from psei.errors import PseudoRuntimeError
from psei.tokens import T
from psei.values import Char, DateValue, make_date

from .oop import ClassType, NullObjectValue, ObjectValue
from .types import (
    BASIC_TYPES,
    EnumType,
    EnumValue,
    RecordFieldSpec,
    RecordType,
    RecordValue,
    SetType,
    SetValue,
    make_set_value,
    norm_identifier,
    runtime_type_name,
    type_to_str,
)
from .values import ArrayValue, PointerValue


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

    if isinstance(type_spec, PointerType):
        return {
            "kind": "pointer",
            "target_type": serialize_type_spec(type_spec.target_type),
        }

    if isinstance(type_spec, SetType):
        return {
            "kind": "set",
            "name": type_spec.name,
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

    if kind == "pointer":
        return PointerType(
            deserialize_type_spec(data["target_type"]),
        )

    if kind == "set":
        return SetType(
            name=str(data.get("name", "")),
            element_type=deserialize_type_spec(data["element_type"]),
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

    if isinstance(value, SetValue):
        return {
            "kind": "set",
            "type": serialize_type_spec(value.type_spec),
            "elements": [
                serialize_value(element)
                for element in value.elements.values()
            ],
        }

    if isinstance(value, PointerValue):
        raise PseudoRuntimeError(
            "POINTER values cannot be persisted in RANDOM files"
        )

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

    if kind == "set":
        type_spec = deserialize_type_spec(data["type"])

        if not isinstance(type_spec, SetType):
            raise PseudoRuntimeError("Serialized SET type is invalid")

        elements = data["elements"]

        if not isinstance(elements, list):
            raise PseudoRuntimeError("Serialized SET elements are invalid")

        return make_set_value(
            type_spec,
            [
                deserialize_value(element)
                for element in elements
            ],
        )

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


__all__ = [
    "RANDOM_FILE_FORMAT",
    "deserialize_random_file",
    "deserialize_type_spec",
    "deserialize_value",
    "serialize_random_file",
    "serialize_type_spec",
    "serialize_value",
]
