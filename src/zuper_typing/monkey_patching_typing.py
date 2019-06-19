import dataclasses
import typing
from datetime import datetime
from typing import TypeVar, Generic, Dict

import termcolor

from .constants import PYTHON_36, ANNOTATIONS_ATT, DEPENDS_ATT
from .my_dict import make_dict
from .zeneric2 import ZenericFix, resolve_types

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

if PYTHON_36:
    original_dict_getitem = lambda a: Dict[a[0], a[1]]
else:
    original_dict_getitem = Dict.__getitem__

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
    def wrap(cls):
        # logger.info(f'called my_dataclass for {cls} with bases {_cls.__bases__}')
        # if cls.__name__ == 'B' and len(cls.__bases__) == 1 and cls.__bases__[0].__name__ == 'object' and len(cls.__annotations__) != 2:
        #     assert False, (cls, cls.__bases__, cls.__annotations__)
        res = my_dataclass_(cls, init=init, repr=repr,
                            eq=eq, order=order,
                            unsafe_hash=unsafe_hash, frozen=frozen)
        # logger.info(f'called my_dataclass for {cls} with bases {_cls.__bases__}, '
        #             f'returning {res} with bases {res.__bases__} and annotations {_cls.__annotations__}')
        return res

    # See if we're being called as @dataclass or @dataclass().
    if _cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(_cls)


def get_all_annotations(cls: type) -> Dict[str, type]:
    ''' Gets all the annotations including the parents. '''
    res = {}
    for base in cls.__bases__:
        annotations = getattr(base, ANNOTATIONS_ATT, {})
        res.update(annotations)

    # logger.info(f'name {cls.__name__} bases {cls.__bases__} mro {cls.mro()} res {res}')
    return res


def my_dataclass_(_cls, *, init=True, repr=True, eq=True, order=False,
                  unsafe_hash=False, frozen=False):
    original_doc = getattr(_cls, '__doc__', None)

    unsafe_hash = True

    # if the class does not have a metaclass, add one
    # We copy both annotations and constants. This is needed for cases like:
    #
    #   @dataclass
    #   class C:
    #       a: List[] = field(default_factory=list)
    #
    if type(_cls) is type:
        old_annotations = get_all_annotations(_cls)
        from .zeneric2 import StructuralTyping
        old_annotations.update(getattr(_cls, ANNOTATIONS_ATT, {}))
        attrs = {ANNOTATIONS_ATT: old_annotations}
        for k in old_annotations:
            if hasattr(_cls, k):
                attrs[k] = getattr(_cls, k)

        class Base(metaclass=StructuralTyping):
            pass

        _cls2 = type(_cls.__name__, (_cls, Base) + _cls.__bases__, attrs)
        _cls2.__module__ = _cls.__module__
        _cls2.__qualname__ = _cls.__qualname__
        # from . import logger
        # logger.info(f'Replaced {_cls} with {_cls2} with annotations {_cls2.__annotations__}')
        _cls = _cls2
    else:
        old_annotations = get_all_annotations(_cls)
        old_annotations.update(getattr(_cls, ANNOTATIONS_ATT, {}))
        setattr(_cls, ANNOTATIONS_ATT, old_annotations)

    res = original_dataclass(_cls, init=init, repr=repr, eq=eq, order=order,
                             unsafe_hash=unsafe_hash, frozen=frozen)
    remember_created_class(res)
    assert dataclasses.is_dataclass(res)
    refs = getattr(_cls, DEPENDS_ATT, ())
    resolve_types(res, refs=refs)

    def __repr__(self):
        return DataclassHooks.dc_repr(self)

    def __str__(self):
        return DataclassHooks.dc_str(self)

    setattr(res, '__repr__', __repr__)
    setattr(res, '__str__', __str__)
    # res.__doc__  = res.__doc__.replace(' ', '')
    # if original_doc is None:
    setattr(res, '__doc__', original_doc)
    return res


def nice_str(self):
    return DataclassHooks.dc_repr(self)


def blue(x):
    return termcolor.colored(x, 'blue')


def nice_repr(self):
    s = termcolor.colored(type(self).__name__, 'red')
    s += blue('(')
    ss = []

    annotations = getattr(type(self), '__annotations__', {})
    for k in annotations:
        a = getattr(self, k)
        a_s = debug_print_compact(a)
        eq = blue('=')
        k = termcolor.colored(k, attrs=['dark'])
        ss.append(f'{k}{eq}{a_s}')

    s += blue(', ').join(ss)
    s += blue(')')
    return s


def debug_print_compact(x):
    if isinstance(x, str):
        return debug_print_str(x, '')
    if isinstance(x, bytes):
        return debug_print_bytes(x)
    if isinstance(x, datetime):
        return debug_print_date(x, '')
    return f'{x!r}'


def debug_print_str(x: str, prefix: str):
    if x.startswith('Qm'):
        x2 = 'Qm...' + x[-4:] + ' ' + prefix
        return termcolor.colored(x2, 'magenta')
    if x.startswith('zd'):
        x2 = 'zd...' + x[-4:] + ' ' + prefix
        return termcolor.colored(x2, 'magenta')
    if x.startswith('-----BEGIN'):
        s = 'PEM key' + ' ' + prefix
        return termcolor.colored(s, 'yellow')
    if x.startswith('Traceback'):
        lines = x.split('\n')
        colored = [termcolor.colored(_, 'red') for _ in lines]
        if colored:
            colored[0] += '  ' + prefix
        s = "\n".join(colored)
        return s

    return x.__repr__() + ' ' + prefix


def debug_print_date(x: datetime, prefix=None):
    s = x.isoformat()[:19]
    s = s.replace('T', ' ')
    return termcolor.colored(s, 'yellow') + (' ' + prefix if prefix else '')


def debug_print_bytes(x: bytes):
    s = f'{len(x)} bytes ' + x[:10].__repr__()

    return termcolor.colored(s, 'yellow')


class DataclassHooks:
    dc_repr = nice_repr
    dc_str = nice_str


setattr(dataclasses, 'dataclass', my_dataclass)