import json
from dataclasses import dataclass
from typing import *

from .ipce import ipce_to_object, type_to_schema, schema_to_type
from .test_utils import relies_on_missing_features, assert_type_roundtrip, assert_object_roundtrip, known_failure

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


@known_failure
def test_dict4():
    # T = Dict[str, Any]
    # <class 'zuper_json.my_dict.Dict[str,Any]'>
    ob = {}
    ipce_to_object(ob, {}, expect_type=Any)


def test_any():
    T = Any
    assert_type_roundtrip(T, symbols)


@known_failure
def test_any2():
    @dataclass
    class C:
        a: Any

    c = C(a={})
    assert_object_roundtrip(c, symbols)


def test_any3():
    @dataclass
    class C:
        a: Any

    c = C(a=1)
    assert_object_roundtrip(c, symbols)


def test_any4():
    assert_object_roundtrip(Any, symbols)


def test_defaults1():
    @dataclass
    class DummyImageSourceConfig:
        shape: Tuple[int, int] = (480, 640)
        images_per_episode: int = 120
        num_episodes: int = 10

    mj = type_to_schema(DummyImageSourceConfig, {})
    print(json.dumps(mj, indent=2))

    T2 = schema_to_type(mj, {}, {})
    print(dataclasses.fields(T2))


import dataclasses
