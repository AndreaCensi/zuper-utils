from typing import TypeVar

from zuper_typing import dataclass, Generic


def test_hash1():
    @dataclass
    class Parametric1:
        a: int
        b: int

    p1 = Parametric1(0, 1)
    assert p1.__hash__ is not None
    X = TypeVar("X")

    @dataclass(unsafe_hash=True)
    class Parametric2(Generic[X]):
        a: X
        b: X

    p2 = Parametric2[int](1, 2)
    assert p2.__hash__ is not None
