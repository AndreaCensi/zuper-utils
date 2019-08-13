from typing import Dict, List, Optional, Set, Tuple, Union

from zuper_commons.text import pretty_dict
from zuper_ipce import logger
from zuper_ipce.assorted_recursive_type_subst import recursive_type_subst
from zuper_ipce_tests.test_utils import assert_equivalent_types, assert_type_roundtrip, make_ForwardRef
from zuper_typing import dataclass
from zuper_typing.my_dict import make_dict, make_list, make_set


def test_rec1():
    @dataclass
    class A:
        a: Dict[int, bool]
        a2: Dict[bool, bool]
        b: Union[int, bool]
        b2: Dict[bool, float]
        c: Set[int]
        c2: Set[bool]
        d: List[int]
        d2: List[bool]
        e: Tuple[int, bool]
        e2: Tuple[float, bool]
        f: make_dict(int, int)
        g: make_set(int)
        h: make_list(int)
        i: Optional[int]
        l: Tuple[int, ...]

    def swap(x):
        if x is int:
            return str
        if x is str:
            return int
        return x

    T2 = recursive_type_subst(A, swap)

    T3 = recursive_type_subst(T2, swap)
    logger.info(pretty_dict('A', A.__annotations__))
    logger.info(pretty_dict('T2', T2.__annotations__))
    logger.info(pretty_dict('T3', T3.__annotations__))
    assert_equivalent_types(A, T3, set())

    assert_type_roundtrip(A, {})


def test_recursive_fwd():
    def swap(x):
        return x

    T = make_ForwardRef('n')
    recursive_type_subst(T, swap)
