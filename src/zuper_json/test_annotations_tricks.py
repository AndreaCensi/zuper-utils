import typing
from typing import *

from .annotations_tricks import is_optional, get_optional_type, is_forward_ref, get_forward_ref_arg, is_Any, is_Tuple, \
    is_ClassVar, get_ClassVar_arg, is_Type, get_Type_arg
from .constants import PYTHON_36, PYTHON_37


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
    assert is_optional(a)
    assert get_optional_type(a) is int


class Tree:
    n: Optional['Tree']


symbols = {'Tree': Tree}


def test_forward():
    x = Tree.__annotations__['n']

    assert is_optional(x)

    t = get_optional_type(x)
    # print(t)
    # print(type(t))
    # print(t.__dict__)
    assert is_forward_ref(t)

    # print(f'__forward_arg__: {t.__forward_arg__!r}')
    # print(f'__forward_code__: {t.__forward_code__!r}')
    # print(f'__forward_evaluated__: {t.__forward_evaluated__!r}')
    # print(f'__forward_value__: {t.__forward_value__!r}')
    # print(f'__forward_is_argument__: {t.__forward_is_argument__!r}')

    assert get_forward_ref_arg(t) == 'Tree'

    if PYTHON_36: # pragma: no cover
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
    a = TypeVar('X')
    assert isinstance(a, TypeVar)


def test_ClassVar():
    a = ClassVar[int]
    assert is_ClassVar(a)
    assert get_ClassVar_arg(a) is int


def test_Type():
    X = TypeVar('X')
    a = Type[X]
    assert is_Type(a)
    assert get_Type_arg(a) == X
    # assert get_ClassVar_arg(a) is int
