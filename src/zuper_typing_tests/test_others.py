from typing import List, Set

from zuper_typing.annotations_tricks import get_Set_arg, is_Any, is_List, is_Set
from zuper_typing.my_dict import (
    get_ListLike_arg,
    get_SetLike_arg,
    is_ListLike,
    is_SetLike,
    make_dict,
    make_set,
)


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
