import pytest

from src.psei.errors import ParseError, PseudoRuntimeError
from src.psei.runner import run_source
from src.psei.runtime import Runtime


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_byval_parameter_does_not_modify_caller():
    source = """
PROCEDURE AddOne(X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER
A ← 5

CALL AddOne(A)
OUTPUT A
"""

    assert run_capture(source) == ["5"]


def test_byref_parameter_modifies_caller():
    source = """
PROCEDURE AddOne(BYREF X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER
A ← 5

CALL AddOne(A)
OUTPUT A
"""

    assert run_capture(source) == ["6"]


def test_byref_mode_persists_across_parameters():
    source = """
PROCEDURE Swap(BYREF X : INTEGER, Y : INTEGER)
   DECLARE Temp : INTEGER

   Temp ← X
   X ← Y
   Y ← Temp
ENDPROCEDURE

DECLARE A : INTEGER
DECLARE B : INTEGER

A ← 1
B ← 2

CALL Swap(A, B)
OUTPUT A, ",", B
"""

    assert run_capture(source) == ["2,1"]


def test_explicit_byval_after_byref_resets_parameter_mode():
    source = """
PROCEDURE Test(BYREF X : INTEGER, BYVAL Y : INTEGER)
   X ← 10
   Y ← 20
ENDPROCEDURE

DECLARE A : INTEGER
DECLARE B : INTEGER

A ← 1
B ← 2

CALL Test(A, B)
OUTPUT A, ",", B
"""

    assert run_capture(source) == ["10,2"]


def test_function_can_be_called_inside_expression():
    source = """
FUNCTION Double(X : INTEGER) RETURNS INTEGER
   RETURN X * 2
ENDFUNCTION

OUTPUT Double(5) + 1
"""

    assert run_capture(source) == ["11"]


def test_forward_function_call_is_supported():
    source = """
OUTPUT Add(2, 3)

FUNCTION Add(A : INTEGER, B : INTEGER) RETURNS INTEGER
   RETURN A + B
ENDFUNCTION
"""

    assert run_capture(source) == ["5"]


def test_byref_requires_lvalue():
    source = """
PROCEDURE P(BYREF X : INTEGER)
   X ← 1
ENDPROCEDURE

CALL P(1 + 2)
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_byref_rejects_wrong_type():
    source = """
PROCEDURE P(BYREF X : INTEGER)
   X ← 1
ENDPROCEDURE

DECLARE R : REAL
R ← 1.5

CALL P(R)
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_function_parameters_cannot_be_byref():
    source = """
FUNCTION Bad(BYREF X : INTEGER) RETURNS INTEGER
   RETURN X
ENDFUNCTION
"""

    with pytest.raises(ParseError):
        run_source(source)


def test_return_outside_function_is_error():
    source = """
RETURN 1
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_return_inside_procedure_is_error():
    source = """
PROCEDURE Bad()
   RETURN 1
ENDPROCEDURE

CALL Bad()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_function_missing_return_is_error():
    source = """
FUNCTION Bad() RETURNS INTEGER
   OUTPUT "no return"
ENDFUNCTION

OUTPUT Bad()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)
