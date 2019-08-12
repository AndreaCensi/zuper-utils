from dataclasses import dataclass, field
from typing import List

from zuper_ipce.constants import USE_REMEMBERED_CLASSES
from zuper_ipce_tests.test_utils import assert_object_roundtrip, assert_type_roundtrip
from zuper_typing_tests.test_utils import known_failure

if not USE_REMEMBERED_CLASSES: # pragma: no cover
    @known_failure
    def test_default_arguments():
        @dataclass
        class A1b:
            a: List[int] = field(default_factory=list)

        F = assert_type_roundtrip(A1b, {}, expect_type_equal=False)
        F(a=[])
        F()


@known_failure
def test_object():
    T = object
    assert_type_roundtrip(T, {})


def test_slice():
    T = slice
    assert_type_roundtrip(T, {})


def test_slice1():
    T = slice(1, None, None)
    assert_object_roundtrip(T, {})


def test_slice2():
    T = slice(1, 2, None)
    assert_object_roundtrip(T, {})


def test_slice3():
    T = slice(1, 2, 3)
    assert_object_roundtrip(T, {})
