import math

import pytest

from psei.ast_nodes import ArrayType, PointerType
from psei.errors import PseudoRuntimeError
from psei.runtime.files import ensure_random_file_value_supported
from psei.runtime.oop import ClassType, NullObjectValue, ObjectValue
from psei.runtime.serialization import (
    RANDOM_FILE_FORMAT,
    deserialize_random_file,
    deserialize_type_spec,
    deserialize_value,
    serialize_random_file,
    serialize_type_spec,
    serialize_value,
)
from psei.runtime.types import (
    EnumType,
    EnumValue,
    RecordFieldSpec,
    RecordType,
    RecordValue,
    SetType,
    make_set_value,
)
from psei.runtime.values import ArrayValue, PointerValue
from psei.tokens import T
from psei.values import Char, make_date


def enum_type() -> EnumType:
    return EnumType(
        name="Season",
        values=("Spring", "Summer"),
        value_to_index={"spring": 0, "summer": 1},
    )


def record_type() -> RecordType:
    return RecordType(
        name="Student",
        fields={
            "name": RecordFieldSpec("Name", T.STRING),
            "scores": RecordFieldSpec(
                "Scores",
                ArrayType(((1, 2),), T.INTEGER),
            ),
        },
        completed=True,
    )


@pytest.mark.parametrize(
    "value",
    [
        True,
        42,
        3.5,
        Char("X"),
        "hello",
        make_date(8, 8, 2026),
    ],
)
def test_scalar_values_round_trip(value):
    assert deserialize_value(serialize_value(value)) == value


@pytest.mark.parametrize(
    "type_spec",
    [
        T.INTEGER,
        ArrayType(((1, 2), (-1, 1)), T.REAL),
        PointerType(T.CHAR),
        SetType("LetterSet", T.CHAR),
        enum_type(),
        record_type(),
        ClassType("Pet", completed=True),
    ],
)
def test_type_specs_round_trip(type_spec):
    encoded = serialize_type_spec(type_spec)

    assert serialize_type_spec(deserialize_type_spec(encoded)) == encoded


def test_composite_values_round_trip_canonically():
    scores_type = ArrayType(((1, 2),), T.INTEGER)
    scores = ArrayValue(scores_type, {(1,): 91, (2,): 87})
    student = RecordValue(record_type(), {"name": "Ali", "scores": scores})
    season = enum_type()
    values = [
        EnumValue(season, "Summer", 1),
        make_set_value(SetType("LetterSet", T.CHAR), [Char("A"), Char("E")]),
        scores,
        student,
        NullObjectValue(ClassType("Pet", completed=True)),
    ]

    for value in values:
        encoded = serialize_value(value)

        assert serialize_value(deserialize_value(encoded)) == encoded


def test_random_file_round_trip_uses_numeric_address_order():
    encoded = serialize_random_file({10: "ten", 2: "two", 0: "zero"})

    assert encoded["format"] == RANDOM_FILE_FORMAT
    assert list(encoded["records"]) == ["0", "2", "10"]
    assert deserialize_random_file(encoded) == {0: "zero", 2: "two", 10: "ten"}


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_non_finite_real_values_cannot_be_persisted(value):
    with pytest.raises(PseudoRuntimeError, match="Non-finite REAL"):
        serialize_value(value)


@pytest.mark.parametrize("address", [-1, True, 1.5, "1"])
def test_random_file_serialization_rejects_invalid_addresses(address):
    with pytest.raises(PseudoRuntimeError, match="address"):
        serialize_random_file({address: 1})


@pytest.mark.parametrize(
    "data, message",
    [
        (None, "not a valid psei random file"),
        ({"format": "future", "records": {}}, "not a valid psei random file"),
        ({"format": RANDOM_FILE_FORMAT}, "records must be an object"),
        (
            {"format": RANDOM_FILE_FORMAT, "records": []},
            "records must be an object",
        ),
        (
            {"format": RANDOM_FILE_FORMAT, "records": {"bad": {}}},
            "address must be a non-negative integer",
        ),
        (
            {"format": RANDOM_FILE_FORMAT, "records": {"01": {}}},
            "canonical decimal integer",
        ),
        (
            {"format": RANDOM_FILE_FORMAT, "records": {"-1": {}}},
            "address cannot be negative",
        ),
        (
            {"format": RANDOM_FILE_FORMAT, "records": {1: {}}},
            "address must be a non-negative integer",
        ),
    ],
)
def test_malformed_random_files_raise_runtime_errors(data, message):
    with pytest.raises(PseudoRuntimeError, match=message):
        deserialize_random_file(data)


@pytest.mark.parametrize(
    "data",
    [
        None,
        {},
        {"kind": "basic"},
        {"kind": "basic", "name": 1},
        {"kind": "basic", "name": "MISSING"},
        {
            "kind": "array",
            "bounds": "bad",
            "element_type": {"kind": "basic", "name": "INTEGER"},
        },
        {
            "kind": "array",
            "bounds": [],
            "element_type": {"kind": "basic", "name": "INTEGER"},
        },
        {
            "kind": "array",
            "bounds": [[1]],
            "element_type": {"kind": "basic", "name": "INTEGER"},
        },
        {
            "kind": "array",
            "bounds": [[True, 2]],
            "element_type": {"kind": "basic", "name": "INTEGER"},
        },
        {
            "kind": "array",
            "bounds": [[2, 1]],
            "element_type": {"kind": "basic", "name": "INTEGER"},
        },
        {"kind": "pointer"},
        {
            "kind": "set",
            "name": 1,
            "element_type": {"kind": "basic", "name": "CHAR"},
        },
        {"kind": "enum", "name": "Empty", "values": []},
        {"kind": "enum", "name": "Bad", "values": ["A", "a"]},
        {"kind": "record", "name": "Bad", "fields": "bad"},
        {"kind": "record", "name": "Bad", "fields": [1]},
        {"kind": "record", "name": "Bad", "fields": [{"name": "X"}]},
        {
            "kind": "record",
            "name": "Bad",
            "fields": [
                {
                    "name": "X",
                    "type": {"kind": "basic", "name": "INTEGER"},
                },
                {
                    "name": "x",
                    "type": {"kind": "basic", "name": "INTEGER"},
                },
            ],
        },
        {"kind": "class", "name": ""},
        {"kind": "future"},
    ],
)
def test_malformed_type_specs_raise_runtime_errors(data):
    with pytest.raises(PseudoRuntimeError):
        deserialize_type_spec(data)


@pytest.mark.parametrize(
    "data",
    [
        None,
        {},
        {"kind": "boolean"},
        {"kind": "boolean", "value": 1},
        {"kind": "integer", "value": True},
        {"kind": "real", "value": "1.0"},
        {"kind": "real", "value": math.inf},
        {"kind": "real", "value": 10**1000},
        {"kind": "char", "value": "XX"},
        {"kind": "string", "value": Char("X")},
        {"kind": "date", "day": 31, "month": 2, "year": 2026},
        {
            "kind": "enum",
            "type": {"kind": "basic", "name": "INTEGER"},
            "name": "A",
        },
        {
            "kind": "set",
            "type": {"kind": "basic", "name": "INTEGER"},
            "elements": [],
        },
        {
            "kind": "record",
            "type": {"kind": "basic", "name": "INTEGER"},
            "fields": {},
        },
        {
            "kind": "array",
            "type": {"kind": "basic", "name": "INTEGER"},
            "data": [],
        },
        {"kind": "null_object", "type": {"kind": "basic", "name": "INTEGER"}},
        {"kind": "future"},
    ],
)
def test_malformed_values_raise_runtime_errors(data):
    with pytest.raises(PseudoRuntimeError):
        deserialize_value(data)


def test_record_deserialization_validates_fields_and_values():
    encoded = serialize_value(
        RecordValue(
            record_type(),
            {
                "name": "Ali",
                "scores": ArrayValue(
                    ArrayType(((1, 2),), T.INTEGER),
                    {(1,): 1, (2,): 2},
                ),
            },
        )
    )

    missing = {**encoded, "fields": {"Name": {"kind": "string", "value": "Ali"}}}
    extra = {
        **encoded,
        "fields": {
            **encoded["fields"],
            "Other": {"kind": "integer", "value": 1},
        },
    }
    wrong_type = {
        **encoded,
        "fields": {
            **encoded["fields"],
            "Name": {"kind": "integer", "value": 1},
        },
    }
    duplicate = {
        **encoded,
        "fields": {
            **encoded["fields"],
            "name": {"kind": "string", "value": "Other"},
        },
    }

    for data in (missing, extra, wrong_type, duplicate):
        with pytest.raises(PseudoRuntimeError):
            deserialize_value(data)


def test_array_deserialization_validates_shape_bounds_completeness_and_values():
    array_type = ArrayType(((1, 2),), T.INTEGER)
    encoded = serialize_value(ArrayValue(array_type, {(1,): 10, (2,): 20}))
    bad_data_sets = [
        "bad",
        [{"indices": [1, 2], "value": {"kind": "integer", "value": 10}}],
        [{"indices": [0], "value": {"kind": "integer", "value": 10}}],
        [
            {"indices": [1], "value": {"kind": "integer", "value": 10}},
            {"indices": [1], "value": {"kind": "integer", "value": 20}},
        ],
        [{"indices": [1], "value": {"kind": "integer", "value": 10}}],
        [
            {"indices": [1], "value": {"kind": "integer", "value": 10}},
            {"indices": [2], "value": {"kind": "string", "value": "bad"}},
        ],
    ]

    for data in bad_data_sets:
        with pytest.raises(PseudoRuntimeError):
            deserialize_value({**encoded, "data": data})


def test_random_files_reject_objects_and_pointers_at_any_nesting_level():
    pet_type = ClassType("Pet", completed=True)
    unsupported = [
        ObjectValue(pet_type, {}),
        NullObjectValue(pet_type),
        PointerValue(PointerType(T.INTEGER)),
        ArrayValue(
            ArrayType(((1, 1),), pet_type),
            {(1,): NullObjectValue(pet_type)},
        ),
    ]

    for value in unsupported:
        with pytest.raises(PseudoRuntimeError):
            ensure_random_file_value_supported(value)


@pytest.mark.parametrize(
    "value",
    [
        PointerValue(PointerType(T.INTEGER)),
        ObjectValue(ClassType("Pet", completed=True), {}),
    ],
)
def test_value_serializer_rejects_live_references(value):
    with pytest.raises(PseudoRuntimeError):
        serialize_value(value)


def test_type_serializer_rejects_unknown_types():
    with pytest.raises(PseudoRuntimeError):
        serialize_type_spec(object())


def test_value_serializer_rejects_unknown_values():
    with pytest.raises(PseudoRuntimeError):
        serialize_value(object())
