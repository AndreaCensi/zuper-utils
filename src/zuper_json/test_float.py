from dataclasses import dataclass

from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_float_1():
    @dataclass
    class MyClass:
        f: float

    e = MyClass(1.0)
    assert_object_roundtrip(e, {})

def test_float_2():
    @dataclass
    class MyClass:
        f: float

    T2 = assert_type_roundtrip(MyClass, {})

    print(T2)
    assert T2.__annotations__['f'] is float
