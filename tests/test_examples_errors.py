import json
from pathlib import Path

import importlib
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ERROR_EXAMPLES_DIR = PROJECT_ROOT / "examples" / "errors"
MANIFEST_PATH = ERROR_EXAMPLES_DIR / "manifest.json"


def import_api():
    """
    Support both possible source package names:

    - interpreter
    - pseudo_interpreter
    """
    errors = []

    for package_name in ("interpreter", "pseudo_interpreter"):
        try:
            runner_module = importlib.import_module(f"{package_name}.runner")
            errors_module = importlib.import_module(f"{package_name}.errors")
            return runner_module.run_source, errors_module
        except ModuleNotFoundError as e:
            errors.append(f"{package_name}: {e}")

    raise ImportError(
        "Could not import interpreter API from interpreter.* "
        "or pseudo_interpreter.*. Tried:\n"
        + "\n".join(errors)
    )


run_source, errors_module = import_api()


ERROR_CLASSES = {
    "LexError": errors_module.LexError,
    "ParseError": errors_module.ParseError,
    "PseudoRuntimeError": errors_module.PseudoRuntimeError,
}


def load_error_examples():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    examples = []

    for item in manifest:
        program_path = ERROR_EXAMPLES_DIR / item["file"]
        error_name = item["error"]
        strict = item.get("strict", False)

        if error_name not in ERROR_CLASSES:
            raise ValueError(f"Unknown error type in manifest: {error_name}")

        examples.append(
            pytest.param(
                program_path,
                ERROR_CLASSES[error_name],
                strict,
                id=program_path.stem,
            )
        )

    return examples


@pytest.mark.parametrize(
    "program_path, expected_error, strict",
    load_error_examples(),
)
def test_error_example(program_path: Path, expected_error, strict: bool):
    source = program_path.read_text(encoding="utf-8")

    with pytest.raises(expected_error):
        run_source(source, strict=strict)
