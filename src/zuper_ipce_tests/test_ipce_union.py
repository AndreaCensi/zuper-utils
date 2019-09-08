from typing import Dict, Optional, Set, Tuple, Union

from nose.tools import raises

from zuper_ipce import object_from_ipce
from zuper_typing import dataclass
from zuper_typing.annotations_tricks import make_Tuple
from zuper_typing.my_dict import make_dict, make_list, make_set
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


# noinspection PyUnresolvedReferences


def test_union_1():
    @dataclass
    class MyClass:
        f: Union[int, str]

    e = MyClass(1)
    assert_object_roundtrip(e)  # raise here
    e = MyClass("a")  # pragma: no cover
    assert_object_roundtrip(e)  # pragma: no cover


def test_union_2():
    T = Union[int, str]
    assert_type_roundtrip(T)


def test_union_2b():
    T = Union[Tuple[str], int]
    assert_type_roundtrip(T)


def test_union_2c():
    T = Tuple[int, ...]
    assert_type_roundtrip(T)


def test_tuple_empty():
    T = make_Tuple()
    assert_type_roundtrip(T)


def test_union_3():
    @dataclass
    class A:
        a: int

    @dataclass
    class B:
        b: int

    @dataclass
    class C:
        c: Union[A, B]

    ec1 = C(A(1))
    ec2 = C(B(1))

    assert_type_roundtrip(C)
    assert_object_roundtrip(ec1)
    assert_object_roundtrip(ec2)


@raises(ValueError)
def test_none1():
    @dataclass
    class A:
        b: int

    object_from_ipce(None, expect_type=A)


def test_tuple_wiht_optional_inside():
    T = Tuple[int, Optional[int], str]
    assert_type_roundtrip(T)


def test_dict_with_optional():
    # T = Dict[str, Optional[int]]
    T = make_dict(str, Optional[int])
    assert_type_roundtrip(T)


def test_list_with_optional():
    T = make_list(Optional[int])
    assert_type_roundtrip(T)


def test_set_with_optional():
    # even though it does not make sense ...
    T = make_set(Optional[int])
    assert_type_roundtrip(T)


def test_set_with_optional2():
    # even though it does not make sense ...
    T = Set[Optional[int]]
    assert_type_roundtrip(T)


def test_dict_with_optional_key():
    T = Dict[Optional[int], int]
    assert_type_roundtrip(T)
