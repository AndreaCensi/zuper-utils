import datetime
import traceback
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from typing import cast, Dict, List, Optional, Tuple, Type, TypeVar, Set

import cbor2
import numpy as np
from frozendict import frozendict

X = TypeVar("X")
from zuper_typing.annotations_tricks import (
    get_Optional_arg,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Optional,
    is_SpecialForm,
    is_TupleLike,
    is_Union,
    is_VarTuple,
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
    CustomDict,
)
from .constants import GlobalsDict, HINTS_ATT, SCHEMA_ATT, IESO
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
    ieso: Optional[IESO] = None,
    # with_schema: bool = True,
) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
    if ieso is None:
        ieso = IESO(with_schema=True)
    if globals_ is None:
        globals_ = {}
    try:
        res = ipce_from_object_(ob, suggest_type, globals_=globals_, ieso=ieso)
    except TypeError as e:
        msg = "ipce_from_object() for type @t failed."
        raise ZTypeError(msg, ob=ob, T=type(ob)) from e

    assert_canonical_ipce(res)
    return res


def is_unconstrained(t: TypeLike):
    assert t is not None
    return is_Any(t) or (t is object)


def ipce_from_object_(
    ob: object, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO
) -> IPCE:
    unconstrained = is_unconstrained(st)
    if ob is None:
        if unconstrained or (st is type(None)) or is_Optional(st):
            return ob
        else:
            msg = f"ob is None but suggest_type is @suggest_type"
            raise ZTypeError(msg, suggest_type=st)

    if is_Optional(st):
        assert ob is not None  # from before
        T = get_Optional_arg(st)
        return ipce_from_object_(ob, T, globals_=globals_, ieso=ieso)

    if is_Union(st):
        return ipce_from_object_union(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, datetime.datetime):
        if not ob.tzinfo:
            msg = "Cannot serialize dates without a timezone."
            raise ZValueError(msg, ob=ob)

    trivial = (bool, int, str, float, bytes, Decimal, datetime.datetime)
    if st in trivial:
        if not isinstance(ob, st):
            msg = "Expected this to be @suggest_type."
            raise ZTypeError(msg, suggest_type=st, T=type(ob))
        return ob

    if isinstance(ob, trivial):
        return ob

    if isinstance(ob, list):
        return ipce_from_object_list(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, tuple):
        return ipce_from_object_tuple(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, slice):
        return ipce_from_object_slice(ob, ieso=ieso)

    if isinstance(ob, set):
        return ipce_from_object_set(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, (dict, frozendict)):
        return ipce_from_object_dict(ob, st, globals_=globals_, ieso=ieso)

    if isinstance(ob, type):
        return ipce_from_typelike(ob, globals0=globals_, processing={}, ieso=ieso)

    if is_SpecialForm(ob):
        ob = cast(TypeLike, ob)
        return ipce_from_typelike(ob, globals0=globals_, processing={}, ieso=ieso)

    if isinstance(ob, np.ndarray):
        return ipce_from_object_numpy(ob, ieso=ieso)

    assert not isinstance(ob, type), ob
    if is_dataclass(ob):
        return ipce_from_object_dataclass_instance(ob, globals_=globals_, ieso=ieso)

    msg = "I do not know a way to convert object @ob of type @T."
    raise ZNotImplementedError(msg, ob=ob, T=type(ob))


def ipce_from_object_numpy(ob, *, ieso: IESO) -> IPCE:
    from .numpy_encoding import ipce_from_numpy_array

    res = ipce_from_numpy_array(ob)
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_ndarray().schema
    return res


def ipce_from_object_slice(ob, *, ieso: IESO):
    from .conv_ipce_from_typelike import ipce_from_typelike_slice

    res = {"start": ob.start, "step": ob.step, "stop": ob.stop}
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike_slice(ieso=ieso).schema
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_union(ob: object, st: TypeLike, *, globals_, ieso: IESO) -> IPCE:
    ts = get_Union_args(st)
    errors = []
    for Ti in ts:
        try:
            return ipce_from_object(ob, Ti, globals_=globals_, ieso=ieso)
        except BaseException:
            errors.append((Ti, traceback.format_exc()))

    msg = "Cannot save union."
    raise ZTypeError(msg, suggest_type=st, value=ob, errors=errors)
    # errors=errors)


def ipce_from_object_list(
    ob, suggest_type: TypeLike, *, globals_: dict, ieso: IESO
) -> IPCE:
    assert suggest_type is not None

    if is_unconstrained(suggest_type):
        suggest_type_l = object
    elif is_ListLike(suggest_type):
        T = cast(Type[List], suggest_type)
        suggest_type_l = get_ListLike_arg(T)
    else:
        msg = "suggest_type does not make sense for a list"
        raise ZTypeError(msg, suggest_type=suggest_type)

    def rec(x: X) -> X:
        return ipce_from_object(x, suggest_type_l, globals_=globals_, ieso=ieso)

    return [rec(_) for _ in ob]


def ipce_from_object_tuple(
    ob: tuple, suggest_type: TypeLike, *, globals_, ieso: IESO
) -> IPCE:
    n = len(ob)
    if is_unconstrained(suggest_type):
        suggest_type_l = [object] * n
    elif is_TupleLike(suggest_type):
        if is_VarTuple(suggest_type):
            suggest_type_l = [get_VarTuple_arg(suggest_type)] * n
        else:
            suggest_type_l = [object] * n
    else:
        msg = "suggest_type does not make sense for a tuple."
        raise ZTypeError(msg, suggest_type=suggest_type)

    res = []
    for _, T in zip(ob, suggest_type_l):
        x = ipce_from_object(_, T, globals_=globals_, ieso=ieso)
        res.append(x)

    return res


def ipce_from_object_dataclass_instance(ob: dataclass, *, globals_, ieso: IESO) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(T, globals0=globals_, ieso=ieso)

    globals_[T.__name__] = T
    hints = {}

    for f in fields(ob):
        k = f.name
        fst = f.type
        if not hasattr(ob, k):  # pragma: no cover
            assert False, (ob, k)
        v = getattr(ob, k)

        try:

            if f.default == v:
                continue

            res[k] = ipce_from_object(v, fst, globals_=globals_, ieso=ieso)
            needs_schema = isinstance(v, (list, tuple))
            if ieso.with_schema and needs_schema and is_unconstrained(f.type):
                hints[k] = ipce_from_typelike(type(v), globals0=globals_, ieso=ieso)

        except BaseException as e:
            msg = (
                f"Could not serialie an object of type {T.__name__!r}. Problem "
                f"occurred with the attribute {k!r}. It is supposed to be of type @expected "
                f" but found @found."
            )
            raise ZValueError(msg, expected=f.type, found=type(ob)) from e
    if hints:
        res[HINTS_ATT] = hints
    res = sorted_dict_with_cbor_ordering(res)

    return res


def ipce_from_object_dict(
    ob: dict, suggest_type: Optional[TypeLike], *, globals_: GlobalsDict, ieso: IESO
):
    assert not is_Optional(suggest_type), suggest_type
    res = {}
    suggest_type, K, V = get_type_for_dict_ser(ob, suggest_type)

    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(suggest_type, globals0=globals_, ieso=ieso)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(v, globals_=globals_, suggest_type=V, ieso=ieso)
    elif isinstance(K, type) and issubclass(K, int):
        for k, v in ob.items():
            res[str(k)] = ipce_from_object(
                v, globals_=globals_, suggest_type=V, ieso=ieso
            )
    else:
        FV = FakeValues[K, V]

        for k, v in ob.items():
            kj = ipce_from_object(k, globals_=globals_)
            h = get_sha256_base58(cbor2.dumps(kj)).decode("ascii")
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_=globals_, ieso=ieso)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_object_set(ob: set, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO):
    from .conv_ipce_from_typelike import ipce_from_typelike

    res = {}

    if is_SetLike(st):
        st = cast(Type[Set], st)
        V = get_SetLike_arg(st)
        if ieso.with_schema:
            res[SCHEMA_ATT] = ipce_from_typelike(st, globals0=globals_, ieso=ieso)
    else:
        V = object
        if ieso.with_schema:
            res[SCHEMA_ATT] = ipce_from_typelike(type(ob), globals0=globals_, ieso=ieso)

    for v in ob:
        vj = ipce_from_object(v, globals_=globals_, ieso=ieso, suggest_type=V)
        h = "set:" + get_sha256_base58(cbor2.dumps(vj)).decode("ascii")

        res[h] = vj

    res = sorted_dict_with_cbor_ordering(res)
    return res


def guess_type_for_naked_dict(ob: dict) -> Tuple[type, type]:
    if not ob:
        return object, object
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


def get_type_for_dict_ser(
    ob: dict, st: TypeLike
) -> Tuple[TypeLike, TypeLike, TypeLike]:
    """ Gets the type to use to serialize a dict.
        Returns Dict[K, V], K, V
    """
    T = type(ob)
    if is_CustomDict(T):
        # if it has the type information, then go for it
        T = cast(Type[CustomDict], T)
        K, V = get_CustomDict_args(T)
    elif is_DictLike(st):
        # There was a suggestion of Dict-like
        st = cast(Type[Dict], st)
        K, V = get_DictLike_args(st)
    elif is_unconstrained(st):
        # Guess from the dictionary itself
        K, V = guess_type_for_naked_dict(ob)
    else:  # pragma: no cover
        assert False, st

    suggest_type = Dict[K, V]
    return suggest_type, K, V
