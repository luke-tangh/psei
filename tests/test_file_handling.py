import json

import pytest

from psei.errors import PseudoRuntimeError
from psei.runner import run_source
from psei.runtime import LocalFileSystem, Runtime
from psei.tokens import T


def run_capture(source: str, *, strict: bool = False):
    output = []
    runtime = Runtime(strict=strict, output_writer=output.append)
    run_source(source, runtime, strict=strict)
    return output


def test_text_file_write_read_and_eof():
    source = """
DECLARE LineOfText : STRING

OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "one"
WRITEFILE "A.txt", "two"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ

WHILE NOT EOF("A.txt")
   READFILE "A.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "A.txt"
"""

    assert run_capture(source) == ["one", "two"]


def test_text_file_append():
    source = """
DECLARE LineOfText : STRING

OPENFILE "Log.txt" FOR WRITE
WRITEFILE "Log.txt", "A"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR APPEND
WRITEFILE "Log.txt", "B"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR READ

WHILE NOT EOF("Log.txt")
   READFILE "Log.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "Log.txt"
"""

    assert run_capture(source) == ["A", "B"]


def test_random_file_record_put_and_get():
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

Pupil.LastName ← "Changed"
Pupil.YearGroup ← 99

SEEK "Students.dat", 5
GETRECORD "Students.dat", Loaded
CLOSEFILE "Students.dat"

OUTPUT Loaded.LastName, ":", Loaded.YearGroup
OUTPUT Pupil.LastName, ":", Pupil.YearGroup
"""

    assert run_capture(source) == ["Ali:12", "Changed:99"]


def test_text_file_cannot_be_reopened_as_random_file():
    source = """
OPENFILE "Mixed.dat" FOR WRITE
WRITEFILE "Mixed.dat", "text"
CLOSEFILE "Mixed.dat"

OPENFILE "Mixed.dat" FOR RANDOM
"""

    with pytest.raises(PseudoRuntimeError, match="not a valid psei random file"):
        run_source(source)


def test_random_file_cannot_be_reopened_as_text_file():
    source = """
OPENFILE "Mixed.dat" FOR RANDOM
SEEK "Mixed.dat", 0
PUTRECORD "Mixed.dat", 42
CLOSEFILE "Mixed.dat"

OPENFILE "Mixed.dat" FOR READ
"""

    with pytest.raises(PseudoRuntimeError, match="cannot be opened for READ"):
        run_source(source)


def test_local_write_mode_truncates_file_when_opened(tmp_path):
    path = tmp_path / "Existing.txt"
    path.write_text("old data\n", encoding="utf-8")
    file_system = LocalFileSystem(tmp_path)

    file_system.open_file("Existing.txt", T.WRITE)

    assert path.read_text(encoding="utf-8") == ""

    file_system.close_file("Existing.txt")


def test_local_random_file_cannot_be_opened_as_text(tmp_path):
    file_system = LocalFileSystem(tmp_path)
    runtime = Runtime(file_system=file_system)

    run_source(
        """
OPENFILE "Data.dat" FOR RANDOM
SEEK "Data.dat", 0
PUTRECORD "Data.dat", 42
CLOSEFILE "Data.dat"
""",
        runtime,
    )

    with pytest.raises(PseudoRuntimeError, match="cannot be opened for READ"):
        run_source('OPENFILE "Data.dat" FOR READ', runtime)


@pytest.mark.parametrize(
    "data",
    [
        {"format": "psei-random-v1", "records": {"invalid": {}}},
        {
            "format": "psei-random-v1",
            "records": {"0": {"kind": "integer"}},
        },
        {
            "format": "psei-random-v1",
            "records": {
                "0": {
                    "kind": "array",
                    "type": {
                        "kind": "array",
                        "bounds": [[1, 2]],
                        "element_type": {
                            "kind": "basic",
                            "name": "INTEGER",
                        },
                    },
                    "data": [],
                },
            },
        },
    ],
)
def test_local_random_file_rejects_malformed_persisted_data(tmp_path, data):
    path = tmp_path / "Broken.dat"
    path.write_text(json.dumps(data), encoding="utf-8")
    file_system = LocalFileSystem(tmp_path)

    with pytest.raises(PseudoRuntimeError):
        file_system.open_file("Broken.dat", T.RANDOM)

    assert file_system.open_files == {}


def test_readfile_target_must_be_string():
    source = """
DECLARE N : INTEGER

OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "text"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ
READFILE "A.txt", N
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_eof_requires_open_read_file():
    source = """
OUTPUT EOF("Missing.txt")
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_writefile_requires_write_or_append_mode():
    source = """
OPENFILE "A.txt" FOR WRITE
WRITEFILE "A.txt", "text"
CLOSEFILE "A.txt"

OPENFILE "A.txt" FOR READ
WRITEFILE "A.txt", "bad"
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)


def test_random_get_missing_record_is_error():
    source = """
DECLARE X : INTEGER

OPENFILE "Data.dat" FOR RANDOM
SEEK "Data.dat", 10
GETRECORD "Data.dat", X
"""

    with pytest.raises(PseudoRuntimeError):
        run_source(source)
