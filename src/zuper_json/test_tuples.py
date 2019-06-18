from dataclasses import dataclass
from typing import Tuple, List

from zuper_json.annotations_tricks import make_Tuple
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

symbols = {}


def test_tuples1():
    @dataclass
    class M:
        a: Tuple[int, str]

    a = M((1, '32'))

    assert_object_roundtrip(a, {})
    assert_type_roundtrip(M, {})


def test_tuples3():
    T = Tuple[str, int]
    assert_type_roundtrip(T, symbols)

def test_tuples2():
    T = Tuple[str, ...]
    assert_type_roundtrip(T, symbols)



def test_list1():
    T = List[str]
    assert_type_roundtrip(T, symbols)


def test_list2():
    @dataclass
    class M:
        a: List[str]

    a = M(['a', 'b'])
    assert_object_roundtrip(a, symbols)


def test_making():
    make_Tuple(int)
    make_Tuple(int, float)
    make_Tuple(int, float, bool)
    make_Tuple(int, float, bool, str)
    make_Tuple(int, float, bool, str, bytes)
    make_Tuple(int, float, bool, str, bytes, int)


# 
# def test_tuples1():
#
#     @dataclass
#     class M:
#         a: Tuple[int, str]
#
#     a = M((1,'32'))
#
#     assert_object_roundtrip(a, {})
#     assert_type_roundtrip(M, {})
