import pytest

from interpreter.errors import PseudoRuntimeError
from interpreter.runner import run_source
from interpreter.runtime import Runtime


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_class_property_initializer_and_methods():
    source = """
CLASS Player
   PRIVATE Attempts : INTEGER

   Attempts ← 3

   PUBLIC PROCEDURE SetAttempts(Number : INTEGER)
      Attempts ← Number
   ENDPROCEDURE

   PUBLIC FUNCTION GetAttempts() RETURNS INTEGER
      RETURN Attempts
   ENDFUNCTION
ENDCLASS

DECLARE P : Player

P ← NEW Player()

OUTPUT P.GetAttempts()
P.SetAttempts(7)
OUTPUT P.GetAttempts()
"""

    assert run_capture(source) == ["3", "7"]


def test_constructor_inheritance_and_super_new():
    source = """
CLASS Pet
   PRIVATE Name : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING)
      Name ← GivenName
   ENDPROCEDURE

   PUBLIC FUNCTION GetName() RETURNS STRING
      RETURN Name
   ENDFUNCTION
ENDCLASS

CLASS Cat INHERITS Pet
   PRIVATE Breed : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING, GivenBreed : STRING)
      SUPER.NEW(GivenName)
      Breed ← GivenBreed
   ENDPROCEDURE

   PUBLIC FUNCTION GetBreed() RETURNS STRING
      RETURN Breed
   ENDFUNCTION
ENDCLASS

MyCat ← NEW Cat("Kitty", "Shorthaired")

OUTPUT MyCat.GetName()
OUTPUT MyCat.GetBreed()
"""

    assert run_capture(source) == ["Kitty", "Shorthaired"]


def test_object_property_can_be_passed_byref():
    source = """
CLASS Box
   PUBLIC Value : INTEGER

   PUBLIC PROCEDURE NEW(Start : INTEGER)
      Value ← Start
   ENDPROCEDURE
ENDCLASS

PROCEDURE AddOne(BYREF X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE B : Box

B ← NEW Box(10)

CALL AddOne(B.Value)

OUTPUT B.Value
"""

    assert run_capture(source) == ["11"]


def test_method_can_return_object_property_in_expression():
    source = """
CLASS Counter
   PRIVATE Value : INTEGER

   PUBLIC PROCEDURE NEW(Start : INTEGER)
      Value ← Start
   ENDPROCEDURE

   PUBLIC FUNCTION GetValue() RETURNS INTEGER
      RETURN Value
   ENDFUNCTION
ENDCLASS

C ← NEW Counter(10)

OUTPUT C.GetValue() + 5
"""

    assert run_capture(source) == ["15"]


def test_unknown_class_in_new_is_error():
    source = """
X ← NEW Missing()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_super_without_parent_is_error():
    source = """
CLASS A
   PUBLIC PROCEDURE NEW()
      SUPER.NEW()
   ENDPROCEDURE
ENDCLASS

X ← NEW A()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_procedure_method_cannot_be_used_as_function():
    source = """
CLASS A
   PUBLIC PROCEDURE P()
      OUTPUT "called"
   ENDPROCEDURE
ENDCLASS

X ← NEW A()
OUTPUT X.P()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)
