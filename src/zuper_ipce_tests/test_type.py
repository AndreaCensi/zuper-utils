import dataclasses
import json
from dataclasses import dataclass
from typing import *

from zuper_ipce.ipce import ipce_from_typelike, object_from_ipce, schema_to_type
from zuper_typing_tests.test_utils import relies_on_missing_features
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

symbols = {}


@relies_on_missing_features
def test_type1():
    T = Type
    assert_type_roundtrip(T, symbols)


def test_type2():
    T = type
    assert_type_roundtrip(T, symbols)


@relies_on_missing_features
def test_newtype():
    T = NewType('T', str)
    assert_type_roundtrip(T, symbols)


def test_dict1():
    c = {}
    assert_object_roundtrip(c, symbols)


def test_dict2():
    T = Dict[str, Any]
    # <class 'zuper_json.my_dict.Dict[str,Any]'>
    assert_type_roundtrip(T, symbols, expect_type_equal=False)


def test_dict4():
    # T = Dict[str, Any]
    # <class 'zuper_json.my_dict.Dict[str,Any]'>
    ob = {}
    object_from_ipce(ob, {}, expect_type=Any)


def test_type__any():
    T = Any
    assert_type_roundtrip(T, symbols)


def test_type_any2():
    @dataclass
    class C:
        a: Any

    c = C(a={})
    assert_object_roundtrip(c, symbols)


def test_type__any3():
    @dataclass
    class C:
        a: Any

    c = C(a=1)
    assert_object_roundtrip(c, symbols)


def test_type__any4():
    assert_object_roundtrip(Any, symbols)


def test_defaults1():
    @dataclass
    class DummyImageSourceConfig:
        shape: Tuple[int, int] = (480, 640)
        images_per_episode: int = 120
        num_episodes: int = 10

    mj = ipce_from_typelike(DummyImageSourceConfig, {})
    print(json.dumps(mj, indent=2))

    T2 = schema_to_type(mj, {}, {})
    print(dataclasses.fields(T2))

    assert_type_roundtrip(DummyImageSourceConfig, {})

def test_type_slice():
    assert_object_roundtrip(slice, {})


def test_type_slice2():
    s = slice(1, 2, 3)
    assert_object_roundtrip(s, {})
