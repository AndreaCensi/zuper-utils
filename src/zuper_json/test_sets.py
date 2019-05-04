from dataclasses import dataclass
from typing import *

from zuper_json.annotations_tricks import is_Set
from zuper_json.my_dict import make_set
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

def test_not_implemented_set():
    @dataclass
    class MyClass:
        f: Set[int]

    e = MyClass({1, 2, 3})
    assert_object_roundtrip(e, {})  # pragma: no cover


def test_is_set01():
    assert not is_Set(set)


def test_is_set02():
    T = Set
    print(f'the set is {T}')
    assert is_Set(T)


def test_is_set03():
    assert is_Set(Set[int])


def test_rt():
    T = Set[int]
    assert_type_roundtrip(T, {}, expect_type_equal=False)

def test_rt_yes():
    T = make_set(int)
    assert_type_roundtrip(T, {}, expect_type_equal=True)

def test_rt2():
    T = make_set(int)
    assert_type_roundtrip(T, {})


def test_not_implemented_set_2():
    @dataclass
    class A:
        a: int

    @dataclass
    class MyClass:
        f: Set[A]

    e = MyClass({A(1), A(2)})
    assert_object_roundtrip(e, {})  # pragma: no cover
