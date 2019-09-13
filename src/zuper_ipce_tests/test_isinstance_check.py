from typing import cast, TypeVar

from zuper_ipce import IEDO, ipce_from_object, object_from_ipce
from zuper_typing import dataclass, Generic
from zuper_typing.exceptions import ZAssertionError
from zuper_typing.logging_util import ztinfo
from zuper_typing.zeneric2 import StructuralTyping


def test1():
    @dataclass
    class C1(metaclass=StructuralTyping):
        a: int
        b: float

    @dataclass
    class C2(metaclass=StructuralTyping):
        a: int
        b: float
        c: str

    c1 = C1(1, 2)
    c2 = C2(1, 2, "a")

    assert_isinstance(c1, C1)
    assert_isinstance(c2, C2)
    assert_isinstance(c2, C1)

    assert_issubclass(C2, C1)


def test2():
    @dataclass
    class C4:
        a: int
        b: float

    c1 = C4(1, 2.0)

    C4_ = object_from_ipce(ipce_from_object(C4))
    c1_ = object_from_ipce(ipce_from_object(c1))

    assert_isinstance(c1, C4)
    # noinspection PyTypeChecker
    assert_isinstance(c1_, C4_), (c1_, C4_)
    # noinspection PyTypeChecker
    assert_isinstance(c1, C4_), (c1, C4_)
    assert_isinstance(c1_, C4)


def test3():
    X = TypeVar("X")

    @dataclass
    class CB(Generic[X]):
        a: X

    C5 = CB[int]

    c1 = C5(1)

    iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)
    C5_ipce = ipce_from_object(C5)
    C5_ = cast(type, object_from_ipce(C5_ipce, iedo=iedo))
    ztinfo("test3", C5=C5, C5_=C5_)
    c1_ipce = ipce_from_object(c1)
    c1_ = object_from_ipce(c1_ipce, iedo=iedo)

    # different class
    assert C5 is not C5_
    # however isinstance should always work
    # noinspection PyTypeHints
    assert_isinstance(c1, C5)
    assert_isinstance(c1_, C5_)
    assert_isinstance(c1, C5_)

    # noinspection PyTypeHints
    assert_isinstance(c1_, C5)

    assert_issubclass(C5, C5_)
    assert_issubclass(C5, CB)

    # logger.info(f"CB {id(CB)}")
    # logger.info(type(CB))
    # logger.info(CB.mro())
    # logger.info(f"C5_ {id(C5_)}")
    # logger.info(type(C5_))
    # logger.info(C5_.mro())
    assert_issubclass(C5_, CB)


def assert_isinstance(a, C):
    if not isinstance(a, C):
        raise ZAssertionError(
            "not isinstance",
            a=a,
            type_a=type(a),
            type_type_a=type(type(a)),
            C=C,
            type_C=type(C),
        )


def assert_issubclass(A, C):
    if not issubclass(A, C):
        raise ZAssertionError(
            "not issubclass", A=A, C=C, type_A=type(A), type_C=type(C)
        )
