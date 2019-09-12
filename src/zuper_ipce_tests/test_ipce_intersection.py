from dataclasses import dataclass

from zuper_ipce_tests.test_utils import assert_object_roundtrip, assert_type_roundtrip
from zuper_typing.my_intersection import Intersection, make_Intersection
from zuper_typing.type_algebra import type_inf


def test_ipce_intersection1():
    @dataclass
    class A:
        a: bool

    @dataclass
    class B:
        a: int

    I = make_Intersection((A, B))
    assert_type_roundtrip(I)


def test_intersection1():
    @dataclass
    class A1:
        a: int

    @dataclass
    class B1:
        b: str

    AB = Intersection[A1, B1]
    assert_type_roundtrip(AB, expect_type_equal=False)


def test_intersection2():
    @dataclass
    class A:
        a: int

    @dataclass
    class B:
        b: str

    # AB = Intersection[A, B]
    AB = type_inf(A, B)

    # print(AB.__annotations__)
    e = AB(a=1, b="2")
    assert_object_roundtrip(e)  # raise here
