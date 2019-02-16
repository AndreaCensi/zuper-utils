from dataclasses import dataclass
from typing import Callable

from mypy_extensions import NamedArg
from nose.tools import assert_equal

from zuper_json.annotations_tricks import is_Callable, get_Callable_info
from zuper_json.test_utils import with_private_register, assert_type_roundtrip


# @dataclass

#
# def __getitem_inner__(self, params):
#     import collections
#     # noinspection PyUnresolvedReferences
#     from typing import _TypingEmpty, _type_check, _TypingEllipsis
#     if self.__origin__ is tuple and self._special:
#         if params == ():
#             return self.copy_with((_TypingEmpty,))
#         if not isinstance(params, tuple):
#             params = (params,)
#         if len(params) == 2 and params[1] is ...:
#             msg = "Tuple[t, ...]: t must be a type."
#             p = _type_check(params[0], msg)
#             return self.copy_with((p, _TypingEllipsis))
#         msg = "Tuple[t0, t1, ...]: each t must be a type."
#         params = tuple(_type_check(p, msg) for p in params)
#         return self.copy_with(params)
#     if self.__origin__ is collections.abc.Callable and self._special:
#         args, result = params
#         msg = "Callable[args, result]: result must be a type."
#         result = _type_check(result, msg)
#         if args is Ellipsis:
#             return self.copy_with((_TypingEllipsis, result))
#
#         msg = "Callable[[arg, ...], result]: each arg must be a type."
#         args = tuple(_type_check(arg, msg) for arg in args)
#         params = args + (result,)
#         return self.copy_with(params)
#     return _GenericAlias.__getitem__(self, params)
#
# Callable.__getitem_inner__ = __getitem_inner__.__get__(Callable, _VariadicGenericAlias)


# setattr(Callable, '__getitem_inner__', __getitem_inner__.__get__(None, Callable))
# from nose.tools import raises
# import types
# print(type(Callable))
# print(Callable.__getitem_inner__)
# # Callable.__getitem_inner__ = types.MethodType(__getitem_inner__, Callable)
#
# print(Callable.__getitem_inner__)


def test_detection_1():
    T = Callable[[], int]
    print(T.__dict__)
    assert is_Callable(T)

    res = get_Callable_info(T)
    assert_equal(res.parameters_by_name, {})
    assert_equal(res.parameters_by_position, ())
    assert_equal(res.returns, int)


def test_detection_2():
    T = Callable[[NamedArg(str, "A")], int]

    assert is_Callable(T)

    res = get_Callable_info(T)
    assert_equal(res.returns, int)
    assert_equal(res.parameters_by_position, (str,))
    assert_equal(res.parameters_by_name, {"A": str})


def test_detection_3():
    T = Callable[[NamedArg(str, "A")], int]

    assert is_Callable(T)

    res = get_Callable_info(T)
    assert_equal(res.returns, int)
    assert_equal(res.parameters_by_position, (str,))
    assert_equal(res.parameters_by_name, {"A": str})


def test_detection_4():
    @dataclass
    class MyClass:
        pass

    T = Callable[[NamedArg(MyClass, "A")], int]

    assert is_Callable(T)

    res = get_Callable_info(T)
    assert_equal(res.returns, int)
    assert_equal(res.parameters_by_position, (MyClass,))
    assert_equal(res.parameters_by_name, {"A": MyClass})


def test_NamedArg_eq():
    a = NamedArg(int, 'A')
    b = NamedArg(int, 'A')

    assert_equal(a, b)

    A = Callable[[NamedArg(int, 'A')], int]
    B = Callable[[NamedArg(int, 'A')], int]

    assert_equal(A, B)


# @raises(TypeError)
@with_private_register
def test_callable_1():
    T = Callable[[], int]

    assert_type_roundtrip(T, {})


@with_private_register
def test_callable_2():
    T = Callable[[NamedArg(int, "A")], int]

    assert_type_roundtrip(T, {})


@with_private_register
def test_callable_3():
    T = Callable[[int], int]

    assert_type_roundtrip(T, {})
