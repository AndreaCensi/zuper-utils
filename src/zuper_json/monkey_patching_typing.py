from .constants import PYTHON_36
import dataclasses
import typing
from typing import TypeVar, Generic, Dict

from .my_dict import make_dict

from .zeneric2 import ZenericFix

if PYTHON_36:  # pragma: no cover
    from typing import GenericMeta

    previous_getitem = GenericMeta.__getitem__
else:
    from typing import _GenericAlias

    previous_getitem = _GenericAlias.__getitem__


class Alias1:

    def __getitem__(self, params):

        if self is typing.Dict:
            K, V = params
            if K is not str:
                return make_dict(K, V)

        # noinspection PyArgumentList
        return previous_getitem(self, params)


if PYTHON_36:  # pragma: no cover
    from typing import GenericMeta

    old_one = GenericMeta.__getitem__


    class P36Generic:
        def __getitem__(self, params):
            # pprint('P36', params=params, self=self)
            if self is typing.Generic:
                return ZenericFix.__class_getitem__(params)

            if self is typing.Dict:
                K, V = params
                if K is not str:
                    return make_dict(K, V)

            # noinspection PyArgumentList
            return old_one(self, params)


    GenericMeta.__getitem__ = P36Generic.__getitem__

else:
    Generic.__class_getitem__ = ZenericFix.__class_getitem__
    _GenericAlias.__getitem__ = Alias1.__getitem__

Dict.__getitem__ = Alias1.__getitem__


def _cmp_fn_loose(name, op, self_tuple, other_tuple):
    body = ['if other.__class__.__name__ == self.__class__.__name__:',
            f' return {self_tuple}{op}{other_tuple}',
            'return NotImplemented']
    fn = dataclasses._create_fn(name, ('self', 'other'), body)
    fn.__doc__ = """
    This is a loose comparison function.
    Instead of comparing:

        self.__class__ is other.__class__

    we compare:

        self.__class__.__name__ == other.__class__.__name__

    """
    return fn


dataclasses._cmp_fn = _cmp_fn_loose


def typevar__repr__(self):
    if self.__covariant__:
        prefix = '+'
    elif self.__contravariant__:
        prefix = '-'
    else:
        prefix = '~'
    s = prefix + self.__name__

    if self.__bound__:
        if isinstance(self.__bound__, type):
            b = self.__bound__.__name__
        else:
            b = str(self.__bound__)
        s += f'<{b}'
    return s


setattr(TypeVar, '__repr__', typevar__repr__)

NAME_ARG = '__name_arg__'


# need to have this otherwise it's not possible to say that two types are the same
class Reg:
    already = {}


def MyNamedArg(x: type, name):
    key = f'{x} {name}'
    if key in Reg.already:
        return Reg.already[key]
    meta = getattr(x, '__metaclass_', type)

    d = {NAME_ARG: name, 'original': x}
    cname = x.__name__

    res = meta(cname, (x,), d)

    res.__module__ = 'typing'

    Reg.already[key] = res
    return res


import mypy_extensions

setattr(mypy_extensions, 'NamedArg', MyNamedArg)

from dataclasses import dataclass as original_dataclass


class RegisteredClasses:
    # klasses: Dict[str, type] = {}
    klasses = {}


def remember_created_class(res):
    # print(f'Registered class "{res.__name__}"')
    k = (res.__module__, res.__name__)
    RegisteredClasses.klasses[k] = res


def my_dataclass(_cls=None, *, init=True, repr=True, eq=True, order=False,
                 unsafe_hash=False, frozen=False):
    # pprint('my_dataclass', _cls=_cls)
    res = original_dataclass(_cls, init=init, repr=repr, eq=eq, order=order,
                             unsafe_hash=unsafe_hash, frozen=frozen)
    remember_created_class(res)

    # res.__doc__  = res.__doc__.replace(' ', '')
    return res


setattr(dataclasses, 'dataclass', my_dataclass)
