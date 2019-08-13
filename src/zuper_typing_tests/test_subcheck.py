from typing import (Any, Callable, ClassVar, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Type, TypeVar, Union,
                    )

from nose.tools import assert_equal

from zuper_typing import dataclass,Generic
from zuper_typing.annotations_tricks import (get_Callable_info, is_Any, is_Callable, is_Iterator, is_Sequence, is_Tuple,
                                             name_for_type_like)
from zuper_typing.my_dict import make_list, make_set
from zuper_typing.recursive_tricks import replace_typevars
from zuper_typing.subcheck import can_be_used_as2


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


def test_corner_cases30():
    assert not can_be_used_as2(Sequence, List[int], {})


def test_corner_cases31():
    assert not can_be_used_as2(List[str], List[int], {})


def test_corner_cases32():
    assert can_be_used_as2(List[str], List, {})


def test_corner_cases33():
    class A:
        pass

    class B:
        pass

    assert not can_be_used_as2(A, B, {})


def test_corner_cases36():
    A = Set[str]
    B = Set[Any]

    assert can_be_used_as2(A, B, {})

    assert not can_be_used_as2(B, A, {})


def test_corner_cases34():
    assert not can_be_used_as2(Dict[str, str], Dict[int, str], {})


def test_corner_cases35():
    assert not can_be_used_as2(Dict[str, str], Dict[int, str], {})


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
    L2 = TypeVar('L2')
    res = can_be_used_as2(L1, L2, {})
    print(res)

    assert res, res


def test_match_TypeVar0b():
    L1 = str
    L2 = TypeVar('L2')
    res = can_be_used_as2(L1, L2, {})
    print(res)
    assert res.matches['L2'] is L1, res

    assert res, res


def test_match_MySet1():
    C1 = Set[str]
    C2 = make_set(str)
    res = can_be_used_as2(C1, C2, {})
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

    # noinspection PyTypeHints
    X2 = TypeVar('X')  # note: needs this to make the test work
    S = {X2: str, Y: int}
    tries = (
          (X, {X2: str}, str),
          (Any, {}, Any),
          (List[X], {X2: str}, List[str]),
          (Tuple[X], {X2: str}, Tuple[str]),
          (Callable[[X], Y], {X2: str, Y: int}, Callable[[str], int]),
          (Optional[X], {X2: str}, Optional[str]),
          (Union[X, Y], {X2: str, Y: int}, Union[str, int]),
          (ClassVar[X], {X2: str}, ClassVar[str]),
          (Dict[X, Y], {X2: str, Y: int}, Dict[str, int]),
          (Sequence[X], {X2: str}, Sequence[str]),
          (Iterator[X], {X2: str}, Iterator[str]),
          (Set[X], S, Set[str]),
          (Type[X], {X2: str}, Type[str]),
          (Type[int], {X2: str}, Type[int]),
          (ClassVar[List[X]], {X2: str}, ClassVar[List[str]]),
          (ClassVar[int], {X2: str}, ClassVar[int]),
          (Iterator, S, Iterator[Any]),
          (List, S, List[Any]),
          (make_list(bool), S, make_list(bool)),
          (make_list(X), S, make_list(str)),
          (Sequence, S, Sequence[Any]),

          )
    for orig, subst, result in tries:
        yield try_, orig, subst, result


def try_(orig, subst, result):
    obtained = replace_typevars(orig, bindings=subst, symbols={})
    print(f'obtained {type(obtained)} {obtained!r}')
    assert_equal(name_for_type_like(obtained), name_for_type_like(result))


def test_dataclass2():
    @dataclass
    class A:
        data: int
        parent: 'A'

    assert A.__annotations__['parent'] is A
    X = TypeVar('X')
    bindings = {X: int}
    A2 = replace_typevars(A, bindings=bindings, symbols={})


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


def test_Sequence1():
    assert is_Sequence(Sequence[int])


def test_Sequence2():
    assert is_Sequence(Sequence)


def test_Iterator1():
    assert is_Iterator(Iterator[int])


def test_Iterator2():
    assert is_Iterator(Iterator)
