from dataclasses import dataclass
from typing import *

import yaml
from nose.tools import raises

from zuper_json.ipce import ipce_to_object, object_to_ipce, type_to_schema
from zuper_json.subcheck import can_be_used_as


def test_corner_cases01():
    assert None is ipce_to_object(None, {}, {}, expect_type=Optional[int])


def test_corner_cases02():
    assert 2 == ipce_to_object(2, {}, {}, expect_type=Optional[int])


def test_corner_cases03():
    assert None is ipce_to_object(None, {}, {}, expect_type=None)


def test_corner_cases04():
    object_to_ipce({1: 2}, {}, suggest_type=None)


def test_corner_cases05():
    object_to_ipce(12, {}, suggest_type=Optional[int])


def test_corner_cases06():
    assert can_be_used_as(int, Optional[int])[0]


@raises(ValueError)
def test_corner_cases07():
    ipce_to_object(12, {}, expect_type=Union[bool, str])


@raises(ValueError)
def test_corner_cases08():
    ipce_to_object(12, {}, expect_type=Optional[bool])


@raises(ValueError)
def test_corner_cases09():
    type_to_schema(None, {})



@raises(ValueError)
def test_property_error():
    @dataclass
    class MyClass32:
        a: int

    ok, _ = can_be_used_as(str, int)
    assert not ok

    # noinspection PyTypeChecker
    ob = MyClass32('not an int')
    # ipce_to_object(ob, {}, {}, expect_type=MyClass32)
    res = object_to_ipce(ob, {}, {})
    print(yaml.dump(res))


@raises(NotImplementedError)
def test_not_know():
    class C:
        pass

    object_to_ipce(C(), {}, {})


if __name__ == '__main__':
    test_property_error()
