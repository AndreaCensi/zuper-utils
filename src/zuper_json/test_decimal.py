from dataclasses import dataclass
from decimal import Decimal

from .test_utils import relies_on_missing_features, assert_object_roundtrip, \
    with_private_register


@relies_on_missing_features
@with_private_register
def test_not_implemented_decimal_1():
    @dataclass
    class MyClass:
        f: Decimal

    e = MyClass(Decimal(1.0))
    assert_object_roundtrip(e, {})  # raise here
    e = MyClass(Decimal('0.3'))  # pragma: no cover
    assert_object_roundtrip(e, {})  # pragma: no cover
