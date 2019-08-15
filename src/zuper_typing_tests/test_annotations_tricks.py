import typing
from typing import Any, ClassVar, NewType, Optional, Tuple, Type, TypeVar, Union

from nose.tools import assert_equal

from zuper_typing.annotations_tricks import (
    get_ClassVar_arg,
    get_Dict_args,
    get_ForwardRef_arg,
    get_NewType_arg,
    get_Optional_arg,
    get_Type_arg,
    is_Any,
    is_ClassVar,
    is_Dict,
    is_ForwardRef,
    is_NewType,
    is_Optional,
    is_Tuple,
    is_Type,
    name_for_type_like,
)
from zuper_typing.constants import PYTHON_36, PYTHON_37
from zuper_typing.monkey_patching_typing import original_dict_getitem
from zuper_typing.my_dict import is_CustomDict, make_dict


def test_union():
    a = Union[int, str]
    # print(a)
    # print(type(a))
    if PYTHON_37:
        assert isinstance(a, typing._GenericAlias)
        # print(a.__dict__)
        assert a.__origin__ == Union


def test_optional():
    a = Optional[int]
    assert is_Optional(a)
    assert get_Optional_arg(a) is int


class Tree:
    n: Optional["Tree"]


symbols = {"Tree": Tree}


def test_forward():
    x = Tree.__annotations__["n"]

    assert is_Optional(x)

    t = get_Optional_arg(x)
    # print(t)
    # print(type(t))
    # print(t.__dict__)
    assert is_ForwardRef(t)

    # print(f'__forward_arg__: {t.__forward_arg__!r}')
    # print(f'__forward_code__: {t.__forward_code__!r}')
    # print(f'__forward_evaluated__: {t.__forward_evaluated__!r}')
    # print(f'__forward_value__: {t.__forward_value__!r}')
    # print(f'__forward_is_argument__: {t.__forward_is_argument__!r}')

    assert get_ForwardRef_arg(t) == "Tree"

    if PYTHON_36:  # pragma: no cover
        t._eval_type(localns=locals(), globalns=globals())
    else:
        t._evaluate(localns=locals(), globalns=globals())
    # print(f'__forward_arg__: {t.__forward_arg__!r}')
    # print(f'__forward_code__: {t.__forward_code__!r}')
    # print(f'__forward_evaluated__: {t.__forward_evaluated__!r}')
    # print(f'__forward_value__: {t.__forward_value__!r}')
    # print(f'__forward_is_argument__: {t.__forward_is_argument__!r}')


def test_any():
    a = Any
    assert is_Any(a)


def test_Tuple1():
    a = Tuple[int, str]
    assert is_Tuple(a)


def test_Tuple2():
    a = Tuple[int, ...]
    assert is_Tuple(a)


def test_Typevar():
    a = TypeVar("a")
    assert isinstance(a, TypeVar)


def test_ClassVar():
    a = ClassVar[int]
    assert is_ClassVar(a)
    assert get_ClassVar_arg(a) is int


def test_Type():
    X = TypeVar("X")
    a = Type[X]
    assert is_Type(a)
    assert get_Type_arg(a) == X
    # assert get_ClassVar_arg(a) is int


def test_NewType():
    C = NewType("C", str)

    assert is_NewType(C)
    assert get_NewType_arg(C) is str
    # assert get_ClassVar_arg(a) is int


def test_DictName():
    D = original_dict_getitem((int, str))
    # print(D.__dict__)
    assert is_Dict(D)
    # assert get_Dict_name(D) == 'Dict[int,str]'


def test_Dict1():
    K, V = get_Dict_args(typing.Dict)
    assert_equal(K, Any)
    assert_equal(V, Any)


def test_Dict2():
    X = typing.Dict[str, int]
    print(type(X))
    print(f"{X!r}")
    assert is_Dict(X)
    K, V = get_Dict_args(X)
    assert_equal(K, str)
    assert_equal(V, int)
    print(K, V)
    N = name_for_type_like(X)
    assert_equal(N, "Dict[str,int]")


def test_Dict3():
    D = make_dict(str, int)
    assert is_CustomDict(D)
    N = name_for_type_like(D)
    assert_equal(N, "Dict[str,int]")


def test_corner_Type():
    T = Type
    get_Type_arg(T)
