import pytest

from psei.errors import PseudoRuntimeError
from psei.runner import run_source
from psei.runtime import Runtime


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_enum_assignment_and_case():
    source = """
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE S : Season
S ← Autumn

CASE OF S
   Spring : OUTPUT "spring"
   Autumn : OUTPUT "autumn"
   OTHERWISE : OUTPUT "other"
ENDCASE

OUTPUT S
"""

    assert run_capture(source) == ["autumn", "Autumn"]


def test_enum_default_value_is_first_value():
    source = """
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE S : Season

OUTPUT S
"""

    assert run_capture(source) == ["Spring"]


def test_record_assignment_clones_value():
    source = """
TYPE StudentRecord
   DECLARE Name : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE A : StudentRecord
DECLARE B : StudentRecord

A.Name ← "Ali"
A.YearGroup ← 6

B ← A

A.YearGroup ← 7

OUTPUT B.Name, ":", B.YearGroup
OUTPUT A.Name, ":", A.YearGroup
"""

    assert run_capture(source) == ["Ali:6", "Ali:7"]


def test_record_array_and_field_update():
    source = """
TYPE StudentRecord
   DECLARE Name : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Form : ARRAY[1:2] OF StudentRecord
DECLARE I : INTEGER

Form[1].Name ← "Ali"
Form[1].YearGroup ← 10

Form[2].Name ← "Mei"
Form[2].YearGroup ← 11

FOR I ← 1 TO 2
   Form[I].YearGroup ← Form[I].YearGroup + 1
NEXT I

OUTPUT Form[1].Name, ":", Form[1].YearGroup
OUTPUT Form[2].Name, ":", Form[2].YearGroup
"""

    assert run_capture(source) == ["Ali:11", "Mei:12"]


def test_record_field_can_be_passed_byref():
    source = """
TYPE StudentRecord
   DECLARE YearGroup : INTEGER
ENDTYPE

PROCEDURE AddOne(BYREF X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE Pupil : StudentRecord

Pupil.YearGroup ← 6

CALL AddOne(Pupil.YearGroup)

OUTPUT Pupil.YearGroup
"""

    assert run_capture(source) == ["7"]


def test_unknown_user_type_is_error():
    source = """
DECLARE X : MissingType
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_assigning_wrong_enum_type_is_error():
    source = """
TYPE Season = (Spring, Summer, Autumn, Winter)
TYPE Colour = (Red, Green, Blue)

DECLARE S : Season

S ← Red
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_unknown_record_field_is_error():
    source = """
TYPE StudentRecord
   DECLARE Name : STRING
ENDTYPE

DECLARE Pupil : StudentRecord

Pupil.YearGroup ← 6
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)
