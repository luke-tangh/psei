import json

import pytest

from psei.errors import PseudoRuntimeError
from psei.runner import run_file, run_source
from psei.runtime import Runtime


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_run_source_rejects_strict_mismatch_with_existing_runtime():
    runtime = Runtime(strict=False)

    with pytest.raises(ValueError):
        run_source("X ← 1", runtime, strict=True)


def test_procedure_method_used_as_function_does_not_execute_body():
    source = """
CLASS A
   PUBLIC PROCEDURE P()
      OUTPUT "side effect"
   ENDPROCEDURE
ENDCLASS

X ← NEW A()
OUTPUT X.P()
"""

    output = []
    runtime = Runtime(output_writer=output.append)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)

    assert output == []


def test_function_new_is_rejected_during_class_registration():
    source = """
CLASS A
   PUBLIC FUNCTION NEW() RETURNS INTEGER
      OUTPUT "bad"
      RETURN 1
   ENDFUNCTION
ENDCLASS

X ← NEW A()
"""

    output = []
    runtime = Runtime(output_writer=output.append)

    with pytest.raises(PseudoRuntimeError):
        run_source(source, runtime)

    assert output == []


def test_inheritance_cycle_is_runtime_error():
    source = """
CLASS A INHERITS B
ENDCLASS

CLASS B INHERITS A
ENDCLASS

X ← NEW A()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_declared_class_variable_starts_as_null_reference():
    source = """
CLASS Player
ENDCLASS

DECLARE P : Player
OUTPUT P
"""

    assert run_capture(source) == ["NULL"]


def test_method_call_on_null_class_reference_is_error():
    source = """
CLASS Player
   PRIVATE Attempts : INTEGER

   Attempts ← 3

   PUBLIC FUNCTION GetAttempts() RETURNS INTEGER
      RETURN Attempts
   ENDFUNCTION
ENDCLASS

DECLARE P : Player

OUTPUT P.GetAttempts()
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_new_after_class_declaration_runs_initializers():
    source = """
CLASS Player
   PRIVATE Attempts : INTEGER

   Attempts ← 3

   PUBLIC FUNCTION GetAttempts() RETURNS INTEGER
      RETURN Attempts
   ENDFUNCTION
ENDCLASS

DECLARE P : Player

P ← NEW Player()

OUTPUT P.GetAttempts()
"""

    assert run_capture(source) == ["3"]


def test_self_referential_class_property_is_null_reference_not_recursive_value():
    source = """
CLASS Node
   PUBLIC Child : Node
ENDCLASS

N ← NEW Node()

OUTPUT N.Child
"""

    assert run_capture(source) == ["NULL"]


def test_integer_boolean_equality_is_type_error_not_python_truthiness():
    source = """
OUTPUT 1 = TRUE
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_char_string_equality_is_type_error():
    source = """
OUTPUT 'A' = "A"
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_recursive_record_type_is_rejected():
    source = """
TYPE Node
   DECLARE Child : Node
ENDTYPE

DECLARE N : Node
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_run_file_random_files_use_json_not_pickle(tmp_path, capsys):
    source = """
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord
DECLARE Loaded : StudentRecord

Pupil.LastName ← "Ali"
Pupil.YearGroup ← 12

OPENFILE "Students.dat" FOR RANDOM
SEEK "Students.dat", 5
PUTRECORD "Students.dat", Pupil
CLOSEFILE "Students.dat"

OPENFILE "Students.dat" FOR RANDOM
SEEK "Students.dat", 5
GETRECORD "Students.dat", Loaded
CLOSEFILE "Students.dat"

OUTPUT Loaded.LastName, ":", Loaded.YearGroup
"""

    program_path = tmp_path / "program.pseudo"
    random_path = tmp_path / "Students.dat"

    program_path.write_text(source, encoding="utf-8")

    run_file(str(program_path))

    assert capsys.readouterr().out == "Ali:12\n"

    raw = random_path.read_bytes()

    assert raw.startswith(b"{")
    assert not raw.startswith(b"\x80")

    parsed = json.loads(raw.decode("utf-8"))

    assert parsed["format"] == "psei-random-v1"
