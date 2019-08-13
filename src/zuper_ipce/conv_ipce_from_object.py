import datetime
from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple, Type

import cbor2
import numpy as np
from frozendict import frozendict

from zuper_commons.text import pretty_dict
from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike_ndarray
from zuper_typing.annotations_tricks import (get_Optional_arg, get_Union_args, get_VarTuple_arg, is_Any, is_Callable,
                                             is_ClassVar, is_Dict, is_List, is_Optional, is_Sequence, is_Set, is_Tuple,
                                             is_TupleLike, is_Union, is_VarTuple)
from zuper_typing.my_dict import (get_CustomDict_args, get_DictLike_args, get_ListLike_arg, get_SetLike_arg,
                                  is_CustomDict, is_DictLike, is_ListLike, is_SetLike)
from .assorted_recursive_type_subst import resolve_all
from .constants import GlobalsDict, HINTS_ATT, SCHEMA_ATT
from .ipce_spec import assert_canonical_ipce, sorted_dict_with_cbor_ordering
from .structures import FakeValues
from .types import IPCE
from .utils_text import get_sha256_base58


def ipce_from_object(ob, globals_: GlobalsDict = None, suggest_type=None, with_schema=True) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
    globals_ = globals_ or {}
    try:
        res = ipce_from_object_(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)
    except TypeError as e:
        msg = f'ipce_from_object() for type {type(ob)} failed.'
        raise TypeError(msg) from e

    # if isinstance(res, dict) and SCHEMA_ATT in res:
    #     schema = res[SCHEMA_ATT]
    #     if False:
    #         validate(res, schema)
    assert_canonical_ipce(res)
    return res


def ipce_from_object_(ob,
                      globals_: GlobalsDict,
                      with_schema: bool,
                      suggest_type: Type = None,
                      ) -> IPCE:
    if ob is None:
        return ob

    if is_Optional(suggest_type):
        T = get_Optional_arg(suggest_type)
        return ipce_from_object_(ob, globals_, with_schema, suggest_type=T)
    if is_Union(suggest_type):
        return ipce_from_object_union(ob, globals_, with_schema, suggest_type)
    if isinstance(ob, datetime.datetime):
        if not ob.tzinfo:
            msg = 'Cannot serialize dates without a timezone.'
            raise ValueError(msg)

    trivial = (bool, int, str, float, bytes, Decimal, datetime.datetime)
    if suggest_type in trivial:
        if not isinstance(ob, suggest_type):
            msg = f'Expected this to be a {suggest_type}, got {type(ob)}'
            raise TypeError(msg)
        return ob

    if isinstance(ob, trivial):
        return ob

    if isinstance(ob, list):
        return ipce_from_object_list(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, tuple):
        return ipce_from_object_tuple(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    from .conv_ipce_from_typelike import (ipce_from_typelike)
    if isinstance(ob, slice):
        return ipce_from_object_slice(ob, with_schema)

    if isinstance(ob, set):
        return ipce_from_object_set(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, (dict, frozendict)):
        return ipce_from_object_dict(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, type):
        return ipce_from_typelike(ob, globals_, processing={})

    if is_Any(ob) or is_List(ob) or is_Dict(ob) or is_Set(ob) or is_Tuple(ob) \
          or is_Callable(ob) or is_Union(ob) or is_Sequence(ob) or is_Optional(ob):
        # TODO: put more here
        return ipce_from_typelike(ob, globals_, processing={})

    if isinstance(ob, np.ndarray):
        return ipce_from_object_numpy(ob, with_schema)

    assert not isinstance(ob, type), ob
    if is_dataclass(ob):
        return ipce_from_object_dataclass_instance(ob, globals_, with_schema=with_schema, suggest_type=suggest_type)

    msg = f'I do not know a way to convert object of type {type(ob)} ({ob}).'
    raise NotImplementedError(msg)


def ipce_from_object_numpy(ob, with_schema) -> IPCE:
    from .numpy_encoding import ipce_from_numpy_array

    res = ipce_from_numpy_array(ob)
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_ndarray().schema
    return res


def ipce_from_object_slice(ob, with_schema):
    from .conv_ipce_from_typelike import (ipce_from_typelike_slice)
    res = {
          'start': ob.start,
          'step':  ob.step,
          'stop':  ob.stop
          }
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_slice().schema
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_union(ob, globals_, with_schema, suggest_type) -> IPCE:
    ts = get_Union_args(suggest_type)
    errors = []
    for Ti in ts:
        try:
            return ipce_from_object(ob, globals_=globals_, with_schema=with_schema,
                                    suggest_type=Ti)
        except BaseException as e:
            errors.append((Ti, e))

    msg = 'Cannot save union.'
    d = {'value': ob, 'errors': errors}
    raise TypeError(pretty_dict(msg, d))


def ipce_from_object_list(ob, globals_, suggest_type, with_schema: bool) -> IPCE:
    if suggest_type is not None:
        if suggest_type is object or is_Any(suggest_type):
            suggest_type_l = Any
        elif is_ListLike(suggest_type):
            suggest_type_l = get_ListLike_arg(suggest_type)
        else:
            msg = f'suggest_type = {suggest_type} does not make sense for a list'
            raise TypeError(msg)
    else:
        suggest_type_l = None
    return [ipce_from_object(_, globals_, suggest_type=suggest_type_l,
                             with_schema=with_schema) for _ in ob]


def ipce_from_object_tuple(ob: tuple, globals_, suggest_type, with_schema: bool) -> IPCE:
    if suggest_type is not None:
        if suggest_type is object or is_Any(suggest_type):
            suggest_type_l = [Any] * len(ob)
        elif is_TupleLike(suggest_type):
            if is_VarTuple(suggest_type):
                suggest_type_l = [get_VarTuple_arg(suggest_type)] * len(ob)
            else:
                suggest_type_l = [None] * len(ob)
        else:
            msg = f'suggest_type = {suggest_type} does not make sense for a tuple'
            raise TypeError(msg)
    else:
        suggest_type_l = [None] * len(ob)
    res = []
    for i, (_, T) in enumerate(zip(ob, suggest_type_l)):
        x = ipce_from_object(_, globals_, suggest_type=T, with_schema=with_schema)
        res.append(x)

    return res


def ipce_from_object_dataclass_instance(ob, globals_, with_schema: bool, suggest_type: Optional[type]) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    from .conv_ipce_from_typelike import ipce_from_typelike
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(T, globals_)

    globals_[T.__name__] = T
    hints = {}

    for f in fields(ob):
        k = f.name
        suggest_type = f.type
        if not hasattr(ob, k):  # pragma: no cover
            assert False, (ob, k)
        v = getattr(ob, k)

        try:
            suggest_type = resolve_all(suggest_type, globals_)

            # if is_ClassVar(suggest_type):
            #     continue

            if v is None:
                if is_Optional(suggest_type):
                    continue

            if is_Optional(suggest_type):
                suggest_type = get_Optional_arg(suggest_type)

            if f.default == v:
                continue
            if hasattr(T, k):  # XXX: default
                if getattr(T, k) == v:
                    continue
            res[k] = ipce_from_object(v, globals_,
                                      suggest_type=suggest_type, with_schema=with_schema)
            if with_schema and isinstance(v, (list, tuple)) and is_Any(f.type):
                hints[k] = ipce_from_typelike(type(v), globals_)

        except BaseException as e:
            msg = f'Obtained {type(e).__name__} while serializing attribute {k}  of type {type(v)}.'
            msg += f'\nThe schema for {type(ob)} says that it should be of type {f.type}.'

            msg += '\n' + f'{v}'
            raise ValueError(msg) from e
    if hints:
        res[HINTS_ATT] = hints
    res = sorted_dict_with_cbor_ordering(res)

    return res


def ipce_from_object_dict(ob: dict, globals_: GlobalsDict, suggest_type: Optional[type], with_schema: bool):
    # logger.info(f'dict_to_ipce suggest_type: {suggest_type}')
    # assert suggest_type is not None
    assert not is_Optional(suggest_type), suggest_type
    res = {}
    suggest_type, K, V = get_best_type_for_serializing_dict(ob, suggest_type)
    # logger.info(f'Using suggest_type for dict = {suggest_type}')
    from .conv_ipce_from_typelike import ipce_from_typelike
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(suggest_type, globals_)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(v, globals_, suggest_type=V, with_schema=with_schema)
    elif isinstance(K, type) and issubclass(K, int):
        for k, v in ob.items():
            res[str(k)] = ipce_from_object(v, globals_, suggest_type=V, with_schema=with_schema)
    else:
        FV = FakeValues[K, V]

        for k, v in ob.items():
            kj = ipce_from_object(k, globals_)
            h = get_sha256_base58(cbor2.dumps(kj)).decode('ascii')
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_, with_schema=with_schema)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_set(ob: set, globals_: GlobalsDict, suggest_type: Optional[type], with_schema: bool):
    if suggest_type is not None and is_SetLike(suggest_type):
        V = get_SetLike_arg(suggest_type)
    else:
        V = None

    res = {}

    from .conv_ipce_from_typelike import ipce_from_typelike
    if with_schema:
        if suggest_type is not None and is_SetLike(suggest_type):
            res[SCHEMA_ATT] = ipce_from_typelike(suggest_type, globals_)
        else:
            res[SCHEMA_ATT] = ipce_from_typelike(type(ob), globals_)

    for v in ob:
        vj = ipce_from_object(v, globals_, with_schema=with_schema,
                              suggest_type=V)
        h = 'set:' + get_sha256_base58(cbor2.dumps(vj)).decode('ascii')

        res[h] = vj

    res = sorted_dict_with_cbor_ordering(res)
    return res


def guess_type_for_naked_dict(ob: dict) -> Tuple[type, type]:
    if not ob:
        return Any, Any
    type_values = tuple(type(_) for _ in ob.values())
    type_keys = tuple(type(_) for _ in ob.keys())
    K = Any
    if len(set(type_keys)) == 1:
        K = type_keys[0]

    V = Any
    if len(set(type_values)) == 1:
        V = type_values[0]

    return K, V


def get_best_type_for_serializing_dict(ob: dict, suggest_type: Optional[type]) -> Tuple[type, type, type]:
    T = type(ob)
    if is_CustomDict(T):
        K, V = get_CustomDict_args(T)
    elif is_DictLike(suggest_type):
        K, V = get_DictLike_args(suggest_type)
    elif (suggest_type is None) or is_Any(suggest_type):
        K, V = guess_type_for_naked_dict(ob)
    else:  # pragma: no cover
        assert False, suggest_type

    suggest_type = Dict[K, V]
    return suggest_type, K, V
