from dataclasses import dataclass

from .test_utils import assert_object_roundtrip, \
    with_private_register


@with_private_register
def test_float_1():
    @dataclass
    class MyClass:
        f: float

    e = MyClass(1.0)
    assert_object_roundtrip(e, {})
