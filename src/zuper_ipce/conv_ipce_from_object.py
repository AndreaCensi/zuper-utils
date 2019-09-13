import datetime
import traceback
from dataclasses import dataclass, Field, fields, is_dataclass, MISSING
from decimal import Decimal
from typing import cast, Dict, Iterator, Optional, Set, TypeVar

import numpy as np
from frozendict import frozendict

from zuper_ipce.guesses import (
    get_dict_type_suggestion,
    get_list_type_suggestion,
    get_set_type_suggestion,
    get_tuple_type_suggestion,
)
from zuper_ipce.types import is_unconstrained
from zuper_typing.my_dict import make_dict

X = TypeVar("X")
from zuper_typing.annotations_tricks import (
    get_Optional_arg,
    get_Union_args,
    is_Optional,
    is_SpecialForm,
    is_Union,
)
from zuper_typing.exceptions import ZNotImplementedError, ZTypeError, ZValueError
from .constants import GlobalsDict, HINTS_ATT, SCHEMA_ATT, IESO, IPCE_PASS_THROUGH
from .conv_ipce_from_typelike import ipce_from_typelike, ipce_from_typelike_ndarray
from .ipce_spec import assert_canonical_ipce, sorted_dict_cbor_ord
from .structures import FakeValues
from .types import IPCE, TypeLike


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
            raise ZTypeError(msg, st=st, ob=ob, T=type(ob))
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
    res = sorted_dict_cbor_ord(res)
    return res


def ipce_from_object_union(ob: object, st: TypeLike, *, globals_, ieso: IESO) -> IPCE:
    ts = get_Union_args(st)
    errors = []
    for Ti in ts:
        try:
            return ipce_from_object(ob, Ti, globals_=globals_, ieso=ieso)
        except IPCE_PASS_THROUGH:
            raise
        except BaseException:
            errors.append((Ti, traceback.format_exc()))

    msg = "Cannot save union."
    raise ZTypeError(msg, suggest_type=st, value=ob, errors=errors)


def ipce_from_object_list(ob, st: TypeLike, *, globals_: dict, ieso: IESO) -> IPCE:
    assert st is not None

    V = get_list_type_suggestion(ob, st)

    def rec(x: X) -> X:
        return ipce_from_object(x, V, globals_=globals_, ieso=ieso)

    return [rec(_) for _ in ob]


def ipce_from_object_tuple(ob: tuple, st: TypeLike, *, globals_, ieso: IESO) -> IPCE:
    ts = get_tuple_type_suggestion(ob, st)

    res = []
    for _, T in zip(ob, ts):
        x = ipce_from_object(_, T, globals_=globals_, ieso=ieso)
        res.append(x)

    return res


@dataclass
class IterAtt:
    attr: str
    T: TypeLike
    value: object


def same_as_default(f: Field, value: object) -> bool:
    if f.default != MISSING:
        return f.default == value
    elif f.default_factory != MISSING:
        default = f.default_factory()
        return default == value
    else:
        return False


def iterate_resolved_type_values_without_default(x: dataclass) -> Iterator[IterAtt]:
    for f in fields(type(x)):
        k = f.name
        v0 = getattr(x, k)

        if same_as_default(f, v0):
            continue
        k_st = f.type

        yield IterAtt(k, k_st, v0)


def get_fields_values(x: dataclass) -> Dict[str, object]:
    res = {}
    for f in fields(type(x)):
        k = f.name
        v0 = getattr(x, k)
        res[k] = v0
    return res


def ipce_from_object_dataclass_instance(ob: dataclass, *, globals_, ieso: IESO) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(T, globals0=globals_, ieso=ieso)

    globals_[T.__name__] = T
    H = make_dict(str, type)
    hints = H()

    for ia in iterate_resolved_type_values_without_default(ob):
        k = ia.attr
        v = ia.value
        T = ia.T
        try:

            res[k] = ipce_from_object(v, T, globals_=globals_, ieso=ieso)

            needs_schema = isinstance(v, (list, tuple))
            if ieso.with_schema and needs_schema and is_unconstrained(T):
                # hints[k] = ipce_from_typelike(type(v), globals0=globals_, ieso=ieso)
                hints[k] = type(v)

        except IPCE_PASS_THROUGH:
            raise
        except BaseException as e:
            msg = (
                f"Could not serialize an object. Problem "
                f"occurred with the attribute {k!r}. It is supposed to be of type @expected "
                f" but found @found."
            )
            raise ZValueError(msg, expected=T, found=type(ob)) from e
    if hints:
        res[HINTS_ATT] = ipce_from_object(hints, ieso=ieso)
    res = sorted_dict_cbor_ord(res)

    return res


def ipce_from_object_dict(ob: dict, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO):
    K, V = get_dict_type_suggestion(ob, st)
    DT = Dict[K, V]
    res = {}

    from .conv_ipce_from_typelike import ipce_from_typelike

    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(DT, globals0=globals_, ieso=ieso)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
    elif isinstance(K, type) and issubclass(K, int):
        for k, v in ob.items():
            res[str(k)] = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
    else:
        FV = FakeValues[K, V]

        for i, (k, v) in enumerate(ob.items()):
            # kj = ipce_from_object(k, globals_=globals_)
            # h = get_sha256_base58(cbor2.dumps(kj)).decode("ascii")
            #
            h = get_key_for_set_entry(i, len(ob))
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_=globals_, ieso=ieso)
    res = sorted_dict_cbor_ord(res)
    return res


def ipce_from_object_set(ob: set, st: TypeLike, *, globals_: GlobalsDict, ieso: IESO):
    from .conv_ipce_from_typelike import ipce_from_typelike

    V = get_set_type_suggestion(ob, st)
    ST = Set[V]

    res = {}
    if ieso.with_schema:
        res[SCHEMA_ATT] = ipce_from_typelike(ST, globals0=globals_, ieso=ieso)

    for i, v in enumerate(ob):
        h = get_key_for_set_entry(i, len(ob))
        vj = ipce_from_object(v, V, globals_=globals_, ieso=ieso)
        # h = "set:" + get_sha256_base58(cbor2.dumps(vj)).decode("ascii")

        res[h] = vj

    res = sorted_dict_cbor_ord(res)
    return res


def get_key_for_set_entry(i: int, n: int):
    ndigits = len(str(n))
    format = f"%0{ndigits}d"
    x = format % i
    return f"set:{x}"
