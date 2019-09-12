from dataclasses import dataclass
from typing import Optional, Union

from zuper_typing.subcheck import can_be_used_as2
from zuper_typing.zeneric2 import resolve_types


def test_recursive1():
    @dataclass
    class T1:
        data: int
        branch: "Optional[T1]"

    resolve_types(T1)

    @dataclass
    class T2:
        data: int
        branch: "Optional[T2]"

    resolve_types(T2)

    # print(T1.__annotations__)
    # print(T2.__annotations__)
    #
    # print(T1)
    # print(T2)
    c = can_be_used_as2(T1, T2)
    # print(c)

    assert c.result, c.why


def test_recursive2():
    @dataclass
    class T1:
        data: int
        branch: "Union[T1, int]"

    resolve_types(T1)

    @dataclass
    class T2:
        data: int
        branch: "T2"

    resolve_types(T2)

    # print(T1)
    # print(T2)
    c = can_be_used_as2(T2, T1)
    # print(c)

    assert c.result, c.why
