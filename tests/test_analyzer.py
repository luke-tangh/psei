import json
from pathlib import Path

import pytest

from psei import analyze_file, analyze_source
from psei.analyzer import SEMANTIC_CODES
from psei.cli import main


PASSING_EXAMPLES = sorted(
    (Path(__file__).resolve().parents[1] / "examples" / "passing").glob(
        "*.pseudo"
    )
)


def codes(report):
    return [diagnostic.code for diagnostic in report.diagnostics]


@pytest.mark.parametrize(
    "path",
    PASSING_EXAMPLES,
    ids=lambda path: path.stem,
)
def test_passing_examples_are_semantically_valid(path):
    report = analyze_source(path.read_text(encoding="utf-8"))

    assert report.valid, [item.format(path) for item in report.diagnostics]


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        ("OUTPUT Missing\n", "SEM001"),
        (
            "DECLARE Value : INTEGER\nDECLARE value : REAL\n",
            "SEM002",
        ),
        (
            'DECLARE Value : INTEGER\nValue ← "wrong"\n',
            "SEM004",
        ),
        ("IF 1 THEN\n   OUTPUT 1\nENDIF\n", "SEM005"),
        ("CALL Missing()\n", "SEM006"),
        ("OUTPUT LENGTH()\n", "SEM007"),
        (
            "FUNCTION Identity(Value : INTEGER) RETURNS INTEGER\n"
            "   RETURN Value\n"
            "ENDFUNCTION\n"
            'OUTPUT Identity("wrong")\n',
            "SEM008",
        ),
        (
            "PROCEDURE Increment(BYREF Value : INTEGER)\n"
            "   Value ← Value + 1\n"
            "ENDPROCEDURE\n"
            "CALL Increment(1)\n",
            "SEM009",
        ),
        (
            "DECLARE Value : INTEGER\nOUTPUT Value[1]\n",
            "SEM010",
        ),
        (
            "FUNCTION MissingReturn() RETURNS INTEGER\n"
            "   OUTPUT 1\n"
            "ENDFUNCTION\n",
            "SEM011",
        ),
        ("RETURN 1\n", "SEM012"),
        (
            "FUNCTION WrongReturn() RETURNS INTEGER\n"
            '   RETURN "wrong"\n'
            "ENDFUNCTION\n",
            "SEM013",
        ),
        ("DECLARE Value : MissingType\n", "SEM015"),
    ],
)
def test_core_semantic_errors_have_stable_codes(source, expected_code):
    report = analyze_source(source)

    assert expected_code in codes(report)
    assert not report.valid


def test_recommendation_mode_reports_uninitialised_reads():
    source = "DECLARE Value : INTEGER\nOUTPUT Value\n"

    normal = analyze_source(source)
    recommendations = analyze_source(source, recommendations=True)

    assert normal.valid
    assert normal.diagnostics == ()
    assert codes(recommendations) == ["SEM003"]
    assert recommendations.valid
    assert recommendations.has_warnings


def test_strict_mode_rejects_inferred_variables_but_normal_mode_accepts_them():
    source = "Value ← 1\nOUTPUT Value\n"

    assert analyze_source(source).valid
    assert codes(analyze_source(source, strict=True)) == ["SEM001", "SEM001"]


def test_forward_calls_and_complete_function_paths_are_valid():
    source = """
OUTPUT Maximum(10, 20)

FUNCTION Maximum(A : INTEGER, B : INTEGER) RETURNS INTEGER
   IF A > B THEN
      RETURN A
   ELSE
      RETURN B
   ENDIF
ENDFUNCTION
"""

    assert analyze_source(source).valid


def test_unreachable_statement_is_a_warning():
    report = analyze_source(
        "FUNCTION Stop() RETURNS INTEGER\n"
        "   RETURN 1\n"
        "   OUTPUT 2\n"
        "ENDFUNCTION\n"
    )

    assert report.valid
    assert codes(report) == ["SEM014"]
    assert report.diagnostics[0].severity == "warning"


def test_diagnostic_uses_expression_source_location_and_serialises():
    report = analyze_source("OUTPUT 1 + Missing\n")

    diagnostic = report.diagnostics[0]
    assert (diagnostic.line, diagnostic.col) == (1, 12)
    assert diagnostic.format("sample.pseudo").startswith(
        "sample.pseudo:1:12: error SEM001:"
    )
    assert report.to_dict()["diagnostics"] == [diagnostic.to_dict()]


def test_named_pointer_record_array_set_and_byref_lvalues_are_valid():
    source = """
TYPE Student
   DECLARE Score : INTEGER
ENDTYPE
TYPE TIntPointer = ^INTEGER
TYPE TIntSet = SET OF INTEGER

PROCEDURE Increment(BYREF Value : INTEGER)
   Value ← Value + 1
ENDPROCEDURE

DECLARE Pupil : Student
DECLARE Values : ARRAY[1:2] OF INTEGER
DECLARE Pointer : TIntPointer
DECLARE Numbers : TIntSet

Pointer ← ^Pupil.Score
Pointer^ ← 1
Values[1] ← Pointer^
CALL Increment(Values[1])
CALL SETADD(Numbers, Values[1])
OUTPUT CONTAINS(Numbers, 2)
"""

    assert analyze_source(source).valid


def test_invalid_array_record_and_comparison_operations_are_reported():
    source = """
TYPE Student
   DECLARE Name : STRING
ENDTYPE
DECLARE Pupil : Student
DECLARE Grid : ARRAY[1:2,1:2] OF INTEGER
OUTPUT Pupil.Missing
OUTPUT Grid[1]
OUTPUT Grid["row", 1]
OUTPUT Pupil = Pupil
"""

    assert codes(analyze_source(source)) == [
        "SEM010",
        "SEM010",
        "SEM005",
        "SEM005",
    ]


def test_callable_kind_byref_type_and_method_rules_are_checked():
    source = """
CLASS Counter
   PRIVATE Value : INTEGER
   PRIVATE PROCEDURE Reset()
      Value ← 0
   ENDPROCEDURE
   PUBLIC FUNCTION Current() RETURNS INTEGER
      RETURN Value
   ENDFUNCTION
ENDCLASS

PROCEDURE SetValue(BYREF Value : INTEGER)
   Value ← 1
ENDPROCEDURE
FUNCTION GetValue() RETURNS INTEGER
   RETURN 1
ENDFUNCTION

DECLARE CounterValue : Counter
DECLARE Text : STRING
CounterValue ← NEW Counter()
OUTPUT CounterValue.Value
CounterValue.Reset()
OUTPUT CounterValue.Reset()
CounterValue.Current()
OUTPUT SetValue(Text)
CALL GetValue()
CALL SetValue(Text)
"""

    report = analyze_source(source)

    assert set(codes(report)) >= {"SEM006", "SEM009", "SEM010"}


def test_duplicate_type_members_enum_values_and_inheritance_cycles_are_safe():
    source = """
TYPE Choice = (First, First)
TYPE RecordType
   DECLARE Value : INTEGER
   DECLARE value : REAL
ENDTYPE
CLASS A INHERITS B
   PUBLIC Value : INTEGER
   PRIVATE value : INTEGER
ENDCLASS
CLASS B INHERITS A
ENDCLASS
"""

    report = analyze_source(source)

    assert "SEM002" in codes(report)
    assert "SEM015" in codes(report)


def test_invalid_recursive_record_set_and_constructor_types_are_reported():
    source = """
TYPE Recursive
   DECLARE Child : Recursive
ENDTYPE
TYPE InvalidSet = SET OF Recursive
CLASS Invalid
   PUBLIC FUNCTION NEW() RETURNS INTEGER
      RETURN 1
   ENDFUNCTION
ENDCLASS
"""

    report = analyze_source(source)

    assert codes(report).count("SEM015") == 2
    assert "SEM006" in codes(report)


def test_subclass_cannot_access_inherited_private_property():
    source = """
CLASS Parent
   PRIVATE Value : INTEGER
ENDCLASS
CLASS Child INHERITS Parent
   PUBLIC FUNCTION GetValue() RETURNS INTEGER
      RETURN Value
   ENDFUNCTION
ENDCLASS
"""

    report = analyze_source(source)

    assert codes(report) == ["SEM010"]


def test_builtin_and_operator_types_are_checked():
    source = """
OUTPUT INT(1)
OUTPUT INT(1.5)
OUTPUT INT("one")
OUTPUT TRUE + 1
OUTPUT "A" < 1
OUTPUT TRUE < FALSE
OUTPUT LCASE("A")
"""

    assert codes(analyze_source(source)) == [
        "SEM005",
        "SEM005",
        "SEM005",
        "SEM005",
        "SEM008",
    ]


def test_semantic_code_registry_is_complete_and_stable():
    assert tuple(SEMANTIC_CODES) == tuple(
        f"SEM{number:03d}" for number in range(1, 16)
    )


def test_analyze_file_and_cli_json_output(tmp_path, capsys):
    path = tmp_path / "invalid.pseudo"
    path.write_text("OUTPUT Missing\n", encoding="utf-8")

    assert codes(analyze_file(path)) == ["SEM001"]

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", str(path), "--format", "json"])

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert not payload["valid"]
    assert payload["diagnostics"][0]["code"] == "SEM001"


def test_analyze_cli_success_and_recommendation_exit_zero(
    tmp_path,
    capsys,
):
    path = tmp_path / "valid.pseudo"
    path.write_text("DECLARE Value : INTEGER\nOUTPUT Value\n", encoding="utf-8")

    main(["analyze", str(path)])
    assert capsys.readouterr().out.endswith("no semantic issues found\n")

    main(["analyze", str(path), "--recommendations"])
    output = capsys.readouterr().out
    assert "warning SEM003" in output
