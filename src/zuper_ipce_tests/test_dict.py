from typing import Any, cast, Dict, Type

from nose.tools import assert_equal, raises

from zuper_ipce import ipce_from_object, object_from_ipce
from zuper_typing import dataclass
from zuper_typing.my_dict import get_DictLike_args, make_dict, make_list, make_set
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_dict_int_int0():
    D = make_dict(int, int)
    assert_type_roundtrip(D)


def test_dict_int_int1():
    D = Dict[int, int]
    # pprint(schema=ipce_from_typelike(D))

    assert_type_roundtrip(D)
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
    assert_object_roundtrip(e)


@raises(ValueError)
def test_dict_err():
    # noinspection PyTypeChecker
    make_dict(int, "str")


def test_dict_int_str():
    D = make_dict(str, int)
    assert_type_roundtrip(D)


def test_dict_int_str2():
    D = make_dict(str, int)
    d = D({"a": 1, "b": 2})
    assert assert_object_roundtrip(d)


def test_dict_int_str3():
    D = make_dict(str, int)

    @dataclass
    class C:
        d: D

    assert_type_roundtrip(C)

    d = D({"a": 1, "b": 2})
    c = C(d)
    res = assert_object_roundtrip(c)
    x1b = res["x1b"]
    # print(f"x1b: {debug_print(res['x1b'])}")
    K, V = get_DictLike_args(type(x1b.d))
    assert_equal(V, int)


def test_dict_int_str4_type():
    D = make_dict(str, int)
    ipce = ipce_from_object(D)
    D2 = object_from_ipce(ipce)

    D = cast(Type[Dict], D)
    K, V = get_DictLike_args(D)
    D2 = cast(Type[Dict], D2)
    K2, V2 = get_DictLike_args(D2)
    assert_equal((K, V), (K2, V2))


def test_dict_int_str4():
    D = make_dict(str, int)

    c = D({"a": 1, "b": 2})
    K, V = get_DictLike_args(type(c))
    debug_print = str
    # logger.info(f"c: {debug_print(c)}")

    ipce = ipce_from_object(c)
    c2 = object_from_ipce(ipce)

    # logger.info(f"ipce: {oyaml_dump(ipce)}")
    # logger.info(f"c2: {debug_print(c2)}")

    K2, V2 = get_DictLike_args(cast(Type[dict], type(c2)))
    assert_equal((K, V), (K2, V2))


def test_dict_kv01():
    x = get_DictLike_args(dict)
    assert_equal(x, (Any, Any))


def test_dict_kv02():
    x = get_DictLike_args(Dict)
    assert_equal(x, (Any, Any))


def test_dict_kv03():
    x = get_DictLike_args(Dict[int, str])
    assert_equal(x, (int, str))


def test_dict_copy():
    T = make_dict(int, str)
    x = T({1: "a"})
    y = x.copy()
    assert type(y) is T


def test_set_copy():
    T = make_set(int)
    x = T({1})
    y = x.copy()
    assert type(y) is T


def test_list_copy():
    T = make_list(int)
    x = T([1])
    y = x.copy()
    assert type(y) is T
