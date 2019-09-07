import datetime
import traceback
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from typing import Any, cast, Dict, List, Optional, Tuple, Type

import cbor2
import numpy as np
from frozendict import frozendict

from zuper_typing.annotations_tricks import (
    get_Optional_arg,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_Dict,
    is_List,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_Set,
    is_Tuple,
    is_TupleLike,
    is_Union,
    is_VarTuple,
    is_SpecialForm,
)
from zuper_typing.exceptions import ZNotImplementedError, ZTypeError, ZValueError
from zuper_typing.my_dict import (
    get_CustomDict_args,
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_CustomDict,
    is_DictLike,
    is_ListLike,
    is_SetLike,
)
from .constants import GlobalsDict, HINTS_ATT, SCHEMA_ATT
from .conv_ipce_from_typelike import ipce_from_typelike, ipce_from_typelike_ndarray
from .ipce_spec import assert_canonical_ipce, sorted_dict_with_cbor_ordering
from .structures import FakeValues
from .types import IPCE, TypeLike
from .utils_text import get_sha256_base58


def ipce_from_object(
    ob: object,
    suggest_type: TypeLike = object,
    *,
    globals_: GlobalsDict = None,
    with_schema: bool = True,
) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
    if globals_ is None:
        globals_ = {}
    try:
        res = ipce_from_object_(
            ob, suggest_type, globals_=globals_, with_schema=with_schema
        )
    except TypeError as e:
        msg = "ipce_from_object() for type @t failed."
        raise ZTypeError(msg, ob=ob, T=type(ob)) from e

    assert_canonical_ipce(res)
    return res


def is_unconstrained(t: TypeLike):
    assert t is not None
    return is_Any(t) or (t is object)


def ipce_from_object_(
    ob: object, suggest_type: TypeLike, *, globals_: GlobalsDict, with_schema: bool
) -> IPCE:
    unconstrained = is_unconstrained(suggest_type)
    if ob is None:
        if unconstrained or (suggest_type is type(None)) or is_Optional(suggest_type):
            return ob
        else:
            raise ZTypeError(
                f"ob is None but suggest_type is @suggest_type",
                suggest_type=suggest_type,
            )

    if is_Optional(suggest_type):
        assert ob is not None  # from before
        T = get_Optional_arg(suggest_type)
        return ipce_from_object_(
            ob, suggest_type=T, globals_=globals_, with_schema=with_schema
        )

    if is_Union(suggest_type):
        return ipce_from_object_union(
            ob, suggest_type=suggest_type, globals_=globals_, with_schema=with_schema
        )

    if isinstance(ob, datetime.datetime):
        if not ob.tzinfo:
            msg = "Cannot serialize dates without a timezone."
            raise ZValueError(msg, ob=ob)

    trivial = (bool, int, str, float, bytes, Decimal, datetime.datetime)
    if suggest_type in trivial:
        if not isinstance(ob, suggest_type):
            msg = "Expected this to be @suggest_type."
            raise ZTypeError(msg, suggest_type=suggest_type, T=type(ob))
        return ob

    if isinstance(ob, trivial):
        return ob

    if isinstance(ob, list):
        return ipce_from_object_list(
            ob, globals_=globals_, suggest_type=suggest_type, with_schema=with_schema
        )

    if isinstance(ob, tuple):
        return ipce_from_object_tuple(
            ob, suggest_type, globals_=globals_, with_schema=with_schema
        )

    if isinstance(ob, slice):
        return ipce_from_object_slice(ob, with_schema=with_schema)

    if isinstance(ob, set):
        return ipce_from_object_set(
            ob, suggest_type, globals_=globals_, with_schema=with_schema
        )

    if isinstance(ob, (dict, frozendict)):
        return ipce_from_object_dict(
            ob, suggest_type, globals_=globals_, with_schema=with_schema
        )

    if isinstance(ob, type):
        return ipce_from_typelike(ob, globals0=globals_, processing={})

    if is_SpecialForm(ob):
        return ipce_from_typelike(ob, globals0=globals_, processing={})

    if isinstance(ob, np.ndarray):
        return ipce_from_object_numpy(ob, with_schema=with_schema)

    assert not isinstance(ob, type), ob
    if is_dataclass(ob):
        return ipce_from_object_dataclass_instance(
            ob, suggest_type, globals_=globals_, with_schema=with_schema
        )

    msg = "I do not know a way to convert object @ob of type @T."
    raise ZNotImplementedError(msg, ob=ob, T=type(ob))


def ipce_from_object_numpy(ob, *, with_schema) -> IPCE:
    from .numpy_encoding import ipce_from_numpy_array

    res = ipce_from_numpy_array(ob)
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_ndarray().schema
    return res


def ipce_from_object_slice(ob, *, with_schema):
    from .conv_ipce_from_typelike import ipce_from_typelike_slice

    res = {"start": ob.start, "step": ob.step, "stop": ob.stop}
    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_slice().schema
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_union(
    ob: object, suggest_type: TypeLike, *, globals_, with_schema
) -> IPCE:
    ts = get_Union_args(suggest_type)
    errors = []
    for Ti in ts:
        try:
            return ipce_from_object(
                ob, globals_=globals_, with_schema=with_schema, suggest_type=Ti
            )
        except BaseException:
            errors.append((Ti, traceback.format_exc()))

    msg = "Cannot save union."
    raise ZTypeError(msg, suggest_type=suggest_type, value=ob)
    # errors=errors)


def ipce_from_object_list(
    ob, suggest_type: TypeLike, *, globals_: dict, with_schema: bool
) -> IPCE:
    assert suggest_type is not None

    if suggest_type is object or is_Any(suggest_type):
        suggest_type_l = object
    elif is_ListLike(suggest_type):
        T = cast(Type[List], suggest_type)
        suggest_type_l = get_ListLike_arg(T)
    else:
        msg = "suggest_type does not make sense for a list"
        raise ZTypeError(msg, suggest_type=suggest_type)

    return [
        ipce_from_object(
            _, suggest_type=suggest_type_l, globals_=globals_, with_schema=with_schema
        )
        for _ in ob
    ]


def ipce_from_object_tuple(
    ob: tuple, suggest_type: TypeLike, *, globals_, with_schema: bool
) -> IPCE:

    if suggest_type is object or is_Any(suggest_type):
        suggest_type_l = [object] * len(ob)
    elif is_TupleLike(suggest_type):
        if is_VarTuple(suggest_type):
            suggest_type_l = [get_VarTuple_arg(suggest_type)] * len(ob)
        else:
            suggest_type_l = [object] * len(ob)
    else:
        msg = "suggest_type does not make sense for a tuple."
        raise ZTypeError(msg, suggest_type=suggest_type)

    res = []
    for i, (_, T) in enumerate(zip(ob, suggest_type_l)):
        x = ipce_from_object(
            _, globals_=globals_, suggest_type=T, with_schema=with_schema
        )
        res.append(x)

    return res


def ipce_from_object_dataclass_instance(
    ob: dataclass, suggest_type: Optional[type], *, globals_, with_schema: bool
) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    from .conv_ipce_from_typelike import ipce_from_typelike

    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(T, globals0=globals_)

    globals_[T.__name__] = T
    hints = {}

    for f in fields(ob):
        k = f.name
        suggest_type = f.type
        if not hasattr(ob, k):  # pragma: no cover
            assert False, (ob, k)
        v = getattr(ob, k)

        try:

            if f.default == v:
                continue

            res[k] = ipce_from_object(
                v, globals_=globals_, suggest_type=suggest_type, with_schema=with_schema
            )
            if with_schema and isinstance(v, (list, tuple)) and is_Any(f.type):
                hints[k] = ipce_from_typelike(type(v), globals0=globals_)

        except BaseException as e:
            msg = (
                f"Obtained {type(e).__name__} while serializing an object of type {T.__name__}. Problem "
                f"occurred with attribute "
                f"'{k}' of type"
                f" {type(v)}."
            )
            msg += (
                f"\nThe schema for {type(ob)} says that it should be of type {f.type}."
            )
            raise ZValueError(msg, type_=f.type) from e
    if hints:
        res[HINTS_ATT] = hints
    res = sorted_dict_with_cbor_ordering(res)

    return res


def ipce_from_object_dict(
    ob: dict,
    suggest_type: Optional[TypeLike],
    *,
    globals_: GlobalsDict,
    with_schema: bool,
):
    assert not is_Optional(suggest_type), suggest_type
    res = {}
    suggest_type, K, V = get_best_type_for_serializing_dict(ob, suggest_type)

    from .conv_ipce_from_typelike import ipce_from_typelike

    if with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(suggest_type, globals0=globals_)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(
                v, globals_=globals_, suggest_type=V, with_schema=with_schema
            )
    elif isinstance(K, type) and issubclass(K, int):
        for k, v in ob.items():
            res[str(k)] = ipce_from_object(
                v, globals_=globals_, suggest_type=V, with_schema=with_schema
            )
    else:
        FV = FakeValues[K, V]

        for k, v in ob.items():
            kj = ipce_from_object(k, globals_=globals_)
            h = get_sha256_base58(cbor2.dumps(kj)).decode("ascii")
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_=globals_, with_schema=with_schema)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_set(
    ob: set, suggest_type: Optional[type], *, globals_: GlobalsDict, with_schema: bool
):
    if suggest_type is not None and is_SetLike(suggest_type):
        V = get_SetLike_arg(suggest_type)
    else:
        V = object

    res = {}

    from .conv_ipce_from_typelike import ipce_from_typelike

    if with_schema:
        if suggest_type is not None and is_SetLike(suggest_type):
            res[SCHEMA_ATT] = ipce_from_typelike(suggest_type, globals0=globals_)
        else:
            res[SCHEMA_ATT] = ipce_from_typelike(type(ob), globals0=globals_)

    for v in ob:
        vj = ipce_from_object(
            v, globals_=globals_, with_schema=with_schema, suggest_type=V
        )
        h = "set:" + get_sha256_base58(cbor2.dumps(vj)).decode("ascii")

        res[h] = vj

    res = sorted_dict_with_cbor_ordering(res)
    return res


def guess_type_for_naked_dict(ob: dict) -> Tuple[type, type]:
    if not ob:
        return Any, Any
    type_values = tuple(type(_) for _ in ob.values())
    type_keys = tuple(type(_) for _ in ob.keys())

    if len(set(type_keys)) == 1:
        K = type_keys[0]
    else:
        K = object

    if len(set(type_values)) == 1:
        V = type_values[0]
    else:
        V = object
    return K, V


def get_best_type_for_serializing_dict(
    ob: dict, suggest_type: Optional[type]
) -> Tuple[type, type, type]:
    T = type(ob)
    if is_CustomDict(T):
        K, V = get_CustomDict_args(T)
    elif is_DictLike(suggest_type):
        K, V = get_DictLike_args(suggest_type)
    elif is_unconstrained(suggest_type):
        K, V = guess_type_for_naked_dict(ob)
    else:  # pragma: no cover
        assert False, suggest_type

    suggest_type = Dict[K, V]
    return suggest_type, K, V
