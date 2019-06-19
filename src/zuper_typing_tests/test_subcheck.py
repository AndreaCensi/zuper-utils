from dataclasses import dataclass
from typing import *

from zuper_typing.annotations_tricks import is_Tuple
from zuper_typing.subcheck import can_be_used_as2


def test_corner_cases10():
    assert can_be_used_as2(str, str, {})
    assert not can_be_used_as2(str, int, {})


def test_corner_cases11():
    assert can_be_used_as2(Dict, Dict, {})
    assert can_be_used_as2(Dict[str, str], Dict[str, str], {})
    assert can_be_used_as2(Dict[str, str], Dict[str, Any], {})


def test_corner_cases12():
    assert not can_be_used_as2(Dict[str, str], str, {})


def test_corner_cases13():
    assert not can_be_used_as2(str, Dict[str, str], {})


def test_corner_cases14():
    assert not can_be_used_as2(Union[int, str], str, {})


def test_corner_cases15():
    assert can_be_used_as2(str, Union[int, str], {})


def test_corner_cases16():
    assert can_be_used_as2(Union[int], Union[int, str], {})


def test_corner_cases17():
    assert not can_be_used_as2(Union[int, str], Union[str], {})


def test_corner_cases18():
    @dataclass
    class A:
        a: int

    @dataclass
    class B(A):
        pass

    @dataclass
    class C:
        a: int

    assert can_be_used_as2(B, A, {})
    assert can_be_used_as2(C, A, {})


def test_corner_cases18b():
    @dataclass
    class A:
        a: int

    @dataclass
    class C:
        a: str

    assert not can_be_used_as2(A, C, {})


def test_corner_cases18c():
    @dataclass
    class A:
        a: int

    @dataclass
    class C:
        pass

    assert not can_be_used_as2(C, A, {})
    assert can_be_used_as2(A, C, {})


def test_corner_cases19():
    assert not can_be_used_as2(str, int, {})


def test_corner_cases06():
    assert can_be_used_as2(int, Optional[int], {}).result


def test_corner_cases20():
    assert is_Tuple(Tuple[int, int])
    res = can_be_used_as2(Tuple[int, int], Tuple[int, Any], {})
    assert res, res


def test_corner_cases21():
    assert not can_be_used_as2(Tuple[int, int], int, {})


def test_corner_cases22():
    assert not can_be_used_as2(Any, int, {})


def test_corner_cases23():
    @dataclass
    class A:
        a: int

    @dataclass
    class B(A):
        pass

    @dataclass
    class C(A):
        pass

    res = can_be_used_as2(Union[B, C], A, {})
    assert res, res


def test_corner_cases24():
    assert not can_be_used_as2(Tuple[int, int], Tuple[int, str], {})


def test_corner_cases25():
    D1 = Dict[str, Any]
    D2 = Dict[str, int]
    res = can_be_used_as2(D2, D1, {})
    assert res, res

def test_corner_cases26():
    D1 = Dict[str, Any]
    D2 = Dict[str, int]
    res = can_be_used_as2(D1, D2, {})
    assert not res, res
