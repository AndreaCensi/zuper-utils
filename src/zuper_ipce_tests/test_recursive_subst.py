from typing import ClassVar, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from nose.tools import raises

from zuper_commons.text import pretty_dict
from zuper_ipce import logger
from zuper_ipce.assorted_recursive_type_subst import recursive_type_subst
from zuper_ipce.constants import JSONSchema
from zuper_ipce.schema_caching import assert_canonical_schema
from zuper_ipce_tests.test_utils import NotEquivalent, assert_equivalent_types, assert_type_roundtrip, make_ForwardRef
from zuper_typing import dataclass
from zuper_typing.annotations_tricks import get_ClassVar_arg, is_ClassVar, is_Dict, is_Type
from zuper_typing.monkey_patching_typing import original_dict_getitem
from zuper_typing.my_dict import make_dict, make_list, make_set


def test_rec1():
    X = TypeVar('X')

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
        h2: make_list(bool)
        i: Optional[int]
        l: Tuple[int, ...]
        m: original_dict_getitem((int, float))
        n: original_dict_getitem((bool, float))

        q: ClassVar[int]
        r: ClassVar[bool]

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
    def identity(x):
        return x

    T = make_ForwardRef('n')
    recursive_type_subst(T, identity)


def test_recursive_fwd2():
    def identity(x):
        return x

    T = original_dict_getitem((str, str))
    assert is_Dict(T)
    recursive_type_subst(T, identity)


def test_Type_1():
    def identity(x):
        return x

    T = Type
    assert is_Type(T)
    recursive_type_subst(T, identity)


def test_Type_2():
    def identity(x):
        return x

    T = Type[int]
    assert is_Type(T)
    recursive_type_subst(T, identity)


@raises(ValueError)
def test_schema1():
    schema = cast(JSONSchema, {})
    assert_canonical_schema(schema)


def test_classvar():
    def swap(x):
        if x is int:
            return str
        if x is str:
            return int
        return x

    T = ClassVar[int]
    assert is_ClassVar(T)
    assert get_ClassVar_arg(T) is int, T
    T2 = recursive_type_subst(T, swap)
    print(T)
    print(T2)

    assert get_ClassVar_arg(T2) is str, T2

    try:
        assert_equivalent_types(T, T2, set())
    except NotEquivalent:
        pass
    else:
        raise Exception()

    U = ClassVar[bool]
    assert is_ClassVar(U)
    assert get_ClassVar_arg(U) is bool, U
    U2 = recursive_type_subst(U, swap)
    print(U)
    print(U2)

    assert get_ClassVar_arg(U2) is bool, U
