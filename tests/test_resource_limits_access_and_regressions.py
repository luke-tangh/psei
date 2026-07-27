import pytest

from psei.errors import PseudoRuntimeError
from psei.runner import run_source
from psei.runtime import (
    EnumType,
    EnumValue,
    Runtime,
    coerce_value,
    norm_identifier,
)


def run_capture(source: str, *, runtime: Runtime | None = None):
    output = []

    if runtime is None:
        runtime = Runtime(output_writer=output.append)
    else:
        runtime.output_writer = output.append

    run_source(source, runtime)
    return output


def make_enum_type(name: str, values: tuple[str, ...]) -> EnumType:
    return EnumType(
        name=name,
        values=values,
        value_to_index={
            norm_identifier(value): index
            for index, value in enumerate(values)
        },
    )


def test_empty_infinite_while_loop_hits_step_limit():
    source = """
WHILE TRUE
ENDWHILE
"""

    runtime = Runtime(max_steps=5)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)


def test_empty_for_loop_hits_step_limit():
    source = """
FOR I ← 1 TO 100
NEXT I
"""

    runtime = Runtime(max_steps=10)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)


def test_array_allocation_limit_is_enforced():
    source = """
DECLARE Values : ARRAY[1:4] OF INTEGER
"""

    runtime = Runtime(max_array_elements=3)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)


def test_call_depth_limit_is_enforced():
    source = """
FUNCTION Recurse() RETURNS INTEGER
   RETURN Recurse()
ENDFUNCTION

OUTPUT Recurse()
"""

    runtime = Runtime(max_call_depth=5)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)


def test_output_limit_is_enforced():
    source = """
OUTPUT "123456"
"""

    runtime = Runtime(max_output_chars=5)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)


def test_ucase_lcase_unicode_chars_do_not_raise_value_error():
    source = """
OUTPUT UCASE('ß')
OUTPUT LCASE('İ')
OUTPUT UCASE('a')
OUTPUT LCASE('Z')
"""

    assert run_capture(source) == ["ß", "İ", "A", "z"]


def test_large_integer_division_does_not_use_float():
    value = 10**100 + 1

    assert run_capture(f"OUTPUT {value} DIV 3") == [str(value // 3)]


def test_method_function_cannot_be_used_as_standalone_statement_before_body_runs():
    source = """
CLASS A
   PUBLIC FUNCTION F() RETURNS INTEGER
      OUTPUT "side effect"
      RETURN 1
   ENDFUNCTION
ENDCLASS

X ← NEW A()
X.F()
"""

    output = []
    runtime = Runtime(output_writer=output.append)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)

    assert output == []


def test_private_property_access_is_enforced():
    source = """
CLASS A
   PRIVATE Value : INTEGER

   PUBLIC PROCEDURE NEW()
      Value ← 1
   ENDPROCEDURE
ENDCLASS

X ← NEW A()
OUTPUT X.Value
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_private_method_access_is_enforced_before_body_runs():
    source = """
CLASS A
   PRIVATE PROCEDURE Secret()
      OUTPUT "side effect"
   ENDPROCEDURE
ENDCLASS

X ← NEW A()
X.Secret()
"""

    output = []
    runtime = Runtime(output_writer=output.append)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)

    assert output == []


def test_private_property_is_accessible_through_own_public_method():
    source = """
CLASS A
   PRIVATE Value : INTEGER

   PUBLIC PROCEDURE NEW()
      Value ← 7
   ENDPROCEDURE

   PUBLIC FUNCTION GetValue() RETURNS INTEGER
      RETURN Value
   ENDFUNCTION
ENDCLASS

X ← NEW A()
OUTPUT X.GetValue()
"""

    assert run_capture(source) == ["7"]


def test_enum_coercion_revalidates_target_enum_values():
    source_type = make_enum_type("Season", ("Winter",))
    target_type = make_enum_type("Season", ("Spring", "Summer"))

    with pytest.raises(PseudoRuntimeError):
        coerce_value(
            EnumValue(source_type, "Winter", 0),
            target_type,
        )
