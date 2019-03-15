from dataclasses import dataclass
from typing import *

from .test_utils import relies_on_missing_features, assert_object_roundtrip


@relies_on_missing_features
def test_not_implemented_set():
    @dataclass
    class MyClass:
        f: Set[int]

    e = MyClass({1, 2, 3})
    assert_object_roundtrip(e, {})  # pragma: no cover


@relies_on_missing_features
def test_not_implemented_set_2():
    @dataclass
    class A:
        a: int

    @dataclass
    class MyClass:
        f: Set[A]

    e = MyClass({A(1), A(2)})
    assert_object_roundtrip(e, {})  # pragma: no cover
