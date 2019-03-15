from dataclasses import dataclass
from typing import *

from nose.tools import raises

from zuper_json.ipce import ipce_to_object
from zuper_json.my_intersection import Intersection
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
    class A:
        a: int

    @dataclass
    class B:
        b: str

    AB = Intersection[A, B]
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

    ob = ipce_to_object(None, {}, {}, expect_type=A)
    assert ob is not None
