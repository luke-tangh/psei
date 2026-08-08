from __future__ import annotations

import math
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
    coerce_value,
    make_set_value,
    norm_identifier,
    runtime_type_name,
    type_to_str,
)
from .values import ArrayValue, PointerValue


RANDOM_FILE_FORMAT = "psei-random-v1"


def _required(data: dict[str, Any], key: str, description: str) -> Any:
    if key not in data:
        raise PseudoRuntimeError(f"{description} is missing {key!r}")

    return data[key]


def _string(value: Any, description: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise PseudoRuntimeError(f"{description} is invalid")

    return value


def _integer(value: Any, description: str) -> int:
    if type(value) is not int:
        raise PseudoRuntimeError(f"{description} is invalid")

    return value


def _list(value: Any, description: str) -> list[Any]:
    if not isinstance(value, list):
        raise PseudoRuntimeError(f"{description} must be an array")

    return value


def _object(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PseudoRuntimeError(f"{description} must be an object")

    return value


def serialize_random_file(records: dict[int, Any]) -> dict[str, Any]:
    serialized_records = {}
    validated_records = []

    for address, value in records.items():
        if type(address) is not int:
            raise PseudoRuntimeError("Random file address must be an INTEGER")

        if address < 0:
            raise PseudoRuntimeError("Random file address cannot be negative")

        validated_records.append((address, value))

    for address, value in sorted(validated_records):
        serialized_records[str(address)] = serialize_value(value)

    return {
        "format": RANDOM_FILE_FORMAT,
        "records": serialized_records,
    }


def deserialize_random_file(data: Any) -> dict[int, Any]:
    if not isinstance(data, dict) or data.get("format") != RANDOM_FILE_FORMAT:
        raise PseudoRuntimeError("Random file is not a valid psei random file")

    records_data = data.get("records")

    if not isinstance(records_data, dict):
        raise PseudoRuntimeError("Random file records must be an object")

    records: dict[int, Any] = {}

    for address_text, value_data in records_data.items():
        if type(address_text) is not str or not address_text:
            raise PseudoRuntimeError(
                "Random file address must be a non-negative integer"
            )

        if address_text.startswith("-") and address_text[1:].isdigit():
            raise PseudoRuntimeError("Random file address cannot be negative")

        if any(character not in "0123456789" for character in address_text):
            raise PseudoRuntimeError(
                "Random file address must be a non-negative integer"
            )

        address = int(address_text)

        if address_text != str(address):
            raise PseudoRuntimeError(
                "Random file address must use its canonical decimal integer"
            )

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
        name = _string(
            _required(data, "name", "Serialized basic type"),
            "Serialized basic type name",
        ).upper()

        if name not in BASIC_TYPES:
            raise PseudoRuntimeError(f"Unknown serialized basic type {name!r}")

        return name

    if kind == "array":
        bounds_data = _list(
            _required(data, "bounds", "Serialized array type"),
            "Serialized array bounds",
        )

        if not bounds_data:
            raise PseudoRuntimeError("Serialized array must have a bound")

        bounds = []

        for item in bounds_data:
            if not isinstance(item, list) or len(item) != 2:
                raise PseudoRuntimeError("Serialized array bound is invalid")

            lower = _integer(item[0], "Serialized array lower bound")
            upper = _integer(item[1], "Serialized array upper bound")

            if lower > upper:
                raise PseudoRuntimeError(
                    "Serialized array lower bound exceeds upper bound"
                )

            bounds.append((lower, upper))

        return ArrayType(
            tuple(bounds),
            deserialize_type_spec(
                _required(
                    data,
                    "element_type",
                    "Serialized array type",
                )
            ),
        )

    if kind == "pointer":
        return PointerType(
            deserialize_type_spec(
                _required(data, "target_type", "Serialized pointer type")
            ),
        )

    if kind == "set":
        name_data = data.get("name", "")
        name = _string(
            name_data,
            "Serialized SET type name",
            allow_empty=True,
        )
        return SetType(
            name=name,
            element_type=deserialize_type_spec(
                _required(data, "element_type", "Serialized SET type")
            ),
        )

    if kind == "enum":
        name = _string(
            _required(data, "name", "Serialized enum type"),
            "Serialized enum type name",
        )
        values_data = _list(
            _required(data, "values", "Serialized enum type"),
            "Serialized enum values",
        )
        values = tuple(
            _string(value, "Serialized enum value")
            for value in values_data
        )

        if not values:
            raise PseudoRuntimeError("Serialized enum has no values")

        normalized_values = [norm_identifier(value) for value in values]

        if len(set(normalized_values)) != len(normalized_values):
            raise PseudoRuntimeError("Serialized enum values must be unique")

        return EnumType(
            name=name,
            values=values,
            value_to_index={
                norm_identifier(value): index
                for index, value in enumerate(values)
            },
        )

    if kind == "record":
        name = _string(
            _required(data, "name", "Serialized record type"),
            "Serialized record type name",
        )
        fields_data = _list(
            _required(data, "fields", "Serialized record type"),
            "Serialized record fields",
        )
        field_specs: dict[str, RecordFieldSpec] = {}

        for field_data in fields_data:
            field = _object(field_data, "Serialized record field")
            field_name = _string(
                _required(field, "name", "Serialized record field"),
                "Serialized record field name",
            )
            key = norm_identifier(field_name)

            if key in field_specs:
                raise PseudoRuntimeError(
                    "Serialized record field names must be unique"
                )

            field_specs[key] = RecordFieldSpec(
                original_name=field_name,
                type_spec=deserialize_type_spec(
                    _required(field, "type", "Serialized record field")
                ),
            )

        return RecordType(
            name=name,
            fields=field_specs,
            completed=True,
        )

    if kind == "class":
        return ClassType(
            name=_string(
                _required(data, "name", "Serialized class type"),
                "Serialized class type name",
            ),
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
        if not math.isfinite(value):
            raise PseudoRuntimeError(
                "Non-finite REAL values cannot be persisted in RANDOM files"
            )

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
        value = _required(data, "value", "Serialized BOOLEAN value")

        if type(value) is not bool:
            raise PseudoRuntimeError("Serialized BOOLEAN value is invalid")

        return value

    if kind == "integer":
        value = _required(data, "value", "Serialized INTEGER value")

        if type(value) is not int:
            raise PseudoRuntimeError("Serialized INTEGER value is invalid")

        return value

    if kind == "real":
        value = _required(data, "value", "Serialized REAL value")

        if type(value) is not int and type(value) is not float:
            raise PseudoRuntimeError("Serialized REAL value is invalid")

        try:
            real_value = float(value)
        except OverflowError as error:
            raise PseudoRuntimeError(
                "Serialized REAL value must be finite"
            ) from error

        if not math.isfinite(real_value):
            raise PseudoRuntimeError("Serialized REAL value must be finite")

        return real_value

    if kind == "char":
        value = _string(
            _required(data, "value", "Serialized CHAR value"),
            "Serialized CHAR value",
        )

        if len(value) != 1:
            raise PseudoRuntimeError(
                "Serialized CHAR value must contain exactly one character"
            )

        return Char(value)

    if kind == "string":
        value = _required(data, "value", "Serialized STRING value")

        if type(value) is not str:
            raise PseudoRuntimeError("Serialized STRING value is invalid")

        return value

    if kind == "date":
        return make_date(
            _integer(
                _required(data, "day", "Serialized DATE value"),
                "Serialized DATE day",
            ),
            _integer(
                _required(data, "month", "Serialized DATE value"),
                "Serialized DATE month",
            ),
            _integer(
                _required(data, "year", "Serialized DATE value"),
                "Serialized DATE year",
            ),
        )

    if kind == "enum":
        type_spec = deserialize_type_spec(
            _required(data, "type", "Serialized enum value")
        )

        if not isinstance(type_spec, EnumType):
            raise PseudoRuntimeError("Serialized enum type is invalid")

        name = _string(
            _required(data, "name", "Serialized enum value"),
            "Serialized enum value name",
        )
        return EnumValue(type_spec, name, type_spec.ordinal_of(name))

    if kind == "set":
        type_spec = deserialize_type_spec(
            _required(data, "type", "Serialized SET value")
        )

        if not isinstance(type_spec, SetType):
            raise PseudoRuntimeError("Serialized SET type is invalid")

        elements = _list(
            _required(data, "elements", "Serialized SET value"),
            "Serialized SET elements",
        )

        return make_set_value(
            type_spec,
            [
                deserialize_value(element)
                for element in elements
            ],
        )

    if kind == "record":
        type_spec = deserialize_type_spec(
            _required(data, "type", "Serialized record value")
        )

        if not isinstance(type_spec, RecordType):
            raise PseudoRuntimeError("Serialized record type is invalid")

        fields_data = _object(
            _required(data, "fields", "Serialized record value"),
            "Serialized record fields",
        )
        fields = {}

        for field_name_data, field_value in fields_data.items():
            field_name = _string(
                field_name_data,
                "Serialized record field name",
            )
            key = norm_identifier(field_name)

            if key in fields:
                raise PseudoRuntimeError(
                    "Serialized record field names must be unique"
                )

            if key not in type_spec.fields:
                raise PseudoRuntimeError(
                    f"Serialized record has unknown field {field_name!r}"
                )

            fields[key] = coerce_value(
                deserialize_value(field_value),
                type_spec.fields[key].type_spec,
            )

        missing_fields = set(type_spec.fields) - set(fields)

        if missing_fields:
            missing = type_spec.fields[min(missing_fields)].original_name
            raise PseudoRuntimeError(
                f"Serialized record is missing field {missing!r}"
            )

        return RecordValue(type_spec, fields)

    if kind == "array":
        type_spec = deserialize_type_spec(
            _required(data, "type", "Serialized array value")
        )

        if not isinstance(type_spec, ArrayType):
            raise PseudoRuntimeError("Serialized array type is invalid")

        data_items = _list(
            _required(data, "data", "Serialized array value"),
            "Serialized array data",
        )
        values: dict[tuple[int, ...], Any] = {}

        for item_data in data_items:
            item = _object(item_data, "Serialized array element")
            indices_data = _list(
                _required(item, "indices", "Serialized array element"),
                "Serialized array indices",
            )

            if len(indices_data) != len(type_spec.bounds):
                raise PseudoRuntimeError(
                    "Serialized array element has the wrong number of indices"
                )

            indices = tuple(
                _integer(index, "Serialized array index")
                for index in indices_data
            )

            for index, (lower, upper) in zip(indices, type_spec.bounds):
                if index < lower or index > upper:
                    raise PseudoRuntimeError(
                        f"Serialized array index {index} is out of bounds"
                    )

            if indices in values:
                raise PseudoRuntimeError(
                    f"Serialized array index {indices!r} is duplicated"
                )

            values[indices] = coerce_value(
                deserialize_value(
                    _required(item, "value", "Serialized array element")
                ),
                type_spec.element_type,
            )

        expected_elements = math.prod(
            upper - lower + 1
            for lower, upper in type_spec.bounds
        )

        if len(values) != expected_elements:
            raise PseudoRuntimeError(
                "Serialized array does not contain every declared element"
            )

        return ArrayValue(type_spec, values)

    if kind == "null_object":
        type_spec = deserialize_type_spec(
            _required(data, "type", "Serialized NULL object value")
        )

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
