from typing import List, Optional, Tuple, cast

from nose.tools import raises

from zuper_commons.logs import setup_logging
from zuper_ipce import typelike_from_ipce
from zuper_ipce.constants import JSONSchema
from zuper_ipce.utils_text import oyaml_load
from zuper_typing import dataclass
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_list_1():
    @dataclass
    class MyClass:
        f: List[int]

    e = MyClass([1, 2, 3])
    assert_object_roundtrip(e)


def test_tuple1a():
    @dataclass
    class MyClass:
        f: Tuple[int, ...]

    assert_type_roundtrip(MyClass)


def test_tuple1():
    @dataclass
    class MyClass:
        f: Tuple[int, ...]

    e = MyClass((1, 2, 3))
    assert_object_roundtrip(e)


def test_tuple2a():
    @dataclass
    class MyClass:
        f: Tuple[int, str]

    assert_type_roundtrip(MyClass)


def test_tuple2():
    @dataclass
    class MyClass:
        f: Tuple[int, str]

    e = MyClass((1, "a"))
    assert_object_roundtrip(e)


def test_tuple_inside_class():
    """ tuple inside needs a schema hint"""

    @dataclass
    class MyClass:
        f: object

    e = MyClass((1, 2))
    assert_object_roundtrip(e, works_without_schema=False)


@raises(AssertionError)
def test_tuple_inside_class_withoutschema():
    """ tuple inside needs a schema hint"""

    @dataclass
    class MyClass:
        f: object

    e = MyClass((1, 2))
    assert_object_roundtrip(e, works_without_schema=True)


def test_Optional_fields():
    @dataclass
    class MyClass:
        f: int
        g: Optional[int] = None

    e = MyClass(1)
    assert_object_roundtrip(e, works_without_schema=True)


def test_another():
    a = """\
$schema:
  $id: http://invalid.json-schema.org/A#
  $schema: http://json-schema.org/draft-07/schema#
  __module__: zuper_lang.compile_utils
  __qualname__: my_make_dataclass.<locals>.C
  order: [a]
  properties:
    a:
      $schema: http://json-schema.org/draft-07/schema#
      items: {$schema: 'http://json-schema.org/draft-07/schema#', type: string}
      title: List[str]
      type: array
  required: [a]
  title: A
  type: object

"""
    ipce = cast(JSONSchema, oyaml_load(a))
    r = typelike_from_ipce(ipce)
    # print(r)

    assert_type_roundtrip(r)


if __name__ == "__main__":
    setup_logging()
    test_tuple_inside_class()
