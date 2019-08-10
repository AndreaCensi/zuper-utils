from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

from nose.tools import raises

from zuper_ipce.conv_object_from_ipce import object_from_ipce
from zuper_typing.annotations_tricks import make_Tuple
from zuper_typing.my_dict import make_set
from zuper_typing.my_intersection import Intersection
from zuper_typing_tests.test_utils import known_failure
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


# noinspection PyUnresolvedReferences


def test_union_1():
    @dataclass
    class MyClass:
        f: Union[int, str]

    e = MyClass(1)
    assert_object_roundtrip(e, {})  # raise here
    e = MyClass('a')  # pragma: no cover
    assert_object_roundtrip(e, {})  # pragma: no cover


def test_union_2():
    T = Union[int, str]
    assert_type_roundtrip(T, {})


def test_union_2b():
    T = Union[Tuple[str], int]
    assert_type_roundtrip(T, {})


def test_union_2c():
    T = Tuple[int, ...]
    assert_type_roundtrip(T, {})


def test_tuple_empty():
    T = make_Tuple()
    assert_type_roundtrip(T, {})


def test_union_3():
    @dataclass
    class A:
        a: int

    @dataclass
    class B:
        b: int

    @dataclass
    class C:
        c: Union[A, B]

    ec1 = C(A(1))
    ec2 = C(B(1))

    assert_type_roundtrip(C, {})
    assert_object_roundtrip(ec1, {})
    assert_object_roundtrip(ec2, {})


def test_intersection1():
    @dataclass
    class A1:
        a: int

    @dataclass
    class B1:
        b: str

    AB = Intersection[A1, B1]
    assert_type_roundtrip(AB, {}, expect_type_equal=False)


def test_intersection2():
    @dataclass
    class A:
        a: int

    @dataclass
    class B:
        b: str

    AB = Intersection[A, B]

    e = AB(a=1, b='2')
    assert_object_roundtrip(e, {})  # raise here


@raises(TypeError)
def test_none1():
    @dataclass
    class A:
        b: int

    object_from_ipce(None, {}, {}, expect_type=A)


def test_tuple_wiht_optional_inside():
    T = Tuple[int, Optional[int], str]
    assert_type_roundtrip(T, {})


def test_dict_with_optional():
    T = Dict[str, Optional[int]]
    assert_type_roundtrip(T, {})


def test_list_with_optional():
    T = List[Optional[int]]
    assert_type_roundtrip(T, {})


def test_set_with_optional():
    # even though it does not make sense ...
    T = make_set(Optional[int])
    assert_type_roundtrip(T, {})

@known_failure
def test_set_with_optional2():
    # even though it does not make sense ...
    T = Set[Optional[int]]
    assert_type_roundtrip(T, {})


def test_dict_with_optional_key():
    T = Dict[Optional[int], int]
    assert_type_roundtrip(T, {})


