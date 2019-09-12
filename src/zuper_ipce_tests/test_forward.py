from typing import Dict, List, Optional, Set, Tuple, TypeVar, Union

from nose.tools import assert_equal

from zuper_ipce import ipce_from_typelike, typelike_from_ipce
from zuper_typing import dataclass, Generic
from zuper_typing.zeneric2 import resolve_types
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_forward1_ok_no_locals_if_using_name():
    # """
    # *USED TO* Fail because there is no "C" in the context
    # if we don't evaluate locals().
    # l
    # """

    @dataclass
    class C:
        a: int
        b: Optional["C"] = None

    e = C(12, C(1))
    assert_object_roundtrip(e)


def test_forward1():
    @dataclass
    class C:
        a: int
        b: Optional["C"] = None

    e = C(12, C(1))
    assert_object_roundtrip(e, use_globals={"C": C})


def test_forward2():
    @dataclass
    class C:
        a: int
        b: "Optional[C]" = None

    # noinspection PyTypeChecker
    e = C(12, C(1))
    assert_object_roundtrip(e, use_globals={"C": C})


def test_forward3():
    @dataclass
    class C:
        a: int
        b: "Optional[C]"

    e = C(12, C(1, None))
    assert_object_roundtrip(e, use_globals={"C": C})


def test_forward04():
    @dataclass
    class C:
        a: int
        b: "Dict[str, C]"

    assert_type_roundtrip(C, expect_type_equal=False)


def test_forward05():
    @dataclass
    class C:
        a: int
        b: "List[C]"

    assert_type_roundtrip(C, expect_type_equal=False)


def test_forward05b():
    @dataclass
    class C:
        a: int
        b: "Set[C]"

    assert_type_roundtrip(C, expect_type_equal=False)


def test_forward06():
    @dataclass
    class C:
        a: int
        b: "Union[C, int]"

    assert_type_roundtrip(C, expect_type_equal=False)


def test_forward07():
    @dataclass
    class C:
        a: int
        b: "Tuple[C, int]"

    assert_type_roundtrip(C, expect_type_equal=False)


def test_forward08():
    @dataclass
    class C:
        a: int
        b: "Tuple[C, ...]"

    assert_type_roundtrip(C, expect_type_equal=False)


# if  USE_REMEMBERED_CLASSES:
#     f = lambda x: x
# else:
#     f = known_failure
#
#
# @f


def test_forward09():
    X = TypeVar("X")

    @dataclass
    class B(Generic[X]):
        # b: Optional[X]
        b: X

    @dataclass
    class A:
        pass

    BA = B[A]
    assert_equal(BA.__doc__, None)

    s = ipce_from_typelike(BA)
    # print(oyaml_dump(s))

    @dataclass
    class C:
        a: int
        b: "B[C]"

        __depends__ = (B,)

    resolve_types(C, refs=(B,))
    # print("\n\n\n\n")
    Cb = C.__annotations__["b"]
    # print("Cb: " + Cb.__qualname__)
    assert "forward09" in C.__qualname__
    assert "forward09" in C.__annotations__["b"].__qualname__

    ipce_Cb = ipce_from_typelike(Cb)
    # logger.info("ipce_CB: \n" + oyaml_dump(ipce_Cb))
    assert ipce_Cb["__qualname__"] == "test_forward09.<locals>.B[C]"
    assert ipce_Cb["properties"]["b"]["__qualname__"] == "test_forward09.<locals>.C"

    Cb2 = typelike_from_ipce(ipce_Cb)
    Cb2_C = Cb2.__annotations__["b"]
    # print(Cb2_C)
    assert_equal(Cb2_C.__qualname__, "test_forward09.<locals>.C")

    # assert_type_roundtrip(Cb, {}, expect_type_equal=False)
    # assert_type_roundtrip(C, {}, expect_type_equal=False)
    assert_type_roundtrip(B)
    assert_type_roundtrip(BA)


if __name__ == "__main__":
    test_forward05b()
