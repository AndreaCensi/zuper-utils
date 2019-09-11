from datetime import datetime
from decimal import Decimal
from numbers import Number
from typing import (
    Any,
    cast,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from zuper_typing.literal import is_Literal
from .aliases import TypeLike
from .annotations_tricks import (
    get_Callable_info,
    get_ClassVar_arg,
    get_FixedTuple_args,
    get_ForwardRef_arg,
    get_Iterator_arg,
    get_List_arg,
    get_Optional_arg,
    get_Sequence_arg,
    get_Type_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_FixedTuple,
    is_FixedTuple_canonical,
    is_ForwardRef,
    is_Iterator,
    is_List,
    is_List_canonical,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_Type,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    is_VarTuple_canonical,
    make_Tuple,
    make_Union,
    make_VarTuple,
)
from .my_dict import (
    CustomList,
    get_CustomList_arg,
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_CustomList,
    is_DictLike,
    is_DictLike_canonical,
    is_ListLike,
    is_ListLike_canonical,
    is_SetLike,
    is_SetLike_canonical,
    make_dict,
    make_list,
    make_set,
)
from .my_intersection import get_Intersection_args, is_Intersection, make_Intersection
from .uninhabited import is_Uninhabited


def get_name_without_brackets(name: str) -> str:
    if "[" in name:
        return name[: name.index("[")]
    else:
        return name


class NoConstructorImplemented(TypeError):
    pass


def get_default_attrs():
    return dict(
        Any=Any,
        Optional=Optional,
        Union=Union,
        Tuple=Tuple,
        List=List,
        Set=Set,
        Dict=Dict,
    )


def canonical(typelike: TypeLike) -> TypeLike:
    return replace_typevars(typelike, bindings={}, symbols={}, make_canonical=True)


def replace_typevars(
    cls: TypeLike,
    *,
    bindings: Dict[Any, TypeLike],
    symbols: Dict[str, TypeLike],
    make_canonical: bool = False,
) -> TypeLike:
    from .logging import logger

    r = lambda _: replace_typevars(_, bindings=bindings, symbols=symbols)
    if cls is type:
        return type

    if hasattr(cls, "__name__") and cls.__name__ in symbols:
        return symbols[cls.__name__]
    elif (isinstance(cls, str) or is_TypeVar(cls)) and cls in bindings:
        return bindings[cls]
    elif hasattr(cls, "__name__") and cls.__name__.startswith("Placeholder"):
        return cls
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
        g0 = dict(g)
        try:
            return eval(cls, g)
        except NameError as e:
            msg = f"Cannot resolve {cls!r}\ng: {list(g0)}"
            # msg += 'symbols: {list(g0)'
            raise NameError(msg) from e
    elif is_NewType(cls):
        return cls
    elif is_Type(cls):
        x = get_Type_arg(cls)
        r = r(x)
        if x == r:
            return cls
        return Type[r]
        # return type
    elif is_DictLike(cls):
        is_canonical = is_DictLike_canonical(cls)
        K0, V0 = get_DictLike_args(cls)
        K = r(K0)
        V = r(V0)
        # logger.debug(f'{K0} -> {K};  {V0} -> {V}')
        if (K0, V0) == (K, V) and (is_canonical or not make_canonical):
            return cls
        res = make_dict(K, V)
        return res
    elif is_SetLike(cls):
        is_canonical = is_SetLike_canonical(cls)
        V0 = get_SetLike_arg(cls)
        V = r(V0)
        if V0 == V and (is_canonical or not make_canonical):
            return cls
        return make_set(V)
    elif is_CustomList(cls):
        cls = cast(Type[CustomList], cls)
        V0 = get_CustomList_arg(cls)
        V = r(V0)
        if V0 == V:
            return cls
        return make_list(V)
    elif is_List(cls):
        arg = get_List_arg(cls)
        is_canonical = is_List_canonical(cls)
        arg2 = r(arg)
        if arg == arg2 and (is_canonical or not make_canonical):
            return cls
        return List[arg2]
    elif is_ListLike(cls):
        cls = cast(Type[List], cls)
        arg = get_ListLike_arg(cls)
        is_canonical = is_ListLike_canonical(cls)
        arg2 = r(arg)
        if arg == arg2 and (is_canonical or not make_canonical):
            return cls
        return make_list(arg2)
    # XXX NOTE: must go after CustomDict
    elif hasattr(cls, "__annotations__"):
        from zuper_typing.zeneric2 import make_type

        cls2 = make_type(cls, bindings=bindings, symbols=symbols)

        # logger.info(f'old cls: {cls.__annotations__}')
        # logger.info(f'new cls2: {cls2.__annotations__}')
        return cls2
    elif is_ClassVar(cls):
        is_canonical = True  # XXXis_ClassVar_canonical(cls)
        x = get_ClassVar_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls
        return ClassVar[r]
    elif is_Iterator(cls):
        is_canonical = True  # is_Iterator_canonical(cls)
        x = get_Iterator_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls
        return Iterator[r]
    elif is_Sequence(cls):
        is_canonical = True  # is_Sequence_canonical(cls)
        x = get_Sequence_arg(cls)
        r = r(x)
        if x == r and (is_canonical or not make_canonical):
            return cls

        return Sequence[r]

    elif is_Optional(cls):
        is_canonical = True  # is_Optional_canonical(cls)
        x = get_Optional_arg(cls)
        x2 = r(x)
        if x == x2 and (is_canonical or not make_canonical):
            return cls
        return Optional[x2]

    elif is_Union(cls):
        xs = get_Union_args(cls)
        is_canonical = True  # is_Union_canonical(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs and (is_canonical or not make_canonical):
            return cls
        return make_Union(*ys)
    elif is_Intersection(cls):
        xs = get_Intersection_args(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs:
            return cls
        return make_Intersection(ys)
    elif is_VarTuple(cls):

        is_canonical = is_VarTuple_canonical(cls)
        X = get_VarTuple_arg(cls)
        Y = r(X)
        if X == Y and (is_canonical or not make_canonical):
            return cls
        return make_VarTuple(Y)
    elif is_FixedTuple(cls):
        is_canonical = is_FixedTuple_canonical(cls)
        xs = get_FixedTuple_args(cls)
        ys = tuple(r(_) for _ in xs)
        if ys == xs and (is_canonical or not make_canonical):
            return cls
        return make_Tuple(*ys)

    elif is_Callable(cls):
        cinfo = get_Callable_info(cls)

        cinfo2 = cinfo.replace(r)
        return cinfo2.as_callable()

    elif is_ForwardRef(cls):
        T = get_ForwardRef_arg(cls)
        if T in symbols:
            return r(symbols[T])
        else:
            logger.warning(f"could not resolve {cls}")
            return cls

    elif cls in (
        int,
        bool,
        float,
        Decimal,
        datetime,
        str,
        bytes,
        Number,
        type(None),
        object,
    ):
        return cls
    elif is_Any(cls):
        return cls
    elif is_Uninhabited(cls):
        return cls
    elif is_Literal(cls):
        return cls
    elif isinstance(cls, type):

        # logger.warning(f"extraneous class {cls}")
        return cls
    # elif is_Literal(cls):
    #     return cls
    else:
        raise NotImplementedError(cls)
        # logger.debug(f'Nothing to do with {cls!r} {cls}')
        # return cls


B = Dict[Any, Any]  # bug in Python 3.6
