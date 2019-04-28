import sys
import traceback
import typing
import warnings
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields
# noinspection PyUnresolvedReferences
from typing import Dict, Type, TypeVar, Any, ClassVar, Sequence, _eval_type, Tuple

from zuper_commons.text import indent, pretty_dict
from .constants import PYTHON_36, GENERIC_ATT2, BINDINGS_ATT
from .logging import logger

try:
    from typing import ForwardRef
except ImportError:  # pragma: no cover
    from typing import _ForwardRef as ForwardRef

from .annotations_tricks import is_ClassVar, get_ClassVar_arg, is_Type, get_Type_arg, name_for_type_like, \
    is_forward_ref, get_forward_ref_arg, is_optional, get_optional_type, is_List, get_List_arg, is_union, \
    get_union_types


def loglevel(f):
    def f2(*args, **kwargs):
        RecLogger.levels += 1
        # if RecLogger.levels >= 10:
        #     raise AssertionError()
        try:
            return f(*args, **kwargs)
        finally:
            RecLogger.levels -= 1

    return f2


class RecLogger:
    levels = 0
    prefix: Tuple[str, ...]
    count = 0

    def __init__(self, prefix=None):
        if prefix is None:
            prefix = (str(RecLogger.count),)
        RecLogger.count += 1
        self.prefix = prefix

    def p(self, s):
        p = '  ' * RecLogger.levels + ':'
        # p = '/'.join(('root',) + self.prefix) + ':'
        print(indent(s, p))

    def pp(self, msg, **kwargs):
        self.p(pretty_dict(msg, kwargs))

    def child(self, name=None):
        name = name or '-'
        prefix = self.prefix + (name,)
        return RecLogger(prefix)


def get_name_without_brackets(name: str) -> str:
    if '[' in name:
        return name[:name.index('[')]
    else:
        return name


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

                    if types == types2:
                        return cls

                    bindings = {}
                    for T, U in zip(types, types2):
                        bindings[T] = U
                        if T.__bound__ is not None and isinstance(T.__bound__, type):
                            if not issubclass(U, T.__bound__):
                                msg = (f'For type parameter "{T.__name__}", expected a'
                                       f'subclass of "{T.__bound__.__name__}", found {U}.')
                                raise TypeError(msg)

                    return make_type(cls, bindings)

        else:
            FakeGenericMeta = MyABC

        class GenericProxy(metaclass=FakeGenericMeta):

            @abstractmethod
            def need(self):
                """"""

            @classmethod
            def __class_getitem__(cls, params2):
                types2 = as_tuple(params2)

                bindings = {}

                if types == types2:
                    return cls

                for T, U in zip(types, types2):
                    bindings[T] = U
                    if T.__bound__ is not None and isinstance(T.__bound__, type):
                        if not issubclass(U, T.__bound__):
                            msg = (f'For type parameter "{T.__name__}", expected a'
                                   f'subclass of "{T.__bound__.__name__}", found {U}.')
                            raise TypeError(msg)

                return make_type(cls, bindings)

        name = 'Generic[%s]' % ",".join(_.__name__ for _ in types)

        gp = type(name, (GenericProxy,), {GENERIC_ATT2: types})
        # setattr(gp, '__name__', name)
        setattr(gp, GENERIC_ATT2, types)

        return gp


class MyABC(ABCMeta):

    def __new__(mcls, name, bases, namespace, **kwargs):
        # logger.info('name: %s' % name)
        # logger.info('namespace: %s' % namespace)
        # logger.info('bases: %s' % str(bases))
        # if bases:
        #     logger.info('bases[0]: %s' % str(bases[0].__dict__))

        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        # logger.info(name)
        # logger.info(bases)

        # logger.info(kwargs)
        # logger.info(mcls.__dict__)
        if GENERIC_ATT2 in namespace:
            spec = namespace[GENERIC_ATT2]
        # elif 'types_' in namespace:
        #     spec = namespace['types_']
        elif bases and GENERIC_ATT2 in bases[0].__dict__:
            spec = bases[0].__dict__[GENERIC_ATT2]
        else:
            spec = {}

        if spec:
            name0 = get_name_without_brackets(name)
            name = f'{name0}[%s]' % (",".join(name_for_type_like(_) for _ in spec))
            setattr(cls, '__name__', name)
        else:
            pass

        setattr(cls, '__module__', mcls.__module__)
        # logger.info('spec: %s' % spec)
        return cls


class NoConstructorImplemented(TypeError):
    pass


from typing import Optional, Union, List, Set


def get_default_attrs():
    return dict(Any=Any, Optional=Optional, Union=Union, Tuple=Tuple,
                List=List, Set=Set,
                Dict=Dict)


#
# @loglevel
# def eval_type(T, bindings0: Dict[str, Any], symbols0: Dict[str, Any]):
#     symbols = dict(symbols0)
#     symbols.update(get_default_attrs())
#
#     if T in bindings0:
#         return bindings0[T]
#     if T in symbols0:
#         return symbols0[T]
#
#     if isinstance(T, str):
#         try:
#             return eval(T, symbols, {})
#         except NameError:
#             msg = f'Could not resolve {T!r} with {symbols0} {bindings0}'
#             raise NameError(msg) from None
#
#     if isinstance(T, type):
#         return T
#
#     info = lambda: dict(bindings=bindings0,
#                         symbols=symbols)
#     bindings = dict(bindings0)
#
#     if is_forward_ref(T):
#         arg = get_forward_ref_arg(T)
#         return eval_type(arg, bindings0, symbols0)
#
#     if is_optional(T):
#         arg = get_optional_type(T)
#         return Optional[eval_type(arg, bindings0, symbols0)]
#
#     if is_List(T):
#         arg = get_List_arg(T)
#         return typing.List[eval_type(arg, bindings0, symbols0)]
#
#     if hasattr(T, '__args__'):
#         T.__args__ = tuple(eval_type(_, bindings0, symbols) for _ in T.__args__)
#
#     try:
#         res = _eval_type(T, bindings, symbols)
#         # pprint('eval_type', T=T, bindings0=bindings0, symbols=symbols, res=res)
#         return res
#     except BaseException as e:  # pragma: no cover
#         m = f'Cannot eval type {T!r}'
#         msg = pretty_dict(m, info())
#         raise TypeError(msg) from e
#


class Fake:
    def __init__(self, myt, symbols):
        self.myt = myt
        self.name_without = get_name_without_brackets(myt.__name__)
        self.symbols = symbols

    def __getitem__(self, item):
        n = name_for_type_like(item)
        complete = f'{self.name_without}[{n}]'
        if complete in self.symbols:
            return self.symbols[complete]
        # noinspection PyUnresolvedReferences
        return self.myt[item]


@loglevel
def resolve_types(T, locals_=None, refs=()):
    assert is_dataclass(T)
    rl = RecLogger()
    # rl.p(f'resolving types for {T!r}')
    # g = dict(globals())
    # g = {}
    # locals_ = {}
    #
    # if hasattr(T, GENERIC_ATT):
    #     for k, v in getattr(T, GENERIC_ATT).items():
    #         g[k] = TypeVar(k)
    # if hasattr(T, '__name__'):
    #     g[get_name_without_brackets(T.__name__)] = T
    #
    # g['Optional'] = typing.Optional
    # g['Any'] = Any
    # g['Union'] = typing.Union
    # # print('globals: %s' % g)
    symbols = dict(locals_ or {})

    for t in (T,) + refs:

        symbols[t.__name__] = t
        name_without = get_name_without_brackets(t.__name__)

        if name_without not in symbols:
            symbols[name_without] = Fake(t, symbols)
        else:
            pass

    for x in getattr(T, GENERIC_ATT2, ()):
        if hasattr(x, '__name__'):
            symbols[x.__name__] = x

    annotations = getattr(T, '__annotations__', {})

    for k, v in annotations.items():
        try:
            r = replace_typevars(v, bindings={}, symbols=symbols, rl=None)
            # rl.p(f'{k!r} -> {v!r} -> {r!r}')
            annotations[k] = r
        except NameError as e:
            msg = f'resolve_type({T.__name__}): Cannot resolve names for attribute "{k}".'
            msg += f'\n symbols: {symbols}'
            msg += '\n\n' + indent(traceback.format_exc(), '', '> ')
            logger.warning(msg)
            continue
        except TypeError as e:
            msg = f'Cannot resolve type for attribute "{k}".'

            raise TypeError(msg) from e
    for f in fields(T):
        if not f.name in annotations:
            # msg = f'Cannot get annotation for field {f.name!r}'
            # logger.warning(msg)
            continue
        f.type = annotations[f.name]


from dataclasses import is_dataclass


@loglevel
def replace_typevars(cls, *, bindings, symbols, rl: Optional[RecLogger], already=None):
    rl = rl or RecLogger()
    # rl.p(f'Replacing typevars {cls}')
    # rl.p(f'   bindings {bindings}')
    # rl.p(f'   symbols {symbols}')

    already = already or {}

    if id(cls) in already:
        return already[id(cls)]

    elif cls in bindings:
        return bindings[cls]

    elif isinstance(cls, str):
        if cls in symbols:
            return symbols[cls]
        g = dict(get_default_attrs())
        g.update(symbols)
        # for t, u in zip(types, types2):
        #     g[t.__name__] = u
        #     g[u.__name__] = u
        g0 = dict(g)
        try:
            return eval(cls, g)
        except NameError as e:
            msg = f'Cannot resolve {cls!r}\ng: {list(g0)}'
            # msg += 'symbols: {list(g0)'
            raise NameError(msg) from e

    elif hasattr(cls, '__annotations__'):
        return make_type(cls, bindings)
    elif is_Type(cls):
        x = get_Type_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols, rl=rl.child('classvar arg'))
        return Type[r]
    elif is_ClassVar(cls):
        x = get_ClassVar_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols, rl=rl.child('classvar arg'))
        return typing.ClassVar[r]
    elif is_List(cls):
        arg = get_List_arg(cls)
        return typing.List[
            replace_typevars(arg, bindings=bindings, already=already, symbols=symbols, rl=rl.child('list arg'))]
    elif is_optional(cls):
        x = get_optional_type(cls)
        return typing.Optional[
            replace_typevars(x, bindings=bindings, already=already, symbols=symbols, rl=rl.child('optional arg'))]
    elif is_union(cls):
        xs = get_union_types(cls)
        ys = tuple(replace_typevars(_, bindings=bindings, already=already, symbols=symbols, rl=rl.child())
                   for _ in xs)
        return typing.Union[ys]

    elif is_forward_ref(cls):
        T = get_forward_ref_arg(cls)
        return replace_typevars(T, bindings=bindings, already=already, symbols=symbols, rl=rl.child('forward '))
    else:
        return cls


cache_enabled = True

cache = {}


@loglevel
def make_type(cls: type, bindings: Dict[TypeVar, Any], rl: RecLogger = None) -> type:
    if not bindings:
        return cls
    cache_key = (str(cls), str(bindings))
    if cache_enabled:
        if cache_key in cache:
            return cache[cache_key]

    rl = rl or RecLogger()
    generic_att2 = getattr(cls, GENERIC_ATT2, ())
    assert isinstance(generic_att2, tuple)
    # rl.p(f'make_type for {cls.__name__}')
    # rl.p(f'  dataclass {is_dataclass(cls)}')
    # rl.p(f'  bindings: {bindings}')
    # rl.p(f'  generic_att: {generic_att2}')

    symbols = {}

    annotations = getattr(cls, '__annotations__', {})
    name_without = get_name_without_brackets(cls.__name__)

    def param_name(x):
        x2 = replace_typevars(x, bindings=bindings, symbols=symbols, rl=rl.child('param_name'))
        return name_for_type_like(x2)

    if generic_att2:
        name2 = '%s[%s]' % (name_without, ",".join(param_name(_) for _ in generic_att2))
    else:
        name2 = name_without
    # rl.p('  name2: %s' % name2)
    try:
        cls2 = type(name2, (cls,), {'need': lambda: None})
    except TypeError as e:
        msg = f'Cannot instantiate from {cls!r}'
        raise TypeError(msg) from e

    symbols[name2] = cls2
    symbols[cls.__name__] = cls2  # also MyClass[X] should resolve to the same
    cache[cache_key] = cls2

    #
    class Fake:
        def __getitem__(self, item):
            n = name_for_type_like(item)
            complete = f'{name_without}[{n}]'
            if complete in symbols:
                return symbols[complete]
            # noinspection PyUnresolvedReferences
            return cls[item]

    if name_without not in symbols:
        symbols[name_without] = Fake()
    else:
        pass

    for T, U in bindings.items():
        symbols[T.__name__] = U
        if hasattr(U, '__name__'):
            # dict does not have name
            symbols[U.__name__] = U

    # first of all, replace the bindings in the generic_att

    generic_att2_new = tuple(
            replace_typevars(_, bindings=bindings, symbols=symbols, rl=rl.child('attribute')) for _ in generic_att2)

    # rl.p(f'  generic_att2_new: {generic_att2_new}')

    # pprint(f'\n\n{cls.__name__}')
    # pprint(f'binding', bindings=str(bindings))
    # pprint(f'symbols', **symbols)

    new_annotations = {}

    for k, v0 in annotations.items():
        # v = eval_type(v0, bindings, symbols)
        # if hasattr(v, GENERIC_ATT):
        v = replace_typevars(v0, bindings=bindings, symbols=symbols, rl=rl.child(f'ann {k}'))
        # print(f'{v0!r} -> {v!r}')
        if is_ClassVar(v):
            s = get_ClassVar_arg(v)
            # s = eval_type(s, bindings, symbols)
            if is_Type(s):
                st = get_Type_arg(s)
                # concrete = eval_type(st, bindings, symbols)
                concrete = st
                new_annotations[k] = ClassVar[Type[st]]
                setattr(cls2, k, concrete)
            else:
                new_annotations[k] = ClassVar[s]
        else:
            new_annotations[k] = v

    # pprint('  new annotations', **new_annotations)
    original__post_init__ = getattr(cls, '__post_init__', None)

    def __post_init__(self):

        for k, v in new_annotations.items():
            if is_ClassVar(v): continue
            if isinstance(v, type):
                val = getattr(self, k)
                try:
                    if type(val).__name__ != v.__name__ and not isinstance(val, v):
                        msg = f'Expected field "{k}" to be a "{v.__name__}" but found {type(val).__name__}'
                        warnings.warn(msg, stacklevel=3)
                        # raise ValueError(msg)
                except TypeError as e:
                    msg = f'Cannot judge annotation of {k} (supposedly {v}.'

                    if sys.version_info[:2] == (3, 6):
                        # FIXME: warn
                        continue
                    logger.error(msg)
                    raise TypeError(msg) from e

        if original__post_init__ is not None:
            original__post_init__(self)

    setattr(cls2, '__post_init__', __post_init__)
    # important: do it before dataclass
    cls2.__annotations__ = new_annotations

    # logger.info('new annotations: %s' % new_annotations)
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
    setattr(cls2, '__name__', name2)
    setattr(cls2, BINDINGS_ATT, bindings)

    setattr(cls2, GENERIC_ATT2, generic_att2_new)

    setattr(cls2, '__post_init__', __post_init__)

    # rl.p(f'  final {cls2.__name__}  {cls2.__annotations__}')
    # rl.p(f'     dataclass {is_dataclass(cls2)}')
    #

    return cls2
