from dataclasses import dataclass
from typing import *
from typing import NewType

from .test_utils import relies_on_missing_features, assert_type_roundtrip, assert_object_roundtrip, known_failure

symbols = {}


@relies_on_missing_features
def test_type1():
    T = Type
    assert_type_roundtrip(T, symbols)


def test_type2():
    T = type
    assert_type_roundtrip(T, symbols)


@relies_on_missing_features
def test_newtype():
    T = NewType('T', str)
    assert_type_roundtrip(T, symbols)


def test_dict1():
    c = {}
    assert_object_roundtrip(c, symbols)


def test_any():
    T = Any
    assert_type_roundtrip(T, symbols)


@known_failure
def test_any2():
    @dataclass
    class C:
        a: Any

    c = C(a={})
    assert_object_roundtrip(c, symbols)


def test_any3():
    @dataclass
    class C:
        a: Any

    c = C(a=1)
    assert_object_roundtrip(c, symbols)


def test_any4():
    assert_object_roundtrip(Any, symbols)
