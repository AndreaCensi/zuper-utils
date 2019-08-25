from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, TypeVar, Union

from zuper_typing.my_intersection import Intersection
from zuper_typing.subcheck import can_be_used_as2
from zuper_typing.type_algebra import type_inf, type_sup
from zuper_typing.uninhabited import is_Uninhabited, make_Uninhabited


def test_algebra_sup_1():
    X = TypeVar("X")
    Y = TypeVar("Y")
    U = make_Uninhabited()
    cases = [
        (bool, object, object),
        (bool, int, int),
        (bool, U, bool),
        (int, str, Union[int, str]),
        (int, type(None), Optional[int]),
        (List[bool], List[int], List[int]),
        (Set[bool], Set[int], Set[int]),
        (Dict[bool, str], Dict[int, str], Dict[int, str]),
        (Dict[str, bool], Dict[str, int], Dict[str, int]),
        (Tuple[bool, ...], Tuple[int, ...], Tuple[int, ...]),
        (Tuple[bool, str], Tuple[int, str], Tuple[int, str]),
        (X, Y, Union[X, Y]),
    ]
    for A, B, expect in cases:
        yield check_sup, A, B, expect
        yield check_sup, B, A, expect


def test_algebra_inf_1():
    X = TypeVar("X")
    Y = TypeVar("Y")
    U = make_Uninhabited()
    cases = [
        (bool, object, bool),
        (bool, int, bool),
        (int, str, U),
        (U, str, U),
        (int, type(None), U),
        (List[bool], List[int], List[bool]),
        (List[bool], int, U),
        (List[bool], Set[int], U),
        (Set[bool], Set[int], Set[bool]),
        (Set[bool], int, U),
        (Set[bool], List[int], U),
        (Dict[bool, str], Dict[int, str], Dict[bool, str]),
        (Dict[str, bool], Dict[str, int], Dict[str, bool]),
        (Tuple[bool, ...], Tuple[int, ...], Tuple[bool, ...]),
        (Tuple[bool, str], Tuple[int, str], Tuple[bool, str]),
        (X, Y, Intersection[X, Y]),
    ]
    for A, B, expect in cases:
        yield check_inf, A, B, expect
        yield check_inf, B, A, expect


def check_sup(A, B, expect):
    r = can_be_used_as2(A, expect)
    assert r, r
    r = can_be_used_as2(B, expect)
    assert r, r

    res = type_sup(A, B)
    if res != expect:
        raise ValueError(res, expect)


def check_inf(A, B, expect):
    r = can_be_used_as2(expect, A)
    assert r, (expect, A, r)
    r = can_be_used_as2(expect, B)
    assert r, (expect, B, r)

    res = type_inf(A, B)

    if res != expect:
        raise ValueError(res, expect)


def test_optional1():
    r = can_be_used_as2(type(None), Optional[int])
    assert r, r


def test_algebra_dc1():
    @dataclass
    class A1:
        a: bool

    @dataclass
    class A2:
        a: int

    assert can_be_used_as2(A1, A2)

    ti = type_inf(A1, A2)
    ts = type_sup(A1, A2)

    eq1 = equivalent(ti, A1)
    assert eq1, eq1
    eq2 = equivalent(ts, A2)
    assert eq2, eq2


def test_algebra_dc2():
    @dataclass
    class A1:
        a: bool

    @dataclass
    class A2:
        a: str

    @dataclass
    class A3:
        a: Union[str, bool]

    ti = type_inf(A1, A2)
    ts = type_sup(A1, A2)

    assert is_Uninhabited(ti), ti

    assert equivalent(ts, A3)


def equivalent(x, y):
    r1 = can_be_used_as2(x, y)
    if not r1:
        return r1
    r2 = can_be_used_as2(x, y, r1.M)
    return r2
