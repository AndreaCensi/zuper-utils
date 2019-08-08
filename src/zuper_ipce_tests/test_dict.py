from typing import Any, Dict, List, Set

from nose.tools import assert_equal, raises

from zuper_ipce import logger
from zuper_ipce.ipce import ipce_from_object, make_dict, object_from_ipce, ipce_from_typelike
from zuper_ipce.pretty import pprint
from zuper_typing import dataclass
from zuper_typing.annotations_tricks import get_Set_arg, is_Any, is_List, is_Set
from zuper_typing.my_dict import (get_DictLike_args, get_ListLike_arg, get_SetLike_arg, is_ListLike,
                                  make_set, is_SetLike)
from .test_utils import assert_object_roundtrip, assert_type_roundtrip

if False:
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
    pprint(schema=ipce_from_typelike(D, {}))

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


@raises(ValueError)
def test_dict_err():
    make_dict(int, 'str')


def test_dict_hash():
    s = set()
    s2 = set()
    D = make_dict(str, str)
    d = D()
    s.add(d)
    s2.add(d)


def test_set_hash():
    s = set()
    s2 = set()
    D = make_set(str)
    d = D()
    s.add(d)
    s2.add(d)


def test_dict_int_str():
    D = make_dict(str, int)
    assert_type_roundtrip(D, {})


def test_dict_int_str2():
    D = make_dict(str, int)
    d = D({'a': 1, 'b': 2})
    assert assert_object_roundtrip(d, {})


def test_dict_int_str3():
    D = make_dict(str, int)

    @dataclass
    class C:
        d: D

    assert_type_roundtrip(C, {})

    d = D({'a': 1, 'b': 2})
    c = C(d)
    res = assert_object_roundtrip(c, {})
    x1b = res['x1b']
    # print(f"x1b: {debug_print(res['x1b'])}")
    K, V = get_DictLike_args(type(x1b.d))
    assert_equal(V, int)


def test_dict_int_str4_type():
    D = make_dict(str, int)
    ipce = ipce_from_object(D)
    D2 = object_from_ipce(ipce, {})

    K, V = get_DictLike_args(D)
    K2, V2 = get_DictLike_args(D2)
    assert_equal((K, V), (K2, V2))


def test_dict_int_str4():
    D = make_dict(str, int)

    c = D({'a': 1, 'b': 2})
    K, V = get_DictLike_args(type(c))
    debug_print = str
    logger.info(f'c: {debug_print(c)}')

    ipce = ipce_from_object(c)
    c2 = object_from_ipce(ipce, {})
    import yaml
    logger.info(f'ipce: {yaml.dump(ipce)}')
    logger.info(f'c2: {debug_print(c2)}')

    K2, V2 = get_DictLike_args(type(c2))
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


def test_set_misc01():
    assert is_SetLike(Set)


def test_set_misc02():
    assert is_SetLike(Set[int])


def test_set_misc03():
    assert is_SetLike(set)


def test_set_misc04():
    assert is_SetLike(make_set(int))


def test_set_getvalue01():
    assert is_Set(Set[int])
    assert get_SetLike_arg(Set[int]) is int


def test_set_getvalue02():
    assert is_Set(Set)
    x = get_Set_arg(Set)
    assert is_Any(x), x
    x = get_SetLike_arg(Set)
    assert is_Any(x), x


def test_set_getvalue03():
    assert get_SetLike_arg(make_set(int)) is int


def test_set_getvalue04():
    assert is_Any(get_SetLike_arg(set))


def test_list_is01():
    assert is_List(List)


def test_list_is02():
    assert is_List(List[int])


def test_list_is03():
    assert not is_List(list)


def test_list_arg01():
    x = get_ListLike_arg(List)
    assert is_Any(x), x


def test_list_arg02():
    x = get_ListLike_arg(list)
    assert is_Any(x), x


def test_list_arg03():
    assert get_ListLike_arg(List[int]) is int


def test_islist_01():
    assert is_ListLike(list)


def test_islist_02():
    assert is_ListLike(List)


def test_islist_03():
    assert is_ListLike(List[int])
