from dataclasses import dataclass
from typing import Any, Generic, NewType, Optional, TypeVar, Union, Type

import yaml
from nose.tools import assert_equal, raises

from zuper_ipce.constants import check_types
from zuper_ipce.conv_ipce_from_object import ipce_from_object
from zuper_ipce.conv_object_from_ipce import object_from_ipce
from zuper_ipce.conv_typelike_from_ipce import typelike_from_ipce
from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike
from zuper_ipce_tests.test_utils import assert_object_roundtrip, assert_type_roundtrip

from zuper_typing.annotations_tricks import (get_NewType_arg, get_NewType_name, get_NewType_repr, is_Any, is_NewType,
                                             name_for_type_like, is_Type)
from zuper_typing.my_dict import get_CustomSet_arg, get_ListLike_arg, make_set
from zuper_typing.subcheck import can_be_used_as2


def test_corner_cases01():
    assert None is object_from_ipce(None, {}, {}, expect_type=Optional[int])


def test_corner_cases02():
    assert 2 == object_from_ipce(2, {}, {}, expect_type=Optional[int])


def test_corner_cases03():
    assert None is object_from_ipce(None, {}, {}, expect_type=None)


def test_corner_cases04():
    ipce_from_object({1: 2}, {}, suggest_type=None)


def test_corner_cases05():
    ipce_from_object(12, {}, suggest_type=Optional[int])


@raises(ValueError)
def test_corner_cases09():
    ipce_from_typelike(None, {})


@raises(ValueError)
def test_property_error():
    @dataclass
    class MyClass32:
        a: int

    ok = can_be_used_as2(str, int, {})
    assert not ok.result

    # noinspection PyTypeChecker
    ob = MyClass32('not an int')
    # ipce_to_object(ob, {}, {}, expect_type=MyClass32)
    res = ipce_from_object(ob, {}, {})
    # print(yaml.dump(res))


@raises(NotImplementedError)
def test_not_know():
    class C:
        pass

    ipce_from_object(C(), {}, {})

if check_types:
    @raises(TypeError)
    def test_corner_cases07():
        can0 = can_be_used_as2(int, bool, {})
        assert not can0, can0

        T = Union[bool, str]
        can = can_be_used_as2(int, T, {})
        assert not can, can
        object_from_ipce(12, {}, expect_type=T)


if check_types:
    @raises(TypeError)
    def test_corner_cases08():
        T = Optional[bool]
        assert not can_be_used_as2(int, T, {}).result
        object_from_ipce(12, {}, expect_type=Optional[bool])


def test_newtype1():
    T = NewType('a', int)
    assert is_NewType(T)
    assert_equal(get_NewType_arg(T), int)
    assert_equal(get_NewType_name(T), 'a')
    assert_equal(get_NewType_repr(T), "NewType('a', int)")
    assert_equal(name_for_type_like(T), "NewType('a', int)")


def test_newtype2():
    T = NewType('a', Any)
    assert is_NewType(T)
    assert is_Any(get_NewType_arg(T))
    assert_equal(get_NewType_repr(T), "NewType('a')")
    assert_equal(name_for_type_like(T), "NewType('a')")


def test_list0():
    v = get_ListLike_arg(list)
    assert is_Any(v)


def test_set0():
    a = get_CustomSet_arg(make_set(int))
    assert a is int


def test_default1():
    @dataclass
    class C:
        a: bool = False

    assert_type_roundtrip(C, {})

    ipce1 = ipce_from_typelike(C, {})
    C2 = typelike_from_ipce(ipce1, {}, {})
    # print(debug_print(C))
    # print(debug_print(C2))
    ipce2 = ipce_from_typelike(C2, {})
    assert ipce1 == ipce2


def test_default2():
    X = TypeVar('X')

    @dataclass
    class C(Generic[X]):
        a: bool = False

    assert_type_roundtrip(C, {})

    ipce1 = ipce_from_typelike(C, {})
    C2 = typelike_from_ipce(ipce1, {}, {})
    # print(debug_print(C))
    print(yaml.dump(ipce1))
    assert ipce1['properties']['a']['default'] == False
    # print(debug_print(C2))
    ipce2 = ipce_from_typelike(C2, {})
    assert ipce1 == ipce2


def test_type1():
    assert_type_roundtrip(type, {})
    assert_object_roundtrip(type, {})


def test_parsing():
    schema_bool = """{$schema: 'http://json-schema.org/draft-07/schema#', type: boolean}"""
    ipce = yaml.load(schema_bool)
    T0 = typelike_from_ipce(ipce, {}, {})
    assert T0 is bool, T0
    T0 = object_from_ipce(ipce, {})
    assert T0 is bool, T0
    a = """\
$schema:
  $id: http://invalid.json-schema.org/M#
  $schema: http://json-schema.org/draft-07/schema#
  __module__: zuper_ipce_tests.test_bool
  description: 'M(a: bool)'
  order: [a]
  properties:
    a: {$schema: 'http://json-schema.org/draft-07/schema#', type: boolean}
  required: [a]
  title: M
  type: object
  __qualname__: misc
a: true
    """
    ipce = yaml.load(a)

    T = typelike_from_ipce(ipce['$schema'], {}, {})
    print(T)
    print(T.__annotations__)
    assert T.__annotations__['a'] is bool, T.__annotations__

    ob = object_from_ipce(ipce, {})


def test_Type1():
    T = Type[int]
    assert is_Type(T)
