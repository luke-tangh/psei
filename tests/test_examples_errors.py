import json
from pathlib import Path

import pytest
import psei.runner as runner
import psei.errors as errors


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ERROR_EXAMPLES_DIR = PROJECT_ROOT / "examples" / "errors"
MANIFEST_PATH = ERROR_EXAMPLES_DIR / "manifest.json"


run_source, errors_module = runner.run_source, errors


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
