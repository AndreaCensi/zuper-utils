from dataclasses import is_dataclass
from typing import Tuple, TypeVar

from zuper_typing.exceptions import ZValueError
from .types import IPCE

D = TypeVar("D")


def sorted_dict_with_cbor_ordering(x: D) -> D:
    def key(item: Tuple[str, object]) -> tuple:
        k, v = item
        return (len(k), k)

    res = dict(sorted(x.items(), key=key))

    assert_sorted_dict_with_cbor_ordering(res)
    return res


def sorted_list_with_cbor_ordering(x: list) -> list:
    def key(k: str) -> Tuple[int, str]:
        return (len(k), k)

    return sorted(x, key=key)


IPCL_LINKS = "$links"
IPCL_SELF = "$self"


def assert_sorted_dict_with_cbor_ordering(x: dict):
    keys = list(x.keys())
    keys2 = sorted_list_with_cbor_ordering(keys)
    if keys != keys2:
        msg = f"x not sorted"
        raise ZValueError(msg, keys=keys, keys2=keys2)


def assert_canonical_ipce(ob_ipce: IPCE, max_rec=2):
    if isinstance(ob_ipce, dict):
        if "/" in ob_ipce:
            msg = 'Cannot have "/" in here '
            raise ZValueError(msg, ob_ipce=ob_ipce)
        assert_sorted_dict_with_cbor_ordering(ob_ipce)

        if IPCL_LINKS in ob_ipce:
            msg = f"Should have dropped the {IPCL_LINKS} part."
            raise ZValueError(msg, ob_ipce=ob_ipce)
        if IPCL_SELF in ob_ipce:
            msg = f"Re-processing the {IPCL_LINKS}."
            raise ZValueError(msg, ob_ipce=ob_ipce)

        for k, v in ob_ipce.items():
            assert not is_dataclass(v), ob_ipce
            if max_rec > 0:
                assert_canonical_ipce(v, max_rec=max_rec - 1)
    elif isinstance(ob_ipce, list):
        pass
    elif isinstance(ob_ipce, tuple):
        msg = "Tuple is not valid."
        raise ZValueError(msg, ob_ipce=ob_ipce)
