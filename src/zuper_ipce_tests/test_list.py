from dataclasses import dataclass
from typing import List, Tuple, Any, Optional

from nose.tools import raises

from zuper_commons.logs import setup_logging
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_list_1():
    @dataclass
    class MyClass:
        f: List[int]

    e = MyClass([1, 2, 3])
    assert_object_roundtrip(e, {})


def test_tuple1a():
    @dataclass
    class MyClass:
        f: Tuple[int, ...]

    assert_type_roundtrip(MyClass, {})


def test_tuple1():
    @dataclass
    class MyClass:
        f: Tuple[int, ...]

    e = MyClass((1, 2, 3))
    assert_object_roundtrip(e, {})


def test_tuple2a():
    @dataclass
    class MyClass:
        f: Tuple[int, str]

    assert_type_roundtrip(MyClass, {})


def test_tuple2():
    @dataclass
    class MyClass:
        f: Tuple[int, str]

    e = MyClass((1, 'a'))
    assert_object_roundtrip(e, {})



def test_tuple_inside_class():
    """ tuple inside needs a schema hint"""
    @dataclass
    class MyClass:
        f: Any

    e = MyClass((1, 2))
    assert_object_roundtrip(e, {}, works_without_schema=False)

@raises(AssertionError)
def test_tuple_inside_class_withoutschema():
    """ tuple inside needs a schema hint"""
    @dataclass
    class MyClass:
        f: Any

    e = MyClass((1, 2))
    assert_object_roundtrip(e, {}, works_without_schema=True)



def test_Optional_fields():

    @dataclass
    class MyClass:
        f: int
        g: Optional[int] = None

    e = MyClass(1)
    assert_object_roundtrip(e, {}, works_without_schema=True)


if __name__ == '__main__':
    setup_logging()
    test_tuple_inside_class()
