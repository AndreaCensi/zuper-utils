from typing import List

from zuper_typing.annotations_tricks import get_List_arg, is_Any


def test_list_1():
    X = get_List_arg(List)
    assert is_Any(X), X
