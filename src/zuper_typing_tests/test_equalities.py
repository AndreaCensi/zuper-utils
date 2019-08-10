from typing import List, Set

from nose.tools import assert_equal

from zuper_typing.annotations_tricks import is_Dict, is_List, is_Set
from zuper_typing.monkey_patching_typing import original_dict_getitem
from zuper_typing.my_dict import make_dict, make_list, make_set


def test_eq_list1():
    a = make_list(int)
    b = make_list(int)
    assert a == b
    assert_equal(a, b)


def test_eq_set():
    a = make_set(int)
    b = make_set(int)
    assert a == b
    assert_equal(a, b)


def test_eq_dict():
    a = make_dict(int, str)
    b = make_dict(int, str)

    assert a == b
    assert_equal(a, b)


def test_eq_list2():
    a = make_list(int)
    b = List[int]
    print(type(a), type(b))
    assert is_List(b), type(b)
    assert not is_List(a), a

    assert a == b


def test_eq_dict2():
    a = make_dict(int, str)
    print(original_dict_getitem)
    b = original_dict_getitem((int, str))
    print(type(a), type(b))
    assert is_Dict(b), type(b)
    assert not is_Dict(a), a

    assert a == b


def test_eq_set2():
    a = make_set(int)
    b = Set[int]
    print(type(a), type(b))
    assert is_Set(b), type(b)
    assert not is_Set(a), a
    assert a == b
