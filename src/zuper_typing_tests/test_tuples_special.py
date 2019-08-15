from typing import Any, Tuple, TypeVar

from zuper_typing.annotations_tricks import (
    get_VarTuple_arg,
    is_Any,
    is_FixedTuple,
    is_Tuple,
    is_TupleLike,
    is_VarTuple,
    make_Tuple,
)

#
# T1 = Tuple
# T2 = Tuple[int]
# T3 = Tuple[Any, ...]
X = TypeVar("X")


# T4 = Tuple[X, ...]


def test_tuple_special_1():
    T1 = Tuple
    assert is_Tuple(T1), T1
    assert not is_FixedTuple(T1), T1
    assert is_VarTuple(T1), T1
    x = get_VarTuple_arg(T1)
    assert is_Any(x), x


def test_tuple_special_2():
    T1 = Tuple[Any, ...]
    assert is_Tuple(T1), T1
    assert not is_FixedTuple(T1), T1
    assert is_VarTuple(T1), T1
    x = get_VarTuple_arg(T1)
    assert is_Any(x), x


def test_tuple_special_3():
    T1 = Tuple[X, ...]
    assert is_Tuple(T1), T1
    assert not is_FixedTuple(T1), T1
    assert is_VarTuple(T1), T1
    x = get_VarTuple_arg(T1)
    assert x == X


def test_tuple_special_4():
    T1 = Tuple[int, str]
    assert is_Tuple(T1), T1
    assert is_FixedTuple(T1), T1
    assert not is_VarTuple(T1), T1


def test_tuple_special_5():
    T1 = make_Tuple()
    assert is_Tuple(T1), T1
    assert is_FixedTuple(T1), T1
    assert not is_VarTuple(T1), T1


def test_tuple_special_6():
    T = tuple
    assert not is_Tuple(T)
    assert is_TupleLike(T)
    assert is_VarTuple(T)
    X2 = get_VarTuple_arg(T)
    assert is_Any(X2)
