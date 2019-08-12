from typing import Dict, ForwardRef, List, Optional, Set, Tuple, Union

from zuper_commons.text import pretty_dict
from zuper_ipce.assorted_recursive_type_subst import recursive_type_subst
from zuper_ipce_tests.test_utils import assert_equivalent_types
from zuper_typing import dataclass
from zuper_typing.my_dict import make_dict, make_list, make_set
from zuper_ipce import logger

def test_rec1():
    @dataclass
    class A:
        a: Dict[int, bool]
        b: Union[int, bool]
        c: Set[int]
        d: List[int]
        e: Tuple[int, bool]
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
