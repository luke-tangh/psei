import pytest

from src.psei.errors import PseudoRuntimeError
from src.psei.lexer import Lexer
from src.psei.runtime import Runtime
from src.psei.tokens import T


def test_byval_byref_are_keywords():
    tokens = Lexer("BYVAL BYREF").scan_tokens()
    types = [token.type for token in tokens]

    assert types == [T.BYVAL, T.BYREF, T.EOF]


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
