from dataclasses import is_dataclass
from typing import TypeVar

from .types import IPCE

D = TypeVar("D")


def sorted_dict_with_cbor_ordering(x: D) -> D:
    def key(item):
        k, v = item
        return (len(k), k)

    res = dict(sorted(x.items(), key=key))

    assert_sorted_dict_with_cbor_ordering(res)
    return res


def sorted_list_with_cbor_ordering(x):
    def key(k):
        return (len(k), k)

    return sorted(x, key=key)


def assert_sorted_dict_with_cbor_ordering(x: dict):
    keys = list(x.keys())
    keys2 = sorted_list_with_cbor_ordering(keys)
    if keys != keys2:
        msg = f"x not sorted:\n{keys}\n{keys2}\n{x}"
        raise ValueError(msg)


def assert_canonical_ipce(ob_ipce: IPCE, max=2):
    if isinstance(ob_ipce, dict):
        if "/" in ob_ipce:
            raise ValueError(ob_ipce)
        assert_sorted_dict_with_cbor_ordering(ob_ipce)

        if "$links" in ob_ipce:
            msg = f"Should have dropped the $links part."
            raise ValueError(msg)
        if "$self" in ob_ipce:
            msg = f"Re-processing the $links: {ob_ipce}."
            raise ValueError(msg)

        for k, v in ob_ipce.items():
            assert not is_dataclass(v), ob_ipce
            if max > 0:
                assert_canonical_ipce(v, max=max - 1)
    elif isinstance(ob_ipce, list):
        pass
    elif isinstance(ob_ipce, tuple):
        raise ValueError(ob_ipce)
        # links = set(get_links_hash(x))
        #
        # if links:
        #     msg = f'Should not contain links, found {links}'
        #     raise ValueError(msg)
