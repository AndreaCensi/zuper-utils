import datetime
from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple, Type

import cbor2
import numpy as np
from frozendict import frozendict
from jsonschema import validate

from zuper_ipce import IPCE
from zuper_ipce.assorted_recursive_type_subst import resolve_all
from zuper_ipce.constants import GlobalsDict, HINTS_ATT, PASS_THROUGH, SCHEMA_ATT
from zuper_ipce.ipce_spec import assert_canonical_ipce, sorted_dict_with_cbor_ordering
from zuper_ipce.numpy_encoding import ipce_from_numpy_array
from zuper_ipce.structures import FakeValues
from zuper_ipce.utils_text import get_sha256_base58
from zuper_typing.annotations_tricks import (get_Optional_arg, is_Any, is_Callable, is_ClassVar, is_Dict, is_List,
                                             is_Optional, is_Sequence, is_Set, is_Tuple, is_Union)
from zuper_typing.my_dict import (get_CustomDict_args, get_DictLike_args, get_ListLike_arg, get_SetLike_arg,
                                  is_CustomDict, is_DictLike, is_ListLike, is_SetLike)
from zuper_typing.subcheck import can_be_used_as2


def ipce_from_object(ob, globals_: GlobalsDict = None, suggest_type=None, with_schema=True) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
    globals_ = globals_ or {}
    try:
        res = ipce_from_object_(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)
    except TypeError as e:
        msg = f'ipce_from_object() for type {type(ob)} failed.'
        raise TypeError(msg) from e
    # print(indent(json.dumps(res, indent=3), '|', ' res: -'))
    if isinstance(res, dict) and SCHEMA_ATT in res:

        schema = res[SCHEMA_ATT]

        # print(json.dumps(schema, indent=2))
        # print(json.dumps(res, indent=2))

        # currently disabled becasue JSONSchema insists on resolving all the URIs
        if False:
            validate(res, schema)
        #
        # try:
        #
        # except:  # pragma: no cover
        #     # cannot generate this if there are no bugs
        #     fn = 'error.json'
        #     with open(fn, 'w') as f:
        #         f.write(json.dumps(res, indent=2))
        #     raise
    assert_canonical_ipce(res)
    return res


def ipce_from_object_(ob,
                      globals_: GlobalsDict,
                      with_schema: bool,
                      suggest_type: Type = None,
                      ) -> IPCE:
    if ob is None:
        return ob
    trivial = (bool, int, str, float, bytes, Decimal, datetime.datetime)
    if isinstance(ob, datetime.datetime):
        if not ob.tzinfo:
            msg = 'Cannot serialize dates without a timezone.'
            raise ValueError(msg)
    if isinstance(ob, trivial):
        for T in trivial:
            if isinstance(ob, T):
                if (suggest_type is not None) and (suggest_type is not T) and (not is_Any(suggest_type)) and \
                      (not can_be_used_as2(T, suggest_type, {}).result):
                    msg = f'Found object of type {type(ob)!r} when expected a {suggest_type!r}'
                    raise ValueError(msg)
                return ob

    if isinstance(ob, list):
        if is_ListLike(suggest_type):
            suggest_type_l = get_ListLike_arg(suggest_type)
        else:
            # XXX should we warn?
            suggest_type_l = None  # XXX
        return [ipce_from_object(_, globals_, suggest_type=suggest_type_l,
                                 with_schema=with_schema) for _ in ob]

    if isinstance(ob, tuple):
        suggest_type_l = None  # XXX
        return [ipce_from_object(_, globals_, suggest_type=suggest_type_l,
                                 with_schema=with_schema) for _ in ob]

    from zuper_ipce.conv_ipce_from_typelike import (ipce_from_typelike_slice, ipce_from_typelike,
                                                    ipce_from_typelike_ndarray)
    if isinstance(ob, slice):
        res = {
              'start': ob.start,
              'step':  ob.step,
              'stop':  ob.stop
              }
        if with_schema:
            res[SCHEMA_ATT] = ipce_from_typelike_slice().schema
        res = sorted_dict_with_cbor_ordering(res)
        return res

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
        res = ipce_from_numpy_array(ob)
        if with_schema:
            res[SCHEMA_ATT] = ipce_from_typelike_ndarray().schema
        return res

    assert not isinstance(ob, type), ob
    if is_dataclass(ob):
        return ipce_from_object_dataclass_instance(ob, globals_, with_schema=with_schema, suggest_type=suggest_type)

    msg = f'I do not know a way to convert object of type {type(ob)} ({ob}).'
    raise NotImplementedError(msg)


def ipce_from_object_dataclass_instance(ob, globals_, with_schema: bool, suggest_type: Optional[type]) -> IPCE:
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike
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

            if is_ClassVar(suggest_type):
                continue

            if v is None:
                if is_Optional(suggest_type):
                    continue

            if is_Optional(suggest_type):
                suggest_type = get_Optional_arg(suggest_type)

            res[k] = ipce_from_object(v, globals_,
                                      suggest_type=suggest_type, with_schema=with_schema)
            if with_schema and isinstance(v, (list, tuple)) and is_Any(f.type):
                hints[k] = ipce_from_typelike(type(v), globals_)
        except PASS_THROUGH:
            raise
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
    res = {}
    suggest_type, K, V = get_best_type_for_serializing_dict(ob, suggest_type)
    # logger.info(f'Using suggest_type for dict = {suggest_type}')
    from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike
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
            if isinstance(k, int):
                h = str(k)
            else:
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

    from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike
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
    # noinspection PyBroadException
    try:
        if len(set(type_keys)) == 1:
            K = type_keys[0]
    except:  # XXX
        pass
    V = Any
    # noinspection PyBroadException
    try:
        if len(set(type_values)) == 1:
            V = type_values[0]
    except:  # XXX
        pass
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
