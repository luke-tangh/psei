from pathlib import Path

import importlib
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PASSING_EXAMPLES_DIR = PROJECT_ROOT / "examples" / "passing"


def import_run_source():
    """
    Support both possible source package names:

    - interpreter
    - pseudo_interpreter
    """
    errors = []

    for package_name in ("interpreter", "pseudo_interpreter"):
        try:
            module = importlib.import_module(f"{package_name}.runner")
            return module.run_source
        except ModuleNotFoundError as e:
            errors.append(f"{package_name}: {e}")

    raise ImportError(
        "Could not import run_source from interpreter.runner "
        "or pseudo_interpreter.runner. Tried:\n"
        + "\n".join(errors)
    )


run_source = import_run_source()


def normalise_output(text: str) -> str:
    """
    Normalise line endings and ignore only final newlines.

    Do not use .strip(), because that would remove meaningful spaces
    produced by OUTPUT.
    """
    return text.replace("\r\n", "\n").rstrip("\n")


def find_passing_examples():
    return sorted(PASSING_EXAMPLES_DIR.glob("*.pseudo"))


@pytest.mark.parametrize(
    "program_path",
    find_passing_examples(),
    ids=lambda path: path.stem,
)
def test_passing_example(program_path: Path, capsys):
    expected_path = program_path.with_suffix(".out")

    assert expected_path.exists(), (
        f"Missing expected output file for {program_path.name}: "
        f"{expected_path.name}"
    )

    source = program_path.read_text(encoding="utf-8")
    expected = expected_path.read_text(encoding="utf-8")

    run_source(source)

    actual = capsys.readouterr().out

    assert normalise_output(actual) == normalise_output(expected)
