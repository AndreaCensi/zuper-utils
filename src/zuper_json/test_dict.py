from dataclasses import dataclass
from typing import *

from nose.tools import raises

from zuper_json.ipce import make_dict, type_to_schema
from .pretty import pprint
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


@raises(ValueError)
def test_dict_check_key():
    D = Dict[int, int]
    d = D()
    d['a'] = 2


@raises(ValueError)
def test_dict_check_value():
    D = Dict[int, int]
    d = D()
    d[2] = 'a'



def test_dict_int_int0():
    D = make_dict(int, int)
    assert_type_roundtrip(D, {})



def test_dict_int_int1():
    D = Dict[int, int]
    pprint(schema=type_to_schema(D, {}))

    assert_type_roundtrip(D, {})
    # @dataclass
    # class MyClass:
    #     f: Dict[int, int]
    #
    # e = MyClass({1: 2})
    # assert_object_roundtrip(e, {})



def test_dict_int_int():
    @dataclass
    class MyClass:
        f: Dict[int, int]

    e = MyClass({1: 2})
    assert_object_roundtrip(e, {})
