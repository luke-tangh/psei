import pytest

from psei.errors import PseudoRuntimeError
from psei.lexer import Lexer
from psei.runner import run_source
from psei.runtime import Runtime
from psei.tokens import T


def test_byval_byref_are_keywords():
    tokens = Lexer("BYVAL BYREF").scan_tokens()
    types = [token.type for token in tokens]

    assert types == [T.BYVAL, T.BYREF, T.EOF]


def test_backslashes_in_strings_are_literal_characters():
    output = []
    runtime = Runtime(output_writer=output.append)

    run_source(r'OUTPUT "data\file.txt", ":", "A\qB"', runtime)

    assert output == [r"data\file.txt:A\qB"]


def test_scope_stack_resolves_assignment_to_parent():
    runtime = Runtime(strict=True)

    runtime.env.define("Counter", T.INTEGER, 1)

    child = runtime.push_scope("procedure")

    try:
        runtime.env.assign("Counter", 2)
        runtime.env.define("LocalValue", T.INTEGER, 99)

        assert runtime.global_env.get("Counter") == 2
        assert runtime.env.get("Counter") == 2
        assert runtime.env.get("LocalValue") == 99

    finally:
        popped = runtime.pop_scope()

    assert popped is child

    with pytest.raises(PseudoRuntimeError):
        runtime.global_env.get("LocalValue")


def test_cannot_pop_global_scope():
    runtime = Runtime()

    with pytest.raises(PseudoRuntimeError):
        runtime.pop_scope()
