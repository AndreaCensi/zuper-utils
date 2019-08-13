from dataclasses import is_dataclass
from typing import Dict, List, Optional, Tuple

# from zuper_ipce.conv_ipce_from_typelike import (eval_field)
# from zuper_ipce.conv_ipce_from_typelike import eval_just_string
from zuper_typing.annotations_tricks import (get_Dict_args, get_FixedTuple_args, get_List_arg, get_Optional_arg,
                                             get_Set_arg, get_Union_args, get_VarTuple_arg, is_Dict, is_FixedTuple,
                                             is_ForwardRef, is_List, is_Optional, is_Set, is_TupleLike, is_Union,
                                             is_VarTuple, make_Tuple, make_Union)
from zuper_typing.monkey_patching_typing import my_dataclass, original_dict_getitem
from zuper_typing.my_dict import (get_CustomDict_args, get_CustomList_arg, get_CustomSet_arg, is_CustomDict,
                                  is_CustomList, is_CustomSet, make_dict, make_list, make_set)


def resolve_all(T, globals_):
    """
        Returns either a type or a generic alias


    :return:
    """
    if isinstance(T, type):
        return T

    # if isinstance(T, str):
    #     T = eval_just_string(T, globals_)
    #     return T
    #
    # if is_ForwardRef(T):
    #     tn = get_ForwardRef_arg(T)
    #     return resolve_all(tn, globals_)

    if is_Optional(T):
        t = get_Optional_arg(T)
        t = resolve_all(t, globals_)
        return Optional[t]

    # logger.debug(f'no thing to do for {T}')
    return T


def recursive_type_subst(T, f, ignore=()):
    if T in ignore:
        # logger.info(f'ignoring {T} in {ignore}')
        return T
    r = lambda _: recursive_type_subst(_, f, ignore + (T,))
    if is_Optional(T):
        a = get_Optional_arg(T)
        a2 = r(a)
        if a == a2:
            return T
        # logger.info(f'Optional unchanged under {f.__name__}: {a} == {a2}')
        return Optional[a2]
    elif is_ForwardRef(T):
        return f(T)
    elif is_Union(T):
        ts0 = get_Union_args(T)
        ts = tuple(r(_) for _ in ts0)
        if ts0 == ts:
            # logger.info(f'Union unchanged under {f.__name__}: {ts0} == {ts}')
            return T
        return make_Union(*ts)
    elif is_TupleLike(T):
        if is_VarTuple(T):
            X = get_VarTuple_arg(T)
            X2 = r(X)
            if X == X2:
                return T
            return Tuple[X2, ...]
        elif is_FixedTuple(T):
            args = get_FixedTuple_args(T)
            ts = tuple(r(_) for _ in args)
            if args == ts:
                return T
            return make_Tuple(*ts)
        else:
            assert False
    elif is_Dict(T):
        K, V = get_Dict_args(T)
        K2, V2 = r(K), r(V)
        if (K, V) == (K2, V2):
            return T
        return original_dict_getitem((K, V))
    elif is_CustomDict(T):
        K, V = get_CustomDict_args(T)
        K2, V2 = r(K), r(V)
        if (K, V) == (K2, V2):
            return T
        return make_dict(K2, V2)
    elif is_List(T):
        V = get_List_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return List[V2]
    elif is_CustomList(T):
        V = get_CustomList_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_list(V2)
    elif is_Set(T):
        V = get_Set_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_set(V2)
    elif is_CustomSet(T):
        V = get_CustomSet_arg(T)
        V2 = r(V)
        if V == V2:
            return T
        return make_set(V2)
    elif is_dataclass(T):
        annotations = dict(getattr(T, '__annotations__', {}))
        annotations2 = {}
        nothing_changed = True
        for k, v0 in list(annotations.items()):
            v2 = r(v0)
            nothing_changed &= (v0 == v2)
            annotations2[k] = v2
        if nothing_changed:
            # logger.info(f'Union unchanged under {f.__name__}: {ts0} == {ts}')
            return T
        T2 = my_dataclass(type(T.__name__, (), {
              '__annotations__': annotations2,
              '__module__':      T.__module__,
              '__doc__':         getattr(T, '__doc__', None),
              '__qualname__':    getattr(T, '__qualname__')
              }))

        # from zuper_ipcl.debug_print_ import debug_print
        # logger.info(f'changed {T.__name__} into {debug_print(T2.__annotations__)}')

        return T2

    else:
        return f(T)
