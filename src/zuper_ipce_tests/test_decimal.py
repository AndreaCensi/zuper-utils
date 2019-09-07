from decimal import Decimal

from zuper_typing import dataclass
from .test_utils import assert_object_roundtrip


def test_decimal1():
    @dataclass
    class MyClass:
        f: Decimal

    e = MyClass(Decimal(1.0))
    assert_object_roundtrip(e)
    e = MyClass(Decimal("0.3"))
    assert_object_roundtrip(e)


def test_decimal2():
    f = Decimal("3.14")

    assert_object_roundtrip(f)
