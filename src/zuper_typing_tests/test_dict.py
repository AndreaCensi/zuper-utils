from typing import Dict

from zuper_typing.annotations_tricks import get_Dict_args, is_Any


def test_dict_1():
    K, V = get_Dict_args(Dict)
    assert is_Any(K), K
    assert is_Any(V), V
