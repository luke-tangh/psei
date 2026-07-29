import pytest

from psei.errors import PseudoRuntimeError
from psei.runner import run_source
from psei.runtime import Runtime


def run_capture(source: str):
    output = []
    runtime = Runtime(output_writer=output.append)
    run_source(source, runtime)
    return output


def test_set_algebra_and_deterministic_output():
    source = """
TYPE TIntSet = SET OF INTEGER

DEFINE Left (1, 2, 3) : TIntSet
DEFINE Right (3, 4) : TIntSet

DECLARE Result : TIntSet

Result ← UNION(Left, Right)
OUTPUT Result

Result ← INTERSECTION(Left, Right)
OUTPUT Result

Result ← DIFFERENCE(Left, Right)
OUTPUT Result

Result ← SYMMETRICDIFFERENCE(Left, Right)
OUTPUT Result
"""

    assert run_capture(source) == [
        "{1, 2, 3, 4}",
        "{3}",
        "{1, 2}",
        "{1, 2, 4}",
    ]


def test_set_queries():
    source = """
TYPE TIntSet = SET OF INTEGER

DEFINE Small (1, 2) : TIntSet
DEFINE Same (1, 2) : TIntSet
DEFINE Large (1, 2, 3) : TIntSet
DEFINE Other (8, 9) : TIntSet
DEFINE Empty () : TIntSet

OUTPUT CONTAINS(Large, 3)
OUTPUT CONTAINS(Large, 4)
OUTPUT CARDINALITY(Large)
OUTPUT ISEMPTY(Empty)
OUTPUT ISSUBSET(Small, Large)
OUTPUT ISSUBSET(Small, Same)
OUTPUT ISPROPERSUBSET(Small, Large)
OUTPUT ISPROPERSUBSET(Small, Same)
OUTPUT ISSUPERSET(Large, Small)
OUTPUT ISPROPERSUPERSET(Large, Small)
OUTPUT ISDISJOINT(Small, Other)
"""

    assert run_capture(source) == [
        "TRUE",
        "FALSE",
        "3",
        "TRUE",
        "TRUE",
        "TRUE",
        "TRUE",
        "FALSE",
        "TRUE",
        "TRUE",
        "TRUE",
    ]


def test_set_mutation_procedures_and_copy_semantics():
    source = """
TYPE TIntSet = SET OF INTEGER

DEFINE Original (1, 2, 3) : TIntSet
DECLARE Working : TIntSet

Working ← Original
CALL SETADD(Working, 4)
CALL SETADD(Working, 4)
CALL SETREMOVE(Working, 2)
CALL SETDISCARD(Working, 99)

OUTPUT Working
OUTPUT Original

CALL SETCLEAR(Working)
OUTPUT Working
"""

    assert run_capture(source) == [
        "{1, 3, 4}",
        "{1, 2, 3}",
        "{}",
    ]


def test_set_operations_support_enumerated_elements():
    source = """
TYPE Season = (Spring, Summer, Autumn, Winter)
TYPE SeasonSet = SET OF Season

DEFINE Warm (Summer, Autumn) : SeasonSet
DEFINE Transitional (Spring, Autumn) : SeasonSet

OUTPUT INTERSECTION(Warm, Transitional)
OUTPUT CONTAINS(Warm, Summer)
"""

    assert run_capture(source) == ["{Autumn}", "TRUE"]


def test_set_algebra_requires_matching_set_types():
    source = """
TYPE TIntSet = SET OF INTEGER
TYPE TCharSet = SET OF CHAR

DEFINE Numbers (1, 2) : TIntSet
DEFINE Letters ('A', 'B') : TCharSet

OUTPUT UNION(Numbers, Letters)
"""

    with pytest.raises(PseudoRuntimeError, match="same type"):
        run_source(source)


def test_set_element_must_match_the_declared_type():
    source = """
TYPE TIntSet = SET OF INTEGER
DEFINE Numbers (1, 2) : TIntSet

OUTPUT CONTAINS(Numbers, "1")
"""

    with pytest.raises(PseudoRuntimeError, match="Expected INTEGER"):
        run_source(source)


def test_setremove_requires_an_existing_element():
    source = """
TYPE TIntSet = SET OF INTEGER
DECLARE Numbers : TIntSet

CALL SETREMOVE(Numbers, 1)
"""

    with pytest.raises(PseudoRuntimeError, match="not present"):
        run_source(source)


def test_define_set_cannot_be_mutated():
    source = """
TYPE TIntSet = SET OF INTEGER
DEFINE Numbers (1, 2) : TIntSet

CALL SETADD(Numbers, 3)
"""

    with pytest.raises(PseudoRuntimeError, match="constant"):
        run_source(source)
