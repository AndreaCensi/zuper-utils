from dataclasses import dataclass
from typing import *

from nose.tools import raises

from zuper_typing.annotations_tricks import make_Union
from zuper_ipce_tests.test_not_implemented import test_default_arguments
from zuper_ipce.ipce import ipce_to_object
from zuper_typing.my_intersection import Intersection
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

    ipce_to_object(None, {}, {}, expect_type=A)


def test_making_union():
    make_Union(int)
    make_Union(int, float)
    make_Union(int, float, bool)
    make_Union(int, float, bool, str)
    make_Union(int, float, bool, str, bytes)
    make_Union(int, float, bool, str, bytes, int)


if __name__ == '__main__':
    test_default_arguments()