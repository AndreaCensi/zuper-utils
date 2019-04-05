from dataclasses import dataclass
from decimal import Decimal

from .test_utils import relies_on_missing_features, assert_object_roundtrip



def test_decimal1():
    @dataclass
    class MyClass:
        f: Decimal

    e = MyClass(Decimal(1.0))
    assert_object_roundtrip(e, {})
    e = MyClass(Decimal('0.3'))
    assert_object_roundtrip(e, {})

def test_decimal2():

    f = Decimal('3.14')

    assert_object_roundtrip(f, {})
