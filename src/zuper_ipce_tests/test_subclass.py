from typing import TypeVar

from zuper_typing import dataclass, Generic
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

symbols = {}


def test_subclass1():
    @dataclass
    class A:
        a: int

    @dataclass
    class B(A):
        b: bool

    # print(type(B))
    # print(f'bases for B: {B.__bases__}')
    # print(f'mro for B: {B.mro()}')

    assert A in B.__bases__

    b = B(1, True)

    assert_type_roundtrip(B)
    assert_object_roundtrip(b)


def test_subclass2_generic():
    X = TypeVar("X")

    @dataclass
    class A(Generic[X]):
        a: X

    @dataclass
    class B(A[int]):
        b: bool

    b = B(1, True)

    assert_type_roundtrip(B)
    assert_object_roundtrip(b)


def test_subclass3_generic():
    X = TypeVar("X")

    @dataclass
    class S3A(Generic[X]):
        a: X

    @dataclass
    class S3B0(S3A):
        b: bool

    S3B = S3B0[int]
    b = S3B(1, True)

    assert S3B0.__name__ == "S3B0[X]", S3B0.__name__

    assert_type_roundtrip(S3B0)

    assert_type_roundtrip(S3A)
    assert_type_roundtrip(S3B)
    assert_object_roundtrip(b)


if __name__ == "__main__":
    test_subclass3_generic()
