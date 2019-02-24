from dataclasses import dataclass
from typing import *

try:
    # noinspection PyUnresolvedReferences
    from typing import ForwardRef
except ImportError:
    # noinspection PyUnresolvedReferences
    from typing import _ForwardRef as ForwardRef

from .test_utils import assert_object_roundtrip, with_private_register


@with_private_register
def test_forward1_ok_no_locals_if_using_name():
    # """
    # *USED TO* Fail because there is no "C" in the context
    # if we don't evaluate locals().
    # l
    # """

    @dataclass
    class C:
        a: int
        b: Optional['C'] = None

    e = C(12, C(1))
    assert_object_roundtrip(e, {})


@with_private_register
def test_forward1():
    @dataclass
    class C:
        a: int
        b: Optional['C'] = None

    e = C(12, C(1))
    assert_object_roundtrip(e, {"C": C})


@with_private_register
def test_forward2():
    @dataclass
    class C:
        a: int
        b: 'Optional[C]' = None

    e = C(12, C(1))
    assert_object_roundtrip(e, {"C": C})



@with_private_register
def test_forward3():
    @dataclass
    class C:
        a: int
        b: 'Optional[C]'

    e = C(12, C(1, None))
    assert_object_roundtrip(e, {"C": C})
