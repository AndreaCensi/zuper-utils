from typing import Any, Dict, List, Set, Tuple

from zuper_commons.text import pretty_dict
from zuper_typing.annotations_tricks import (
    is_VarTuple,
    is_VarTuple_canonical,
    make_VarTuple,
    get_VarTuple_arg,
    is_Any,
    is_FixedTuple,
)
from zuper_typing.my_dict import make_dict, make_list, make_set
from zuper_typing.recursive_tricks import canonical


def test_canonical():
    cases = [
        (dict, make_dict(Any, Any)),
        (Dict, make_dict(Any, Any)),
        (list, make_list(Any)),
        (List, make_list(Any)),
        (tuple, make_VarTuple(Any)),
        (Tuple, make_VarTuple(Any)),
        (set, make_set(Any)),
        (Set, make_set(Any)),
    ]

    for a, b in cases:
        yield check_canonical, a, b


def check_canonical(a, expected):
    obtained = canonical(a)
    if obtained != expected:
        msg = "Failure"
        raise Exception(
            pretty_dict(msg, dict(a=a, obtained=obtained, expected=expected))
        )


def test_canonical1():
    assert is_VarTuple(tuple)
    assert not is_FixedTuple(tuple)
    assert is_Any(get_VarTuple_arg(tuple))
    assert not is_VarTuple_canonical(tuple)
    r = canonical(tuple)
    assert r == Tuple[Any, ...], r
