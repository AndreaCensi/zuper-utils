from typing import Set

from nose.tools import assert_equal

from zuper_typing.my_dict import make_set, get_SetLike_name


def test_set_1():
    X = Set[int]
    n = get_SetLike_name(X)
    assert_equal(n, "Set[int]")


def test_set_2():
    X = make_set(int)
    n = get_SetLike_name(X)
    assert_equal(n, "Set[int]")
