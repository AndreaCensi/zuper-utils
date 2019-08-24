from nose.tools import raises

from zuper_typing import dataclass
from zuper_typing.subcheck import can_be_used_as2


def test_nominal_no_nominal():
    @dataclass
    class A:
        a: int

    @dataclass
    class C:
        nominal = True

    @dataclass
    class D:
        pass

    assert not can_be_used_as2(A, C)
    assert can_be_used_as2(A, D)


@raises(TypeError)
def test_nominal_inherit():
    """ this is a limitation of the spec """

    @dataclass
    class A:
        a: int

        nominal = True

    @dataclass
    class B(A):
        b: int
