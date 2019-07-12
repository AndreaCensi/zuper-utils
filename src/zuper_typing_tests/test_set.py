from typing import Set

from nose.tools import assert_equal

from zuper_typing.annotations_tricks import get_Set_or_CustomSet_name
from zuper_typing.my_dict import make_set


def test_set_1():
    X = Set[int]
    n = get_Set_or_CustomSet_name(X)
    assert_equal(n, 'Set[int]')


def test_set_2():
    X = make_set(int)
    n = get_Set_or_CustomSet_name(X)
    assert_equal(n, 'Set[int]')
