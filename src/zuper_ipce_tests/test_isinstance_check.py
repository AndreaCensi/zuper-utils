from typing import TypeVar, cast

from zuper_ipce import logger
from zuper_ipce.conv_ipce_from_object import ipce_from_object
from zuper_ipce.conv_object_from_ipce import object_from_ipce
from zuper_typing import dataclass, Generic
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

    assert isinstance(c1, C1)
    assert isinstance(c2, C2)
    assert isinstance(c2, C1)

    assert issubclass(C2, C1)


def test2():
    @dataclass
    class C4:
        a: int
        b: float

    c1 = C4(1, 2.0)

    C4_ = object_from_ipce(ipce_from_object(C4))
    c1_ = object_from_ipce(ipce_from_object(c1))

    assert isinstance(c1, C4)
    # noinspection PyTypeChecker
    assert isinstance(c1_, C4_)
    # noinspection PyTypeChecker
    assert isinstance(c1, C4_)
    assert isinstance(c1_, C4)


def test3():
    X = TypeVar("X")

    @dataclass
    class CB(Generic[X]):
        a: X

    C5 = CB[int]

    c1 = C5(1)

    C5_ = cast(type, object_from_ipce(ipce_from_object(C5)))
    c1_ = object_from_ipce(ipce_from_object(c1))

    # different class
    assert C5 is not C5_
    # however isinstance should always work
    # noinspection PyTypeHints
    assert isinstance(c1, C5)
    assert isinstance(c1_, C5_)
    assert isinstance(c1, C5_)

    # noinspection PyTypeHints
    assert isinstance(c1_, C5)

    assert issubclass(C5, C5_)
    assert issubclass(C5, CB)

    logger.info(f"CB {id(CB)}")
    logger.info(type(CB))
    logger.info(CB.mro())
    logger.info(f"C5_ {id(C5_)}")
    logger.info(type(C5_))
    logger.info(C5_.mro())
    assert issubclass(C5_, CB)
