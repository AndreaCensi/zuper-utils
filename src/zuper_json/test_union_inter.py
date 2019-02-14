from dataclasses import dataclass
from typing import *
# noinspection PyUnresolvedReferences
from typing import ForwardRef

from zuper_json.my_intersection import Intersection
from .test_utils import assert_object_roundtrip, with_private_register, assert_type_roundtrip


@with_private_register
def test_union_1():
    @dataclass
    class MyClass:
        f: Union[int, str]

    e = MyClass(1)
    assert_object_roundtrip(e, {})  # raise here
    e = MyClass('a')  # pragma: no cover
    assert_object_roundtrip(e, {})  # pragma: no cover


@with_private_register
def test_union_2():
    T = Union[int, str]
    assert_type_roundtrip(T, {})


#
#
# @with_private_register
# def test_intersection1():
#     @dataclass
#     class MyClass:
#         f: Union[int, str]
#
#     e = MyClass(1)
#     assert_object_roundtrip(e, {}) # raise here
#     e = MyClass('a') # pragma: no cover
#     assert_object_roundtrip(e, {}) # pragma: no cover


@with_private_register
def test_intersection1():
    @dataclass
    class A():
        a: int

    @dataclass
    class B():
        b: str

    AB = Intersection[A, B]
    assert_type_roundtrip(AB, {}, expect_type_equal=False)


@with_private_register
def test_intersection2():
    @dataclass
    class A():
        a: int

    @dataclass
    class B():
        b: str

    AB = Intersection[A, B]

    e = AB(a=1, b='2')
    assert_object_roundtrip(e, {})  # raise here
