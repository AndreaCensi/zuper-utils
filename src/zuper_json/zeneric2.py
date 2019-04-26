import sys
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
# noinspection PyUnresolvedReferences
from typing import Dict, Type, TypeVar, Any, ClassVar, Sequence, _eval_type, Tuple
from .logging import logger
from .constants import PYTHON_36

try:
    from typing import ForwardRef
except ImportError:  # pragma: no cover
    from typing import _ForwardRef as ForwardRef

from .annotations_tricks import is_ClassVar, get_ClassVar_arg, is_Type, get_Type_arg, name_for_type_like
from .constants import GENERIC_ATT, BINDINGS_ATT
from .pretty import pretty_dict


def as_tuple(x) -> Tuple:
    return x if isinstance(x, tuple) else (x,)


def get_type_spec(types) -> Dict[str, Type]:
    res = {}
    for x in types:
        if not isinstance(x, TypeVar):  # pragma: no cover
            msg = f'Not sure what happened - but did you import zuper_json? {(x, types)}'
            raise ValueError(msg)

        res[x.__name__] = x.__bound__ or Any
    return res


class ZenericFix:
    class CannotInstantiate(TypeError):
        ...

    @classmethod
    def __class_getitem__(cls, params):
        # pprint('ZenerifFix.__class_getitem__', cls=cls, params=params)
        types = as_tuple(params)

        if PYTHON_36:  # pragma: no cover
            class FakeGenericMeta(ABCMeta):
                def __getitem__(self, params2):
                    types2 = as_tuple(params2)
                    return make_type(self, tuple(types), tuple(types2))
        else:
            FakeGenericMeta = ABCMeta

        class GenericProxy(metaclass=FakeGenericMeta):

            @abstractmethod
            def need(self):
                """"""

            @classmethod
            def __class_getitem__(cls, params2):
                # pprint('ZenericFix', cls=cls, params2=params2)
                types2 = as_tuple(params2)
                return make_type(cls, types, types2)

        name = 'Generic[%s]' % ",".join(_.__name__ for _ in types)

        gp = type(name, (GenericProxy,), {})  # '__getitem__': GenericProxy.__class_getitem__})

        # setattr(gp, '__getitem__', GenericProxy.__class_getitem__)
        setattr(gp, GENERIC_ATT, get_type_spec(types))
        return gp


class NoConstructorImplemented(TypeError):
    pass


def eval_type(T, bindings0: Dict[str, Any], symbols: Dict[str, Any]):
    if T in bindings0:
        return bindings0[T]
    if hasattr(T, '__args__'):
        T.__args__ = tuple(eval_type(_, bindings0, symbols) for _ in T.__args__)

    if isinstance(T, type):
        return T
    info = lambda: dict(bindings=bindings0,
                        symbols=symbols)
    bindings = dict(bindings0)

    try:
        res = _eval_type(T, bindings, symbols)
        # pprint('eval_type', T=T, bindings0=bindings0, symbols=symbols, res=res)
        return res
    except BaseException as e:  # pragma: no cover
        m = f'Cannot eval type {T!r}'
        msg = pretty_dict(m, info())
        raise TypeError(msg) from e


def resolve_types(T, l):
    # g = dict(globals())
    g = {}
    if hasattr(T, '__name__'):
        g[T.__name__] = T
    if hasattr(T, '__annotations__'):
        for k, v in T.__annotations__.items():
            try:
                T.__annotations__[k] = _eval_type(v, g, l)
            except TypeError as e:  # pragma: no cover
                raise TypeError(f'could not resolve {k} = {v}') from e


from dataclasses import is_dataclass


def make_type(cls: type, types, types2: Sequence) -> type:
    # pprint('make_type', types=types, types2=types2)
    # print('cls %s dataclass? %s' % (cls, is_dataclass(cls)))
    # black magic

    for t2 in types2:
        if isinstance(t2, TypeVar):
            # from zuper_json import logger
            # logger.debug(f'trying to instantiate {cls} ({types}) with {t2}')
            name = cls.__name__
            cls2 = type(name, (cls,), {})
            setattr(cls2, GENERIC_ATT, get_type_spec(types2))
            return cls2

    bindings = {T: U for T, U in zip(types, types2)}
    for T, U in bindings.items():
        if T.__bound__ is not None and isinstance(T.__bound__, type):
            if not issubclass(U, T.__bound__):
                msg = (f'For type parameter "{T.__name__}", expected a'
                       f'subclass of "{T.__bound__.__name__}", found {U}.')
                raise TypeError(msg)

    d = {'need': lambda: None}

    annotations = getattr(cls, '__annotations__', {})

    class Fake:
        # pass

        def __getitem__(self, item):
            return ForwardRef(f'{cls.__name__}[{item.__name__}]')

    symbols = {cls.__name__: Fake()}
    for T, U in bindings.items():
        symbols[T.__name__] = U
        if hasattr(U, '__name__'):
            # dict does not have name
            symbols[U.__name__] = U

    # if is_dataclass(cls):
    #     fields = getattr(cls, _FIELDS)
    #     check_isinstance(fields, dict)
    #     fields2 = {}
    #
    #     for k, v in fields.items():
    #         check_isinstance(v, Field)
    #         type2 = eval_type(v.type, bindings, symbols)
    #         f2 = Field(default=v.default,
    #                    default_factory=v.default_factory,
    #                    init=v.init, repr=v.repr, hash=v.hash, compare=v.compare,
    #                    metadata=v.metadata)
    #         f2.name = v.name
    #         f2.type = type2
    #         fields2[k] = f2
    #
    # else:
    #     fields2 = None
    #     pass

    new_annotations = {}

    for k, v in annotations.items():
        if is_ClassVar(v):
            s = get_ClassVar_arg(v)
            s = eval_type(s, bindings, symbols)
            if is_Type(s):
                st = get_Type_arg(s)
                concrete = eval_type(st, bindings, symbols)
                new_annotations[k] = ClassVar[Type]
                d[k] = concrete
            else:
                new_annotations[k] = ClassVar[s]
        else:
            new_annotations[k] = eval_type(v, bindings, symbols)

    name2 = '%s[%s]' % (cls.__name__, ",".join(name_for_type_like(_) for _ in types2))
    assert '<' not in name2, name2
    assert '~' not in name2, (cls.__dict__, name2)

    original__post_init__ = getattr(cls, '__post_init__', None)

    enable_check = False
    def __post_init__(self):
        # s = [(k, type(v)) for k, v in self.__dict__.items()]
        # print('Doing post init check (%s, %s) ' % (type(self), s))
        if enable_check:
            for k, v in new_annotations.items():
                if is_ClassVar(v): continue
                if isinstance(v, type):
                    val = getattr(self, k)
                    try:
                        if type(val).__name__ != v.__name__ and not isinstance(val, v):
                            msg = f'Expected field "{k}" to be a "{v.__name__}" but found {type(val).__name__}'
                            raise ValueError(msg)
                    except TypeError as e:
                        msg = f'Cannot judge annotation of {k} (supposedly {v}.'

                        if sys.version_info[:2] == (3, 6):
                            # FIXME: warn
                            continue
                        logger.error(msg)
                        raise TypeError(msg) from e

        if original__post_init__ is not None:
            original__post_init__(self)

    d['__post_init__'] = __post_init__
    cls2 = type(name2, (cls,), d)

    # important: do it before dataclass
    cls2.__annotations__ = new_annotations

    if is_dataclass(cls):
        # note: need to have set new annotations
        # pprint('creating dataclass from %s' % cls2)
        cls2 = dataclass(cls2)
        # setattr(cls2, _FIELDS, fields2)
    else:
        # print('Detected that cls = %s not a dataclass' % cls)

        # noinspection PyUnusedLocal
        def init_placeholder(self, *args, **kwargs):
            if args or kwargs:
                msg = f'Default constructor of {cls2.__name__} does not know what to do with arguments.'
                msg += f'\nargs: {args!r}\nkwargs: {kwargs!r}'
                msg += f'\nself: {self}'
                msg += f'\nself: {dir(type(self))}'
                msg += f'\nself: {type(self)}'
                raise NoConstructorImplemented(msg)

        setattr(cls2, '__init__', init_placeholder)

    cls2.__module__ = cls.__module__
    setattr(cls2, BINDINGS_ATT, bindings)

    setattr(cls2, GENERIC_ATT, None)

    setattr(cls2, '__post_init__', __post_init__)

    return cls2
