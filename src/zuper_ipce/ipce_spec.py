from dataclasses import is_dataclass
from typing import Dict, List, overload, Tuple, TypeVar

from zuper_ipce.constants import JSONSchema
from zuper_typing.exceptions import ZValueError
from .types import IPCE

D = TypeVar("D")

_V = TypeVar("_V")


@overload
def sorted_dict_cbor_ord(x: JSONSchema) -> JSONSchema:
    ...


@overload
def sorted_dict_cbor_ord(x: Dict[str, _V]) -> Dict[str, _V]:
    ...


def sorted_dict_cbor_ord(x):
    def key(item: Tuple[str, object]) -> Tuple[int, str]:
        k, v = item
        return (len(k), k)

    res = dict(sorted(x.items(), key=key))

    assert_sorted_dict_cbor_ord(res)
    return res


def sorted_list_cbor_ord(x: List[str]) -> List[str]:
    def key(k: str) -> Tuple[int, str]:
        return (len(k), k)

    return sorted(x, key=key)


IPCL_LINKS = "$links"
IPCL_SELF = "$self"


def assert_sorted_dict_cbor_ord(x: dict):
    keys = list(x.keys())
    keys2 = sorted_list_cbor_ord(keys)
    if keys != keys2:
        msg = f"x not sorted"
        raise ZValueError(msg, keys=keys, keys2=keys2)


def assert_canonical_ipce(ob_ipce: IPCE, max_rec=2) -> None:
    if isinstance(ob_ipce, dict):
        if "/" in ob_ipce:
            msg = 'Cannot have "/" in here '
            raise ZValueError(msg, ob_ipce=ob_ipce)
        assert_sorted_dict_cbor_ord(ob_ipce)

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
