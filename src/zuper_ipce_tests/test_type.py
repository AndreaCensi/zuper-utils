from nose.tools import raises

from zuper_typing import dataclass
from zuper_typing.exceptions import ZValueError
from zuper_typing.logging import logger

logger.info("")

from typing import Type, NewType, Dict, Any, Tuple

from zuper_ipce import object_from_ipce
from zuper_ipce import typelike_from_ipce
from zuper_ipce import ipce_from_typelike
from zuper_typing_tests.test_utils import relies_on_missing_features
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

symbols = {}


@relies_on_missing_features
def test_type1():
    T = Type
    assert_type_roundtrip(T, use_globals=symbols)


def test_type2():
    T = type
    assert_type_roundtrip(T, use_globals=symbols)


def test_newtype():
    T = NewType("T", str)
    assert_type_roundtrip(T, use_globals=symbols)


def test_dict1():
    c = {}
    assert_object_roundtrip(c, use_globals=symbols)


def test_dict2():
    T = Dict[str, Any]
    # <class 'zuper_json.my_dict.Dict[str,Any]'>
    assert_type_roundtrip(T, use_globals=symbols, expect_type_equal=False)


@raises(ValueError)
def test_dict4():
    ob = {}
    object_from_ipce(ob, Any)


def test_type__any():
    T = Any
    assert_type_roundtrip(T, use_globals=symbols)


@raises(ZValueError)
def test_type_any2():
    @dataclass
    class C:
        a: Any

    c = C(a={})
    assert_object_roundtrip(c, use_globals=symbols)


def test_type__any3():
    @dataclass
    class C:
        a: Any

    c = C(a=1)
    assert_object_roundtrip(c, use_globals=symbols)


def test_type__any4():
    assert_object_roundtrip(Any, use_globals=symbols)


def test_defaults1():
    @dataclass
    class DummyImageSourceConfig:
        shape: Tuple[int, int] = (480, 640)
        images_per_episode: int = 120
        num_episodes: int = 10

    mj = ipce_from_typelike(DummyImageSourceConfig)
    # print(json.dumps(mj, indent=2))

    T2: Type[dataclass] = typelike_from_ipce(mj)
    # print(dataclasses.fields(T2))

    assert_type_roundtrip(DummyImageSourceConfig)


def test_type_slice():
    assert_object_roundtrip(slice)


def test_type_slice2():
    s = slice(1, 2, 3)
    assert_object_roundtrip(s)
