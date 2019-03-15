from dataclasses import dataclass
from typing import Tuple, List

from zuper_json.test_utils import assert_object_roundtrip, assert_type_roundtrip

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
