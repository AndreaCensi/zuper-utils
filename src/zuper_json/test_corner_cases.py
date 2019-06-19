from dataclasses import dataclass
from typing import *

from nose.tools import raises

from zuper_json.annotations_tricks import is_Tuple
from zuper_json.ipce import ipce_from_object, type_to_schema, object_from_ipce
from zuper_json.subcheck import can_be_used_as2


def test_corner_cases01():
    assert None is object_from_ipce(None, {}, {}, expect_type=Optional[int])


def test_corner_cases02():
    assert 2 == object_from_ipce(2, {}, {}, expect_type=Optional[int])


def test_corner_cases03():
    assert None is object_from_ipce(None, {}, {}, expect_type=None)


def test_corner_cases04():
    ipce_from_object({1: 2}, {}, suggest_type=None)


def test_corner_cases05():
    ipce_from_object(12, {}, suggest_type=Optional[int])


def test_corner_cases06():
    assert can_be_used_as2(int, Optional[int], {}).result


@raises(TypeError)
def test_corner_cases07():
    can0 = can_be_used_as2(int, bool, {})
    assert not can0, can0

    T = Union[bool, str]
    can = can_be_used_as2(int, T, {})
    assert not can, can
    object_from_ipce(12, {}, expect_type=T)


@raises(TypeError)
def test_corner_cases08():
    T = Optional[bool]
    assert not can_be_used_as2(int, T, {}).result
    object_from_ipce(12, {}, expect_type=Optional[bool])


@raises(ValueError)
def test_corner_cases09():
    type_to_schema(None, {})


@raises(ValueError)
def test_property_error():
    @dataclass
    class MyClass32:
        a: int

    ok = can_be_used_as2(str, int, {})
    assert not ok.result

    # noinspection PyTypeChecker
    ob = MyClass32('not an int')
    # ipce_to_object(ob, {}, {}, expect_type=MyClass32)
    res = ipce_from_object(ob, {}, {})
    # print(yaml.dump(res))


@raises(NotImplementedError)
def test_not_know():
    class C:
        pass

    ipce_from_object(C(), {}, {})


def test_corner_cases10():
    assert can_be_used_as2(str, str, {})
    assert not can_be_used_as2(str, int, {})


def test_corner_cases11():
    assert can_be_used_as2(Dict, Dict, {})
    assert can_be_used_as2(Dict[str, str], Dict[str, str], {})
    assert can_be_used_as2(Dict[str, str], Dict[str, Any], {})


def test_corner_cases12():
    assert not can_be_used_as2(Dict[str, str], str, {})


def test_corner_cases13():
    assert not can_be_used_as2(str, Dict[str, str], {})


def test_corner_cases14():
    assert not can_be_used_as2(Union[int, str], str, {})


def test_corner_cases15():
    assert can_be_used_as2(str, Union[int, str], {})


def test_corner_cases16():
    assert can_be_used_as2(Union[int], Union[int, str], {})


def test_corner_cases17():
    assert not can_be_used_as2(Union[int, str], Union[str], {})


def test_corner_cases18():
    @dataclass
    class A:
        a: int

    @dataclass
    class B(A):
        pass

    @dataclass
    class C:
        a: int

    assert can_be_used_as2(B, A, {})
    assert can_be_used_as2(C, A, {})


def test_corner_cases18b():
    @dataclass
    class A:
        a: int

    @dataclass
    class C:
        a: str

    assert not can_be_used_as2(A, C, {})


def test_corner_cases18c():
    @dataclass
    class A:
        a: int

    @dataclass
    class C:
        pass

    assert not can_be_used_as2(C, A, {})
    assert can_be_used_as2(A, C, {})


def test_corner_cases19():
    assert not can_be_used_as2(str, int, {})


def test_corner_cases20():
    assert is_Tuple(Tuple[int, int])
    res = can_be_used_as2(Tuple[int, int], Tuple[int, Any], {})
    assert res, res


def test_corner_cases21():
    assert not can_be_used_as2(Tuple[int, int], int, {})


def test_corner_cases22():
    assert not can_be_used_as2(Any, int, {})


def test_corner_cases23():
    @dataclass
    class A:
        a: int

    @dataclass
    class B(A):
        pass

    @dataclass
    class C(A):
        pass

    res = can_be_used_as2(Union[B, C], A, {})
    assert res, res


def test_corner_cases24():
    assert not can_be_used_as2(Tuple[int, int], Tuple[int, str], {})


if __name__ == '__main__':
    test_corner_cases18b()
