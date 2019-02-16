from dataclasses import dataclass
from decimal import Decimal
from typing import *
# noinspection PyUnresolvedReferences
from typing import NewType, Tuple, List

from zuper_json.test_utils import relies_on_missing_features, assert_type_roundtrip
from .test_utils import assert_object_roundtrip, with_private_register


@relies_on_missing_features
@with_private_register
def test_not_implemented_set():
    @dataclass
    class MyClass:
        f: Set[int]

    e = MyClass(set([1, 2, 3]))
    assert_object_roundtrip(e, {})  # pragma: no cover


@relies_on_missing_features
@with_private_register
def test_not_implemented_set_2():
    @dataclass
    class A:
        a: int

    @dataclass
    class MyClass:
        f: Set[A]

    e = MyClass({A(1), A(2)})
    assert_object_roundtrip(e, {})  # pragma: no cover


#
# @with_private_register
# def test_not_implemented_dict_complex1():
#     @dataclass
#     class MyClass:
#         f: Dict[int, int]
#
#     e = MyClass({1: 2})
#     assert_object_roundtrip(e, {})


@relies_on_missing_features
@with_private_register
def test_not_implemented_list_1():
    @dataclass
    class MyClass:
        f: List[int]

    e = MyClass([1, 2, 3])
    assert_object_roundtrip(e, {})


# @relies_on_missing_features
@with_private_register
def test_not_implemented_float_1():
    @dataclass
    class MyClass:
        f: float

    e = MyClass(1.0)
    assert_object_roundtrip(e, {})


@relies_on_missing_features
@with_private_register
def test_not_implemented_decimal_1():
    @dataclass
    class MyClass:
        f: Decimal

    e = MyClass(Decimal(1.0))
    assert_object_roundtrip(e, {})  # raise here
    e = MyClass(Decimal('0.3'))  # pragma: no cover
    assert_object_roundtrip(e, {})  # pragma: no cover


symbols = {}


@relies_on_missing_features
def test_type1():
    T = Type
    assert_type_roundtrip(T, symbols)


def test_type2():
    T = type
    assert_type_roundtrip(T, symbols)


@relies_on_missing_features
def test_newtype():
    T = NewType('T', str)
    assert_type_roundtrip(T, symbols)

def test_tuples1():
    T = Tuple[str, int]
    assert_type_roundtrip(T, symbols)

def test_tuples2():
    T = Tuple[str, ...]
    assert_type_roundtrip(T, symbols)


@relies_on_missing_features
def test_list1():
    T = List[str]
    assert_type_roundtrip(T, symbols)
