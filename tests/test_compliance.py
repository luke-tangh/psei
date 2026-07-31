import json

import pytest

from psei.cli import main
from psei.compliance import (
    CAMBRIDGE_2027,
    ComplianceDiagnostic,
    check_file,
    check_source,
)


def diagnostic_codes(report):
    return [item.code for item in report.diagnostics]


def test_cambridge_2027_compliant_source():
    report = check_source(
        """
DECLARE Count : INTEGER
Count ← 1
IF Count = 1 THEN
   OUTPUT LENGTH("A")
ELSE
   OUTPUT "No"
ENDIF
""".lstrip()
    )

    assert report.profile == CAMBRIDGE_2027
    assert report.compliant
    assert not report.has_errors
    assert report.diagnostics == ()


def test_keyword_case_and_indentation_are_reported():
    report = check_source(
        """
declare Count : INTEGER
if Count = 1 then
  output length("A")
endif
""".lstrip()
    )

    assert not report.compliant
    assert not report.has_errors
    assert diagnostic_codes(report).count("C2027-K001") == 6
    assert diagnostic_codes(report).count("C2027-I002") == 1

    indentation = next(
        item for item in report.diagnostics if item.code == "C2027-I002"
    )
    assert indentation.line == 3
    assert "expected 3" in indentation.message


def test_tabs_are_reported_even_when_their_width_matches():
    report = check_source(
        "IF TRUE THEN\n"
        "\tOUTPUT \"yes\"\n"
        "ENDIF\n"
    )

    assert "C2027-I001" in diagnostic_codes(report)
    assert "C2027-I002" not in diagnostic_codes(report)


def test_strings_and_comments_do_not_trigger_keyword_case_warnings():
    report = check_source(
        'OUTPUT "if then output" // repeat until\n'
    )

    assert report.compliant


def test_inconsistent_identifier_spelling_is_reported_once_per_variant():
    report = check_source(
        """
DECLARE CountDown : INTEGER
Countdown ← 1
OUTPUT Countdown
""".lstrip()
    )

    inconsistent = [
        item
        for item in report.diagnostics
        if item.code == "C2027-ID001"
    ]

    assert len(inconsistent) == 1
    assert inconsistent[0].line == 2
    assert "'CountDown'" in inconsistent[0].message


def test_non_ascii_identifier_is_a_compliance_error():
    report = check_source(
        "DECLARE Café : INTEGER\n"
    )

    assert report.has_errors
    assert "C2027-ID002" in diagnostic_codes(report)


def test_ascii_assignment_is_a_compliance_error():
    report = check_source(
        "DECLARE X : INTEGER\n"
        "X <- 1\n"
    )

    assert report.has_errors
    assert "C2027-A001" in diagnostic_codes(report)


def test_psei_set_operation_is_reported_as_extension():
    report = check_source(
        """
TYPE TIntSet = SET OF INTEGER
DECLARE Values : TIntSet
OUTPUT CARDINALITY(Values)
""".lstrip()
    )

    extension = next(
        item for item in report.diagnostics if item.code == "C2027-X001"
    )

    assert not report.has_errors
    assert extension.line == 3
    assert "psei extension" in extension.message


def test_user_defined_callable_with_extension_name_is_not_reported():
    report = check_source(
        """
FUNCTION CARDINALITY(Value : INTEGER) RETURNS INTEGER
   RETURN Value
ENDFUNCTION
OUTPUT CARDINALITY(1)
""".lstrip()
    )

    assert "C2027-X001" not in diagnostic_codes(report)


def test_guide_bare_call_is_checked_using_formal_call_grammar():
    report = check_source(
        """
PROCEDURE Beep()
   OUTPUT "beep"
ENDPROCEDURE
DECLARE Move : CHAR
Move ← 'X'
CASE OF Move
   OTHERWISE : CALL Beep
ENDCASE
""".lstrip()
    )

    assert diagnostic_codes(report) == ["C2027-C001"]
    assert not report.has_errors
    assert "section 8.1" in report.diagnostics[0].message


def test_case_clause_statements_use_an_additional_indent_level():
    report = check_source(
        """
DECLARE N : INTEGER
CASE OF N
   1 :
      OUTPUT "one"
      OUTPUT "first"
   OTHERWISE :
      OUTPUT "other"
ENDCASE
""".lstrip()
    )

    assert report.compliant


def test_exam_line_numbers_are_auto_detected_and_removed_for_parsing():
    report = check_source(
        "10 DECLARE X : INTEGER\n"
        "20 X ← 1\n"
        "30 OUTPUT X\n"
    )

    assert report.compliant
    assert report.line_numbers_detected
    assert report.normalized_source.startswith("   DECLARE")


def test_numbered_source_may_omit_indentation():
    report = check_source(
        "1 IF TRUE THEN\n"
        "2 OUTPUT \"yes\"\n"
        "3 ENDIF\n",
        line_numbers="present",
    )

    assert report.compliant
    assert report.line_numbers_detected


def test_non_increasing_exam_line_numbers_are_reported():
    report = check_source(
        "2 DECLARE X : INTEGER\n"
        "1 OUTPUT X\n",
        line_numbers="present",
    )

    assert "C2027-N001" in diagnostic_codes(report)


def test_line_number_processing_can_be_disabled():
    report = check_source(
        "1 DECLARE X : INTEGER\n",
        line_numbers="absent",
    )

    assert not report.line_numbers_detected
    assert report.has_errors
    assert "C2027-P001" in diagnostic_codes(report)


def test_parse_error_is_returned_as_diagnostic():
    report = check_source(
        "IF TRUE\n"
        "   OUTPUT \"missing THEN\"\n"
        "ENDIF\n"
    )

    assert report.has_errors
    assert "C2027-P001" in diagnostic_codes(report)


def test_unknown_profile_and_line_number_mode_are_rejected():
    with pytest.raises(ValueError, match="Unsupported compliance profile"):
        check_source("OUTPUT 1", profile="unknown")

    with pytest.raises(ValueError, match="Unsupported line-number mode"):
        check_source("OUTPUT 1", line_numbers="sometimes")


def test_check_file_and_diagnostic_format(tmp_path):
    program = tmp_path / "program.pseudo"
    program.write_text("output 1\n", encoding="utf-8")

    report = check_file(program)
    diagnostic = report.diagnostics[0]

    assert isinstance(diagnostic, ComplianceDiagnostic)
    assert diagnostic.format(program).startswith(
        f"{program}:1:1: warning C2027-K001:"
    )


def test_cli_check_reports_success(tmp_path, capsys):
    program = tmp_path / "valid.pseudo"
    program.write_text("OUTPUT 1\n", encoding="utf-8")

    result = main(["check", str(program)])

    assert result is None
    assert "compliant with profile cambridge-2027" in capsys.readouterr().out


def test_cli_check_reports_diagnostics_and_exits_one(tmp_path, capsys):
    program = tmp_path / "invalid.pseudo"
    program.write_text("output 1\n", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main(["check", str(program)])

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert f"{program}:1:1: warning C2027-K001:" in output


def test_cli_check_json_output(tmp_path, capsys):
    program = tmp_path / "invalid.pseudo"
    program.write_text("X <- 1\n", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main(
            [
                "check",
                str(program),
                "--format",
                "json",
            ]
        )

    assert error.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["file"] == str(program)
    assert payload["profile"] == CAMBRIDGE_2027
    assert payload["compliant"] is False
    assert payload["diagnostics"][0]["code"] == "C2027-A001"
