from typing import *

from nose.tools import raises, assert_equal
from zuper_typing import dataclass
from zuper_typing.annotations_tricks import is_Any, is_Set, is_List
from zuper_typing.my_dict import (is_set_or_CustomSet, make_set, get_set_Set_or_CustomSet_Value, get_list_List_Value,
                                  is_list_or_List, get_Dict_or_CustomDict_Key_Value)
from zuper_ipce.ipce import make_dict, type_to_schema, ipce_from_object, object_from_ipce
from zuper_ipce.pretty import pprint
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
    from zuper_ipcl import debug_print
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
    K, V = get_Dict_or_CustomDict_Key_Value(type(x1b.d))
    assert_equal(V, int)


from zuper_ipce import logger


def test_dict_int_str4_type():
    D = make_dict(str, int)
    ipce = ipce_from_object(D)
    D2 = object_from_ipce(ipce, {})

    K, V = get_Dict_or_CustomDict_Key_Value(D)
    K2, V2 = get_Dict_or_CustomDict_Key_Value(D2)
    assert_equal((K, V), (K2, V2))


def test_dict_int_str4():
    D = make_dict(str, int)

    c = D({'a': 1, 'b': 2})
    K, V = get_Dict_or_CustomDict_Key_Value(type(c))
    debug_print = str
    logger.info(f'c: {debug_print(c)}')

    ipce = ipce_from_object(c)
    c2 = object_from_ipce(ipce, {})
    import yaml
    logger.info(f'ipce: {yaml.dump(ipce)}')
    logger.info(f'c2: {debug_print(c2)}')

    K2, V2 = get_Dict_or_CustomDict_Key_Value(type(c2))
    assert_equal((K, V), (K2, V2))


def test_dict_kv01():
    x = get_Dict_or_CustomDict_Key_Value(dict)
    assert_equal(x, (Any, Any))


def test_dict_kv02():
    x = get_Dict_or_CustomDict_Key_Value(Dict)
    assert_equal(x, (Any, Any))


def test_dict_kv03():
    x = get_Dict_or_CustomDict_Key_Value(Dict[int, str])
    assert_equal(x, (int, str))


def test_set_misc01():
    assert is_set_or_CustomSet(Set)


def test_set_misc02():
    assert is_set_or_CustomSet(Set[int])


def test_set_misc03():
    assert is_set_or_CustomSet(set)


def test_set_misc04():
    assert is_set_or_CustomSet(make_set(int))


def test_set_getvalue01():
    assert is_Set(Set[int])
    assert get_set_Set_or_CustomSet_Value(Set[int]) is int


def test_set_getvalue02():
    assert is_Set(Set)
    x = get_set_Set_or_CustomSet_Value(Set)
    assert is_Any(x), x


def test_set_getvalue03():
    assert get_set_Set_or_CustomSet_Value(make_set(int)) is int


def test_set_getvalue04():
    assert is_Any(get_set_Set_or_CustomSet_Value(set))


def test_list_is01():
    assert is_List(List)


def test_list_is02():
    assert is_List(List[int])


def test_list_is03():
    assert not is_List(list)


def test_list_arg01():
    x = get_list_List_Value(List)
    assert is_Any(x), x


def test_list_arg02():
    x = get_list_List_Value(list)
    assert is_Any(x), x


def test_list_arg03():
    assert get_list_List_Value(List[int]) is int


def test_islist_01():
    assert is_list_or_List(list)


def test_islist_02():
    assert is_list_or_List(List)


def test_islist_03():
    assert is_list_or_List(List[int])
