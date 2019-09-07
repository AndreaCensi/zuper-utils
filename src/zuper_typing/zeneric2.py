import sys
import typing
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, Dict, Tuple


from .annotations_tricks import (
    get_ClassVar_arg,
    get_Type_arg,
    is_ClassVar,
    is_NewType,
    is_Type,
    name_for_type_like,
)
from .constants import (
    BINDINGS_ATT,
    cache_enabled,
    DEPENDS_ATT,
    enable_type_checking,
    GENERIC_ATT2,
    MakeTypeCache,
    PYTHON_36,
)
from .logging import logger
from .recursive_tricks import (
    get_name_without_brackets,
    NoConstructorImplemented,
    replace_typevars,
    TypeLike,
)
from .subcheck import can_be_used_as2


def as_tuple(x) -> Tuple:
    return x if isinstance(x, tuple) else (x,)


if PYTHON_36:  # pragma: no cover
    from typing import GenericMeta

    # noinspection PyUnresolvedReferences
    old_one = GenericMeta.__getitem__
else:
    old_one = None

# if PYTHON_36:
#     logger.info('In Python 3.6')
#     class ZMeta:
#         @staticmethod
#         def __getitem__(self, params):
#             # pprint('P36', params=params, self=self)
#             if self is typing.Generic:
#                 return ZenericFix.__class_getitem__(params)
#
#             if self is typing.Dict:
#                 K, V = params
#                 if K is not str:
#                     from zuper_typing.my_dict import make_dict
#
#                     return make_dict(K, V)
#
#             # noinspection PyArgumentList
#             return old_one(self, params)
# else:
#     ZMeta = object


class ZenericFix:
    # class CannotInstantiate(TypeError):
    #     ...
    #
    if PYTHON_36:  # pragma: no cover

        def __getitem__(self, params):
            # pprint('P36', params=params, self=self)
            if self is typing.Generic:
                return ZenericFix.__class_getitem__(params)

            if self is typing.Dict:
                K, V = params
                if K is not str:
                    from zuper_typing.my_dict import make_dict

                    return make_dict(K, V)

            # noinspection PyArgumentList
            return old_one(self, params)

    @classmethod
    def __class_getitem__(cls0, params):
        # logger.info(f'ZenericFix.__class_getitem__ params = {params}')
        types = as_tuple(params)
        # types = tuple(map(map_none_to_nonetype, types))

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
                                msg = (
                                    f'For type parameter "{T.__name__}", expected a'
                                    f'subclass of "{T.__bound__.__name__}", found {U}.'
                                )
                                raise TypeError(msg)

                    return make_type(self, bindings)

        else:
            FakeGenericMeta = MyABC

        class GenericProxy(metaclass=FakeGenericMeta):
            @abstractmethod
            def need(self) -> None:
                """"""

            @classmethod
            def __class_getitem__(cls, params2) -> type:
                # logger.info(f'GenericProxy.__class_getitem__ params = {params2}')
                types2 = as_tuple(params2)

                bindings = {}

                for T, U in zip(types, types2):
                    bindings[T] = U
                    if T.__bound__ is not None and isinstance(T.__bound__, type):
                        # logger.info(f"{U} should be usable as {T.__bound__}")
                        # logger.info(
                        #     f" issubclass({U}, {T.__bound__}) ="
                        #     f" {issubclass(U, T.__bound__)}"
                        # )
                        if not issubclass(U, T.__bound__):
                            msg = (
                                f'For type parameter "{T.__name__}", expected a'
                                f'subclass of "{T.__bound__.__name__}", found @U.'
                            )
                            raise TypeError(msg)  # , U=U)

                res = make_type(cls, bindings)
                return res

        name = "Generic[%s]" % ",".join(name_for_type_like(_) for _ in types)

        gp = type(name, (GenericProxy,), {GENERIC_ATT2: types})
        setattr(gp, GENERIC_ATT2, types)

        return gp


class StructuralTyping(type):
    def __subclasscheck__(self, subclass) -> bool:
        can = can_be_used_as2(subclass, self)
        return can.result

    def __instancecheck__(self, instance) -> bool:
        T = type(instance)
        if T is self:
            return True
        if not is_dataclass(T):
            return False
        i = super().__instancecheck__(instance)
        if i:
            return True

        # loadable  - To remove
        if "Loadable" in T.__name__ and hasattr(instance, "T"):  # pragma: no cover
            if hasattr(instance, "T"):
                T = getattr(instance, "T")
                can = can_be_used_as2(T, self)
                if can.result:
                    return True

        res = can_be_used_as2(T, self)

        return res.result


class MyABC(StructuralTyping, ABCMeta):
    def __new__(mcs, name_orig, bases, namespace, **kwargs):
        # logger.info(f'----\nCreating name: {name}')
        # logger.info('namespace: %s' % namespace)
        # logger.info('bases: %s' % str(bases))
        # if bases:
        #     logger.info('bases[0]: %s' % str(bases[0].__dict__))
        if GENERIC_ATT2 in namespace:
            spec = namespace[GENERIC_ATT2]
        elif bases and GENERIC_ATT2 in bases[0].__dict__:
            spec = bases[0].__dict__[GENERIC_ATT2]
        else:
            spec = {}
        if spec:
            name0 = get_name_without_brackets(name_orig)
            name = f"{name0}[%s]" % (",".join(name_for_type_like(_) for _ in spec))
        else:
            name = name_orig

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        qn = cls.__qualname__.replace(name_orig, name)

        setattr(cls, "__qualname__", qn)
        setattr(cls, "__module__", mcs.__module__)
        setattr(cls, GENERIC_ATT2, spec)
        return cls


from typing import Optional


class Fake:
    symbols: dict
    myt: type

    def __init__(self, myt, symbols: dict):
        self.myt = myt
        n = name_for_type_like(myt)
        self.name_without = get_name_without_brackets(n)
        self.symbols = symbols

    def __getitem__(self, item: type) -> type:
        n = name_for_type_like(item)
        complete = f"{self.name_without}[{n}]"
        if complete in self.symbols:
            return self.symbols[complete]
        # noinspection PyUnresolvedReferences
        return self.myt[item]


def resolve_types(
    T, locals_=None, refs: Tuple = (), nrefs: Optional[Dict[str, Any]] = None
):
    if nrefs is None:
        nrefs = {}

    assert is_dataclass(T)
    # rl = RecLogger()

    if locals_ is None:
        locals_ = {}
    symbols = dict(locals_)

    for k, v in nrefs.items():
        symbols[k] = v

    others = getattr(T, DEPENDS_ATT, ())

    for t in (T,) + refs + others:
        n = name_for_type_like(t)
        symbols[n] = t
        # logger.info(f't = {t} n {n}')
        name_without = get_name_without_brackets(n)

        # if name_without in ['Union', 'Dict', ]:
        #     # FIXME please add more here
        #     continue
        if name_without not in symbols:
            symbols[name_without] = Fake(t, symbols)
        # else:
        #     pass

    for x in getattr(T, GENERIC_ATT2, ()):
        if hasattr(x, "__name__"):
            symbols[x.__name__] = x

    # logger.debug(f'symbols: {symbols}')
    annotations: Dict[str, TypeLike] = getattr(T, "__annotations__", {})

    for k, v in annotations.items():
        if not isinstance(v, str) and is_ClassVar(v):
            continue  # XXX
        try:
            r = replace_typevars(v, bindings={}, symbols=symbols)
            # rl.p(f'{k!r} -> {v!r} -> {r!r}')
            annotations[k] = r
        except NameError:
            msg = (
                f"resolve_type({T.__name__}):"
                f' Cannot resolve names for attribute "{k}" = {v!r}.'
            )
            # msg += f'\n symbols: {symbols}'
            # msg += '\n\n' + indent(traceback.format_exc(), '', '> ')
            # raise NameError(msg) from e
            logger.warning(msg)
            continue
        except TypeError as e:  # pragma: no cover
            msg = f'Cannot resolve type for attribute "{k}".'
            raise ZTypeError(msg) from e
    for f in fields(T):
        assert f.name in annotations
        # msg = f'Cannot get annotation for field {f.name!r}'
        # logger.warning(msg)
        # continue
        f.type = annotations[f.name]


#
# if PYTHON_36:
#     B = Dict[Any, Any]  # bug in Python 3.6
# else:
#     B = Dict[TypeVar, Any]


def make_type(cls: type, bindings, symbols=None) -> type:
    if symbols is None:
        symbols = {}
    symbols = dict(symbols)

    assert not is_NewType(cls)
    # logger.info(f'make_type ({cls}) {bindings}')
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

    recur = lambda _: replace_typevars(_, bindings=bindings, symbols=symbols)

    annotations = getattr(cls, "__annotations__", {})
    name_without = get_name_without_brackets(cls.__name__)

    def param_name(x: type) -> str:
        x2 = recur(x)
        return name_for_type_like(x2)

    if generic_att2:
        name2 = "%s[%s]" % (name_without, ",".join(param_name(_) for _ in generic_att2))
    else:
        name2 = name_without
    try:
        cls2 = type(name2, (cls,), {"need": lambda: None})
        # logger.info(f'Created class {cls2} ({name2}) and set qualname {cls2.__qualname__}')
    except TypeError as e:  # pragma: no cover
        msg = f'Cannot create derived class "{name2}" from {cls!r}'
        raise TypeError(msg) from e

    symbols[name2] = cls2
    symbols[cls.__name__] = cls2  # also MyClass[X] should resolve to the same
    MakeTypeCache.cache[cache_key] = cls2

    class Fake2:
        def __getitem__(self, item):
            n = name_for_type_like(item)
            complete = f"{name_without}[{n}]"
            if complete in symbols:
                return symbols[complete]
            # noinspection PyUnresolvedReferences
            return cls[item]

    if name_without not in symbols:
        symbols[name_without] = Fake2()

    for T, U in bindings.items():
        symbols[T.__name__] = U
        if hasattr(U, "__name__"):
            # dict does not have name
            symbols[U.__name__] = U

    # first of all, replace the bindings in the generic_att

    generic_att2_new = tuple(recur(_) for _ in generic_att2)

    # logger.debug(
    #     f"creating derived class {name2} with abstract method need() because
    #     generic_att2_new = {generic_att2_new}")

    # rl.p(f'  generic_att2_new: {generic_att2_new}')

    # pprint(f'\n\n{cls.__name__}')
    # pprint(f'binding', bindings=str(bindings))
    # pprint(f'symbols', **symbols)

    new_annotations = {}

    # logger.info(f'annotations ({annotations}) ')
    for k, v0 in annotations.items():
        v = recur(v0)

        # print(f'{v0!r} -> {v!r}')
        if is_ClassVar(v):
            s = get_ClassVar_arg(v)

            if is_Type(s):
                st = get_Type_arg(s)
                concrete = recur(st)
                # logger.info(f'is_Type ({s}) -> {concrete}')
                # concrete = st
                new_annotations[k] = ClassVar[type]
                setattr(cls2, k, concrete)
            else:
                s2 = recur(s)
                new_annotations[k] = ClassVar[s2]
        else:

            new_annotations[k] = v

    # logger.info(f'new_annotations {new_annotations}')
    # pprint('  new annotations', **new_annotations)
    original__post_init__ = getattr(cls, "__post_init__", None)

    if enable_type_checking:

        def __post_init__(self):
            # do it first
            if original__post_init__ is not None:
                original__post_init__(self)

            # logger.info(f'__post_init__ sees {new_annotations}')
            for k, v in new_annotations.items():
                if is_ClassVar(v):
                    continue
                # logger.info(f' k = {k} v = {v}')
                if isinstance(v, type):
                    val = getattr(self, k)
                    # logger.info(f' k = {k} v = {v} val = {val}')
                    try:
                        if type(val).__name__ != v.__name__ and not isinstance(
                            val, v
                        ):  # pragma: no cover
                            msg = (
                                f'Expected field "{k}" to be a "{v.__name__}" '
                                f"but found {type(val).__name__}"
                            )
                            # warnings.warn(msg, stacklevel=3)
                            raise ValueError(msg)
                    except TypeError as e:  # pragma: no cover
                        msg = f"Cannot judge annotation of {k} (supposedly {v}."

                        if sys.version_info[:2] == (3, 6):
                            # FIXME: warn
                            continue
                        logger.error(msg)
                        raise TypeError(msg) from e

        # important: do it before dataclass
        setattr(cls2, "__post_init__", __post_init__)

    cls2.__annotations__ = new_annotations

    # logger.info('new annotations: %s' % new_annotations)
    if is_dataclass(cls):
        # note: need to have set new annotations
        # pprint('creating dataclass from %s' % cls2)
        doc = getattr(cls2, "__doc__", None)
        cls2 = dataclass(cls2, unsafe_hash=True)
        setattr(cls2, "__doc__", doc)
    else:
        # noinspection PyUnusedLocal
        def init_placeholder(self, *args, **kwargs):
            if args or kwargs:
                msg = (
                    f"Default constructor of {cls2.__name__} does not know what to do with "
                    f""
                    f""
                    f"arguments."
                )
                msg += f"\nargs: {args!r}\nkwargs: {kwargs!r}"
                msg += f"\nself: {self}"
                msg += f"\nself: {dir(type(self))}"
                msg += f"\nself: {type(self)}"
                raise NoConstructorImplemented(msg)

        if cls.__init__ == object.__init__:
            setattr(cls2, "__init__", init_placeholder)

    cls2.__module__ = cls.__module__
    setattr(cls2, "__name__", name2)
    qn = cls.__qualname__

    qn0, sep, _ = qn.rpartition(".")
    if not sep:
        sep = ""
    setattr(cls2, "__qualname__", qn0 + sep + name2)
    setattr(cls2, BINDINGS_ATT, bindings)
    setattr(cls2, GENERIC_ATT2, generic_att2_new)

    MakeTypeCache.cache[cache_key] = cls2

    # logger.info(f'started {cls}; hash is {cls.__hash__}')
    # logger.info(f'specialized {cls2}; hash is {cls2.__hash__}')
    return cls2
