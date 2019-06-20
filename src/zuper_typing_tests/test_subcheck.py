from dataclasses import dataclass
from typing import *

from nose.tools import assert_equal

from zuper_typing.annotations_tricks import is_Tuple, is_Any, name_for_type_like, is_Callable, get_Callable_info
from zuper_typing.subcheck import can_be_used_as2
from zuper_typing.zeneric2 import replace_typevars


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


def test_corner_cases06():
    assert can_be_used_as2(int, Optional[int], {}).result


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


def test_corner_cases25():
    D1 = Dict[str, Any]
    D2 = Dict[str, int]
    res = can_be_used_as2(D2, D1, {})
    assert res, res


def test_corner_cases26():
    D1 = Dict[str, Any]
    D2 = Dict[str, int]
    res = can_be_used_as2(D1, D2, {})
    assert not res, res


def test_match_List1():
    L1 = List[str]
    X = TypeVar('X')
    L2 = List[X]
    res = can_be_used_as2(L1, L2, {})
    print(L1, L2, res)
    assert res, res
    assert res.matches['X'] is str, res


def test_match_List2():
    L1 = List[Any]
    X = TypeVar('X')
    L2 = List[X]
    res = can_be_used_as2(L1, L2, {})
    assert res, res
    assert is_Any(res.matches['X']), res


def test_match_List3():
    """ We want that match(X, Any) does not match X at all. """
    L1 = List[Any]
    X = TypeVar('X')
    L2 = List[X]
    res = can_be_used_as2(L2, L1, {})
    assert res, res

    assert not 'X' in res.matches, res
    # assert is_Any(res.matches['X']), res


def test_match_TypeVar0():
    L1 = Tuple[str]
    L2 = TypeVar('X')
    res = can_be_used_as2(L1, L2, {})
    print(res)

    assert res, res


def test_match_TypeVar0b():
    L1 = str
    L2 = TypeVar('X')
    res = can_be_used_as2(L1, L2, {})
    print(res)
    assert res.matches['X'] is L1, res

    assert res, res


def test_match_Tuple0():
    L1 = Tuple[str]
    X = TypeVar('X')

    L2 = Tuple[X]
    res = can_be_used_as2(L1, L2, {})
    print(res)
    assert res.matches['X'] is str, res
    assert res, res


def test_match_Tuple1():
    L1 = Tuple[str, int]
    X = TypeVar('X')
    Y = TypeVar('Y')
    L2 = Tuple[X, Y]
    res = can_be_used_as2(L1, L2, {})
    print(res)
    assert res.matches['X'] is str, res
    assert res.matches['Y'] is int, res
    assert res, res


def test_replace_typevars():
    X = TypeVar('X')
    Y = TypeVar('Y')

    X2 = TypeVar('X')

    tries = (
        (X, {X2: str},str),
        (List[X], {X2: str}, List[str]),
        (Tuple[X], {X2: str}, Tuple[str]),
        (Callable[[X], Y], {X2: str, Y: int}, Callable[[str], int]),
        (Optional[X], {X2: str}, Optional[str]),
        (Union[X], {X2: str}, Union[str]),
        (ClassVar[X], {X2: str}, ClassVar[str]),
        (Dict[X, Y], {X2: str, Y: int}, Dict[str, int]),

    )
    for orig, subst, result in tries:
        yield try_, orig, subst, result


def try_(orig, subst, result):
    obtained = replace_typevars(orig, bindings=subst, symbols={}, rl=None)
    print(f'obtained {type(obtained)} {obtained!r}')
    assert_equal(name_for_type_like(obtained), name_for_type_like(result))


def test_callable1():
    T = Callable[[int], str]
    assert is_Callable(T)
    cinfo = get_Callable_info(T)
    print(cinfo)

    assert cinfo.parameters_by_name == {'__0': int}
    assert cinfo.parameters_by_position == (int,)

    assert cinfo.returns is str


def test_callable2():
    X = TypeVar('X')
    Y = TypeVar('Y')
    T = Callable[[X], Y]
    assert is_Callable(T)
    cinfo = get_Callable_info(T)
    print(cinfo)

    assert cinfo.parameters_by_name == {'__0': X}
    assert cinfo.parameters_by_position == (X,)

    assert cinfo.returns == Y

    subs = {X: str, Y: int}

    def f(x):
        return subs.get(x, x)

    cinfo2 = cinfo.replace(f)
    assert cinfo2.parameters_by_name == {'__0': str}, cinfo2
    assert cinfo2.parameters_by_position == (str,), cinfo2

    assert cinfo2.returns == int, cinfo2
