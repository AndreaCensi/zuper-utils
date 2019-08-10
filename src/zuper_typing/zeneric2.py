import sys
import typing
import warnings
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields
# noinspection PyUnresolvedReferences
from typing import Any, ClassVar, Dict, Sequence, Tuple, Type, TypeVar, _eval_type

from zuper_commons.text import indent, pretty_dict
from zuper_typing.my_dict import (get_CustomList_arg, get_DictLike_args, get_SetLike_arg, is_CustomList, is_DictLike,
                                  is_SetLike, make_dict, make_list, make_set)
from .annotations_tricks import (get_Callable_info, get_ClassVar_arg, get_ForwardRef_arg, get_Iterator_arg,
                                 get_List_arg, get_Optional_arg, get_Sequence_arg, get_Set_arg, get_TypeVar_name,
                                 get_Type_arg, get_Union_args, get_tuple_types, is_Callable, is_ClassVar, is_ForwardRef,
                                 is_Iterator, is_List, is_NewType, is_Optional, is_Sequence, is_Set, is_Tuple, is_Type,
                                 is_TypeVar, is_Union, name_for_type_like)
from .constants import BINDINGS_ATT, DEPENDS_ATT, GENERIC_ATT2, PYTHON_36
from .logging import logger
from .subcheck import can_be_used_as2


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


def map_none_to_nonetype(x):
    if x is None:
        return type(None)
    else:
        return x


class ZenericFix:
    class CannotInstantiate(TypeError):
        ...

    @classmethod
    def __class_getitem__(cls0, params):
        # logger.info(f'ZenericFix.__class_getitem__ params = {params}')
        types = as_tuple(params)
        types = tuple(map(map_none_to_nonetype, types))

        # logger.info(f'types {types}')

        if PYTHON_36:  # pragma: no cover
            class FakeGenericMeta(MyABC):
                def __getitem__(self, params2):
                    # pprint('FakeGenericMeta.__getitem__', cls=cls, self=self,
                    # params2=params2)
                    types2 = as_tuple(params2)

                    if types == types2:
                        return self

                    bindings = {}
                    for T, U in zip(types, types2):
                        bindings[T] = U
                        if T.__bound__ is not None and isinstance(T.__bound__, type):
                            if not issubclass(U, T.__bound__):
                                msg = (f'For type parameter "{T.__name__}", expected a'
                                       f'subclass of "{T.__bound__.__name__}", found {U}.')
                                raise TypeError(msg)

                    return make_type(self, bindings)

        else:
            FakeGenericMeta = MyABC

        class GenericProxy(metaclass=FakeGenericMeta):

            @abstractmethod
            def need(self):
                """"""

            @classmethod
            def __class_getitem__(cls2, params2):
                # logger.info(f'GenericProxy.__class_getitem__ params = {params2}')
                types2 = as_tuple(params2)

                bindings = {}

                if types == types2:
                    return cls2

                for T, U in zip(types, types2):
                    bindings[T] = U
                    if T.__bound__ is not None and isinstance(T.__bound__, type):
                        logger.info(f'{U} should be usable as {T.__bound__}')
                        logger.info(
                              f' issubclass({U}, {T.__bound__}) ='
                              f' {issubclass(U, T.__bound__)}')
                        if not issubclass(U, T.__bound__):
                            msg = (f'For type parameter "{T.__name__}", expected a'
                                   f'subclass of "{T.__bound__.__name__}", found {U}.')
                            raise TypeError(msg)

                # logger.info(f'cls0 qual: {cls0.__qualname__}')
                res = make_type(cls2, bindings)
                # A = lambda C: getattr(C, '__annotations__', 'no anns')
                # print(f'results of particularization of {cls.__name__} with {
                # params2}:\nbefore: {A(cls)}\nafter: {A(res)}')
                return res

        name = 'Generic[%s]' % ",".join(name_for_type_like(_) for _ in types)

        gp = type(name, (GenericProxy,), {GENERIC_ATT2: types})
        setattr(gp, GENERIC_ATT2, types)

        return gp


class StructuralTyping(type):

    def __subclasscheck__(self, subclass) -> bool:

        can = can_be_used_as2(subclass, self, {})
        # logger.info(
        #     f'StructuralTyping: Performing __subclasscheck__ {self} {id(self)} {subclass}
        #     {id(subclass)}: {can}')
        return can.result

    def __instancecheck__(self, instance) -> bool:
        i = super().__instancecheck__(instance)
        if i:
            return True

        # loadable
        if 'Loadable' in type(instance).__name__ and hasattr(instance, 'T'):
            if hasattr(instance, 'T'):
                T = getattr(instance, 'T')
                can = can_be_used_as2(T, self, {})
                if can.result:
                    return True

        res = can_be_used_as2(type(instance), self, {})

        return res.result


class MyABC(ABCMeta, StructuralTyping):
    #
    def __subclasscheck__(self, subclass) -> bool:

        can = can_be_used_as2(subclass, self, {})
        # logger.info(f'MyABC: Performing __subclasscheck__ {self} {id(self)} {subclass} {
        # id(subclass)}: {can}')
        return can.result

    def __instancecheck__(self, instance) -> bool:
        i = super().__instancecheck__(instance)
        if i:
            return True

        # loadable
        if 'Loadable' in type(instance).__name__ and hasattr(instance, 'T'):
            T = getattr(instance, 'T')
            logger.info(f'Comparing {self} and type {type(instance)} {T}')
            can = can_be_used_as2(T, self, {})
            if can.result:
                return True

        res = can_be_used_as2(type(instance), self, {})

        return res.result

    def __new__(mcls, name_orig, bases, namespace, **kwargs):
        # logger.info(f'----\nCreating name: {name}')
        # logger.info('namespace: %s' % namespace)
        # logger.info('bases: %s' % str(bases))
        # if bases:
        #     logger.info('bases[0]: %s' % str(bases[0].__dict__))

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
        # logger.info(f'Creating name: {name} spec {spec}')
        if spec:
            name0 = get_name_without_brackets(name_orig)
            name = f'{name0}[%s]' % (",".join(name_for_type_like(_) for _ in spec))
            # setattr(cls, '__name__', name)
        else:
            name = name_orig

        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        qn = cls.__qualname__.replace(name_orig, name)

        # if 'need' in namespace and bases:
        #     qn = bases[0].__qualname__
        setattr(cls, '__qualname__', qn)
        # logger.info(f'in MyABC choosing qualname {cls.__qualname__!r} from {cls.__qualname__} ({mcls.__qualname__}')
        setattr(cls, '__module__', mcls.__module__)
        setattr(cls, GENERIC_ATT2, spec)
        # logger.info('spec: %s' % spec)
        return cls


class NoConstructorImplemented(TypeError):
    pass


from typing import Optional, Union, List, Set


def get_default_attrs():
    return dict(Any=Any, Optional=Optional, Union=Union, Tuple=Tuple,
                List=List, Set=Set,
                Dict=Dict)


class Fake:
    def __init__(self, myt, symbols):
        self.myt = myt
        n = name_for_type_like(myt)
        self.name_without = get_name_without_brackets(n)
        self.symbols = symbols

    def __getitem__(self, item):
        n = name_for_type_like(item)
        complete = f'{self.name_without}[{n}]'
        if complete in self.symbols:
            return self.symbols[complete]
        # noinspection PyUnresolvedReferences
        return self.myt[item]


@loglevel
def resolve_types(T, locals_=None, refs: Tuple=(), nrefs: Optional[Dict[str, Any]] = None):
    nrefs = nrefs or {}
    assert is_dataclass(T)
    # rl = RecLogger()

    symbols = dict(locals_ or {})

    for k, v in nrefs.items():
        symbols[k] = v

    others = getattr(T, DEPENDS_ATT, ())

    for t in (T,) + refs + others:
        n = name_for_type_like(t)
        symbols[n] = t
        # logger.info(f't = {t} n {n}')
        name_without = get_name_without_brackets(n)

        if name_without in ['Union', 'Dict', ]:
            # FIXME please add more here
            continue
        if name_without not in symbols:
            symbols[name_without] = Fake(t, symbols)
        else:
            pass

    for x in getattr(T, GENERIC_ATT2, ()):
        if hasattr(x, '__name__'):
            symbols[x.__name__] = x

    # logger.debug(f'symbols: {symbols}')
    annotations = getattr(T, '__annotations__', {})

    for k, v in annotations.items():
        if not isinstance(v, str) and is_ClassVar(v):
            continue  # XXX
        try:
            r = replace_typevars(v, bindings={}, symbols=symbols, rl=None)
            # rl.p(f'{k!r} -> {v!r} -> {r!r}')
            annotations[k] = r
        except NameError as e:
            msg = f'resolve_type({T.__name__}):' \
                  f' Cannot resolve names for attribute "{k}" = {v!r}.'
            # msg += f'\n symbols: {symbols}'
            # msg += '\n\n' + indent(traceback.format_exc(), '', '> ')
            # raise NameError(msg) from e
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

    if cls is type:
        return cls

    if id(cls) in already:
        # rl.p('cached')
        # XXX
        return already[id(cls)]

    elif (isinstance(cls, str) or is_TypeVar(cls)) and cls in bindings:
        return bindings[cls]
    elif is_TypeVar(cls):
        name = get_TypeVar_name(cls)

        for k, v in bindings.items():
            if is_TypeVar(k) and get_TypeVar_name(k) == name:
                return v
        return cls
        # return bindings[cls]

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
    elif is_NewType(cls):
        return cls

    elif is_Type(cls):
        x = get_Type_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('classvar arg'))
        if x == r:
            return cls
        return Type[r]
    elif is_DictLike(cls):
        K0, V0 = get_DictLike_args(cls)
        K = replace_typevars(K0, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('k'))
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('v'))
        # logger.debug(f'{K0} -> {K};  {V0} -> {V}')
        if (K0, V0) == (K, V):
            return cls
        return make_dict(K, V)
    elif is_SetLike(cls):
        V0 = get_SetLike_arg(cls)
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('v'))
        if V0 == V:
            return cls
        return make_set(V)
    elif is_CustomList(cls):
        V0 = get_CustomList_arg(cls)
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('v'))
        if V0 == V:
            return cls
        return make_list(V)
    # XXX NOTE: must go after CustomDict
    elif hasattr(cls, '__annotations__'):
        return make_type(cls, bindings)
    elif is_ClassVar(cls):
        x = get_ClassVar_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('classvar arg'))
        if x == r:
            return cls
        return typing.ClassVar[r]
    elif is_Type(cls):
        x = get_Type_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('classvar arg'))
        if x == r:
            return cls
        return typing.Type[r]
    elif is_Iterator(cls):
        x = get_Iterator_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('classvar arg'))
        if x == r:
            return cls
        return typing.Iterator[r]
    elif is_Sequence(cls):
        x = get_Sequence_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                             rl=rl.child('classvar arg'))
        if x == r:
            return cls

        return typing.Sequence[r]

    elif is_List(cls):
        arg = get_List_arg(cls)
        arg2 = replace_typevars(arg, bindings=bindings, already=already, symbols=symbols,
                                rl=rl.child('list arg'))
        if arg == arg2:
            return cls
        return typing.List[arg2]
    elif is_Set(cls):
        arg = get_Set_arg(cls)
        arg2 = replace_typevars(arg, bindings=bindings, already=already, symbols=symbols,
                                rl=rl.child('set arg'))
        if arg == arg2:
            return cls
        return typing.Set[arg2]
    elif is_Optional(cls):
        x = get_Optional_arg(cls)
        x2 = replace_typevars(x, bindings=bindings, already=already, symbols=symbols,
                              rl=rl.child('optional arg'))
        if x == x2:
            return cls
        return typing.Optional[x2]

    elif is_Union(cls):
        xs = get_Union_args(cls)
        ys = tuple(replace_typevars(_, bindings=bindings, already=already, symbols=symbols,
                                    rl=rl.child())
                   for _ in xs)
        if ys == xs:
            return cls
        return typing.Union[ys]
    elif is_Tuple(cls):

        xs = get_tuple_types(cls)
        ys = tuple(replace_typevars(_, bindings=bindings, already=already, symbols=symbols,
                                    rl=rl.child())
                   for _ in xs)
        if ys == xs:
            return cls
        return typing.Tuple[ys]
    elif is_Callable(cls):
        cinfo = get_Callable_info(cls)

        def f(_):
            return replace_typevars(_, bindings=bindings, already=already, symbols=symbols,
                                    rl=rl.child())

        cinfo2 = cinfo.replace(f)
        return cinfo2.as_callable()
        #
        # pos = []
        # for p in cinfo.parameters_by_name:
        #
        # ret = replace_typevars(cinfo.returns, bindings=bindings, already=already,
        # symbols=symbols, rl=rl.child())
        #
        # xs = get_tuple_types(cls)
        # ys = tuple()
        #            for _ in xs)
        # return typing.Tuple[ys]

    elif is_ForwardRef(cls):
        T = get_ForwardRef_arg(cls)
        return replace_typevars(T, bindings=bindings, already=already, symbols=symbols,
                                rl=rl.child('forward '))
    else:
        # logger.debug(f'Nothing to do with {cls!r} {cls}')
        return cls


cache_enabled = True


class MakeTypeCache:
    cache = {}


if PYTHON_36:
    B = Dict[Any, Any]  # bug in Python 3.6
else:
    B = Dict[TypeVar, Any]


# @loglevel
def make_type(cls: type, bindings: B, rl: RecLogger = None) -> type:
    assert not is_NewType(cls)
    rl = rl or RecLogger()
    # print(f'make_type for {cls.__name__}')
    # rl.p(f'make_type for {cls.__name__}')
    # rl.p(f'  dataclass {is_dataclass(cls)}')
    # rl.p(f'  bindings: {bindings}')
    # rl.p(f'  generic_att: {generic_att2}')
    if not bindings:
        return cls
    cache_key = (str(cls), str(bindings))
    if cache_enabled:
        if cache_key in MakeTypeCache.cache:
            # print(f'using cached value for {cache_key}')
            return MakeTypeCache.cache[cache_key]

    generic_att2 = getattr(cls, GENERIC_ATT2, ())
    assert isinstance(generic_att2, tuple)

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
        # cls2.__qualname__ = cls.__qualname__
        # logger.info(f'Created class {cls2} ({name2}) and set qualname {cls2.__qualname__}')
    except TypeError as e:
        msg = f'Cannot create derived class "{name2}" from {cls!r}'
        raise TypeError(msg) from e

    symbols[name2] = cls2
    symbols[cls.__name__] = cls2  # also MyClass[X] should resolve to the same
    MakeTypeCache.cache[cache_key] = cls2

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

    for T, U in bindings.items():
        symbols[T.__name__] = U
        if hasattr(U, '__name__'):
            # dict does not have name
            symbols[U.__name__] = U

    # first of all, replace the bindings in the generic_att

    generic_att2_new = tuple(
          replace_typevars(_, bindings=bindings, symbols=symbols, rl=rl.child('attribute')) for
          _ in generic_att2)

    # logger.debug(
    #     f"creating derived class {name2} with abstract method need() because
    #     generic_att2_new = {generic_att2_new}")

    # rl.p(f'  generic_att2_new: {generic_att2_new}')

    # pprint(f'\n\n{cls.__name__}')
    # pprint(f'binding', bindings=str(bindings))
    # pprint(f'symbols', **symbols)

    new_annotations = {}

    for k, v0 in annotations.items():

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
                        msg = f'Expected field "{k}" to be a "{v.__name__}"' \
                              f'but found {type(val).__name__}'
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
        doc = getattr(cls2, '__doc__', None)
        cls2 = dataclass(cls2, unsafe_hash=True)
        setattr(cls2, '__doc__', doc)
    else:
        # noinspection PyUnusedLocal
        def init_placeholder(self, *args, **kwargs):
            if args or kwargs:
                msg = f'Default constructor of {cls2.__name__} does not know what to do with ' \
                      f'' \
                      f'' \
                      f'arguments.'
                msg += f'\nargs: {args!r}\nkwargs: {kwargs!r}'
                msg += f'\nself: {self}'
                msg += f'\nself: {dir(type(self))}'
                msg += f'\nself: {type(self)}'
                raise NoConstructorImplemented(msg)

        if cls.__init__ == object.__init__:
            setattr(cls2, '__init__', init_placeholder)

    cls2.__module__ = cls.__module__
    setattr(cls2, '__name__', name2)
    qn = cls.__qualname__
    qn0, _, _ = qn.rpartition('.')

    setattr(cls2, '__qualname__', qn0 + '.' + name2)
    # logger.info(f'choosing qualname {cls2.__qualname__!r} from {qn}')
    setattr(cls2, BINDINGS_ATT, bindings)

    setattr(cls2, GENERIC_ATT2, generic_att2_new)

    setattr(cls2, '__post_init__', __post_init__)

    # rl.p(f'  final {cls2.__name__}  {cls2.__annotations__}')
    # rl.p(f'     dataclass {is_dataclass(cls2)}')
    #
    MakeTypeCache.cache[cache_key] = cls2

    # logger.info(f'started {cls}; hash is {cls.__hash__}')
    # logger.info(f'specialized {cls2}; hash is {cls2.__hash__}')
    return cls2
