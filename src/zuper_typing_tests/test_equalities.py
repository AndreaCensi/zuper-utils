from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, TypeVar

from nose.tools import assert_equal, raises

from zuper_typing.get_patches_ import NotEquivalentException, assert_equivalent_types
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
    # print(type(a), type(b))
    assert is_List(b), type(b)
    assert not is_List(a), a

    assert a == b


def test_eq_dict2():
    a = make_dict(int, str)
    # print(original_dict_getitem)
    b = original_dict_getitem((int, str))
    # print(type(a), type(b))
    assert is_Dict(b), type(b)
    assert not is_Dict(a), a

    assert a == b


def test_eq_set2():
    a = make_set(int)
    b = Set[int]
    # print(type(a), type(b))
    assert is_Set(b), type(b)
    assert not is_Set(a), a
    assert a == b


@raises(NotEquivalentException)
def test_cover_equiv0():
    @dataclass
    class Eq1:
        pass

    assert_equivalent_types(Eq1, bool, set())


@raises(NotEquivalentException)
def test_cover_equiv1():
    @dataclass
    class Eq2:
        pass

    assert_equivalent_types(bool, Eq2, set())


@raises(NotEquivalentException)
def test_cover_equiv2():
    @dataclass
    class Eq3:
        pass

    @dataclass
    class Eq4:
        a: int

    assert_equivalent_types(Eq4, Eq3, set())


@raises(NotEquivalentException)
def test_cover_equiv03():
    assert_equivalent_types(ClassVar[int], bool, set())


@raises(NotEquivalentException)
def test_cover_equiv04():
    assert_equivalent_types(Dict[int, bool], bool, set())


@raises(NotEquivalentException)
def test_cover_equiv05():
    assert_equivalent_types(List[int], bool, set())


@raises(NotEquivalentException)
def test_cover_equiv06():
    assert_equivalent_types(Any, bool, set())


@raises(NotEquivalentException)
def test_cover_equiv07():
    assert_equivalent_types(Set[int], bool, set())


@raises(NotEquivalentException)
def test_cover_equiv08():
    X = TypeVar("X")
    assert_equivalent_types(X, bool, set())


@raises(NotEquivalentException)
def test_cover_equiv09():
    X = TypeVar("X")
    Y = TypeVar("Y")
    assert_equivalent_types(X, Y, set())


@raises(NotEquivalentException)
def test_cover_equiv10():
    X = Tuple[int, bool]
    assert_equivalent_types(X, bool, set())


@raises(NotEquivalentException)
def test_cover_equiv11():
    X = Tuple[int, ...]
    assert_equivalent_types(X, bool, set())


@raises(NotEquivalentException)
def test_cover_equiv12():
    X = Tuple[int, bool]
    Y = Tuple[int, str]
    assert_equivalent_types(X, Y, set())


@raises(NotEquivalentException)
def test_cover_equiv13():
    X = Tuple[int, ...]
    Y = Tuple[bool, ...]
    assert_equivalent_types(X, Y, set())


@raises(NotEquivalentException)
def test_cover_equiv14():
    X = Optional[int]
    Y = Optional[bool]
    assert_equivalent_types(X, Y, set())
