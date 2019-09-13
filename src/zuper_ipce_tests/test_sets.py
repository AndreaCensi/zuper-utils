from typing import Any, Set

from zuper_ipce import ipce_from_object, typelike_from_ipce
from zuper_typing import dataclass
from zuper_typing.annotations_tricks import is_Set
from zuper_typing.my_dict import make_set
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_not_implemented_set():
    @dataclass
    class MyClass:
        f: Set[int]

    e = MyClass({1, 2, 3})
    assert_object_roundtrip(e)  # pragma: no cover


def test_is_set01():
    assert not is_Set(set)


def test_is_set02():
    T = Set
    # print(f"the set is {T}")
    assert is_Set(T)


def test_is_set03():
    assert is_Set(Set[int])


def test_rt():
    T = Set[int]
    assert_type_roundtrip(T, expect_type_equal=False)


def test_rt_yes():
    T = make_set(int)
    assert_type_roundtrip(T, expect_type_equal=True)


def test_rt2():
    T = make_set(int)
    assert_type_roundtrip(T)


def test_not_implemented_set_2():
    @dataclass
    class A:
        a: int

    @dataclass
    class MyClass:
        f: Set[A]

    e = MyClass({A(1), A(2)})
    assert_object_roundtrip(e)  # pragma: no cover


def test_set_any():
    @dataclass
    class A:
        v: Any

    v = {"a"}
    a = A(v)

    assert_object_roundtrip(a)


def test_set_any2():
    @dataclass
    class A:
        v: Any

    v = {"a"}
    v = make_set(str)(v)
    a = A(v)

    ipce_v = ipce_from_object(v)
    # print(oyaml_dump(ipce_v))

    schema = ipce_v["$schema"]
    T = typelike_from_ipce(schema)
    # print(T)

    ipce = ipce_from_object(a)
    # print(oyaml_dump(ipce))

    assert_object_roundtrip(a)


def test_set_any3():
    v = {"a"}
    v = make_set(str)(v)

    assert_object_roundtrip(v)


def test_set_any4():
    v = {"a"}

    assert_object_roundtrip(v)
