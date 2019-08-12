from typing import Iterable, List

from zuper_typing.annotations_tricks import get_Iterable_arg, get_List_arg, is_Any


def test_list_1():
    X = get_List_arg(List)
    assert is_Any(X), X


def test_iterable1():
    X = get_Iterable_arg(Iterable)
    assert is_Any(X), X


def test_iterable2():
    X = get_Iterable_arg(Iterable[int])
    assert X is int, X
