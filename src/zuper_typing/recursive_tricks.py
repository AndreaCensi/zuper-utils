import typing
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from zuper_typing.annotations_tricks import (get_Callable_info, get_ClassVar_arg, get_ForwardRef_arg, get_Iterator_arg,
                                             get_List_arg, get_Optional_arg, get_Sequence_arg, get_Set_arg,
                                             get_TypeVar_name, get_Type_arg, get_Union_args, get_tuple_types,
                                             is_Callable, is_ClassVar, is_ForwardRef, is_Iterator, is_List, is_NewType,
                                             is_Optional, is_Sequence, is_Set, is_Tuple, is_Type, is_TypeVar, is_Union)
from zuper_typing.my_dict import (get_CustomList_arg, get_DictLike_args, get_SetLike_arg, is_CustomList, is_DictLike,
                                  is_SetLike, make_dict, make_list, make_set)


def get_name_without_brackets(name: str) -> str:
    if '[' in name:
        return name[:name.index('[')]
    else:
        return name


class NoConstructorImplemented(TypeError):
    pass


def get_default_attrs():
    return dict(Any=Any, Optional=Optional, Union=Union, Tuple=Tuple,
                List=List, Set=Set,
                Dict=Dict)


def replace_typevars(cls, *, bindings, symbols, already=None):
    if already is None:
        already = {}

    if cls is type:
        return type

    if id(cls) in already:
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
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols)
        if x == r:
            return cls
        return Type[r]
        # return type
    elif is_DictLike(cls):
        K0, V0 = get_DictLike_args(cls)
        K = replace_typevars(K0, bindings=bindings, already=already, symbols=symbols)
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols)
        # logger.debug(f'{K0} -> {K};  {V0} -> {V}')
        if (K0, V0) == (K, V):
            return cls
        return make_dict(K, V)
    elif is_SetLike(cls):
        V0 = get_SetLike_arg(cls)
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols)
        if V0 == V:
            return cls
        return make_set(V)
    elif is_CustomList(cls):
        V0 = get_CustomList_arg(cls)
        V = replace_typevars(V0, bindings=bindings, already=already, symbols=symbols)
        if V0 == V:
            return cls
        return make_list(V)
    # XXX NOTE: must go after CustomDict
    elif hasattr(cls, '__annotations__'):
        from zuper_typing.zeneric2 import make_type
        return make_type(cls, bindings)
    elif is_ClassVar(cls):
        x = get_ClassVar_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols)
        if x == r:
            return cls
        return typing.ClassVar[r]
    elif is_Iterator(cls):
        x = get_Iterator_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols)
        if x == r:
            return cls
        return typing.Iterator[r]
    elif is_Sequence(cls):
        x = get_Sequence_arg(cls)
        r = replace_typevars(x, bindings=bindings, already=already, symbols=symbols)
        if x == r:
            return cls

        return typing.Sequence[r]

    elif is_List(cls):
        arg = get_List_arg(cls)
        arg2 = replace_typevars(arg, bindings=bindings, already=already, symbols=symbols)
        if arg == arg2:
            return cls
        return typing.List[arg2]

    elif is_Optional(cls):
        x = get_Optional_arg(cls)
        x2 = replace_typevars(x, bindings=bindings, already=already, symbols=symbols)
        if x == x2:
            return cls
        return typing.Optional[x2]

    elif is_Union(cls):
        xs = get_Union_args(cls)
        ys = tuple(replace_typevars(_, bindings=bindings, already=already, symbols=symbols)
                   for _ in xs)
        if ys == xs:
            return cls
        return typing.Union[ys]
    elif is_Tuple(cls):

        xs = get_tuple_types(cls)
        ys = tuple(replace_typevars(_, bindings=bindings, already=already, symbols=symbols)
                   for _ in xs)
        if ys == xs:
            return cls
        return typing.Tuple[ys]
    elif is_Callable(cls):
        cinfo = get_Callable_info(cls)

        def f(_):
            return replace_typevars(_, bindings=bindings, already=already, symbols=symbols)

        cinfo2 = cinfo.replace(f)
        return cinfo2.as_callable()

    elif is_ForwardRef(cls):
        T = get_ForwardRef_arg(cls)
        return replace_typevars(T, bindings=bindings, already=already, symbols=symbols)
    else:
        # logger.debug(f'Nothing to do with {cls!r} {cls}')
        return cls


B = Dict[Any, Any]  # bug in Python 3.6
