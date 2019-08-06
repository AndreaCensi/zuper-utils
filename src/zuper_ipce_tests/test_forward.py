from typing import *

import yaml
from nose.tools import assert_equal

from zuper_ipce.ipce import type_to_schema
from zuper_typing import dataclass
from zuper_typing_tests.test_utils import known_failure

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
        b: Optional['C'] = None

    e = C(12, C(1))
    assert_object_roundtrip(e, {})


def test_forward1():
    @dataclass
    class C:
        a: int
        b: Optional['C'] = None

    e = C(12, C(1))
    assert_object_roundtrip(e, {"C": C})


def test_forward2():
    @dataclass
    class C:
        a: int
        b: 'Optional[C]' = None

    # noinspection PyTypeChecker
    e = C(12, C(1))
    assert_object_roundtrip(e, {"C": C})


def test_forward3():
    @dataclass
    class C:
        a: int
        b: 'Optional[C]'

    e = C(12, C(1, None))
    assert_object_roundtrip(e, {"C": C})


def test_forward04():
    @dataclass
    class C:
        a: int
        b: 'Dict[str, C]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)


def test_forward05():
    @dataclass
    class C:
        a: int
        b: 'List[C]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)


def test_forward05b():
    @dataclass
    class C:
        a: int
        b: 'Set[C]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)


def test_forward06():
    @dataclass
    class C:
        a: int
        b: 'Union[C, int]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)


def test_forward07():
    @dataclass
    class C:
        a: int
        b: 'Tuple[C, int]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)


def test_forward08():
    @dataclass
    class C:
        a: int
        b: 'Tuple[C, ...]'

    assert_type_roundtrip(C, {}, expect_type_equal=False)

@known_failure
def test_forward09():
    X = TypeVar('X')

    @dataclass
    class B(Generic[X]):
        b: Optional[X]

    @dataclass
    class A:
        pass

    BA = B[A]
    assert_equal(BA.__doc__, None)

    s = type_to_schema(BA, {})
    print(yaml.dump(s))

    @dataclass
    class C:
        a: int
        b: 'B[C]'

        __depends__ = (B,)

    assert_type_roundtrip(C, {}, expect_type_equal=False)


if __name__ == '__main__':
    test_forward05b()
