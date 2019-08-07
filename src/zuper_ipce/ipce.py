import datetime
import hashlib
import inspect
import typing
import warnings
from dataclasses import make_dataclass, _FIELDS, field, Field, is_dataclass
from decimal import Decimal
from numbers import Number
from typing import (Type, Dict, Any, TypeVar, Optional, ClassVar, cast, Union,
                    Generic, List, Tuple, Callable, Set)

import base58
import cbor2
import numpy as np
import yaml
from frozendict import frozendict
from jsonschema.validators import validator_for, validate
from mypy_extensions import NamedArg
from nose.tools import assert_in

from zuper_commons.text import indent
from zuper_commons.types import check_isinstance
from zuper_typing.constants import PYTHON_36, GENERIC_ATT2, BINDINGS_ATT
from . import logger
from zuper_typing.annotations_tricks import (is_optional, get_optional_type, is_forward_ref,
                                             get_forward_ref_arg, is_Any,
                                             get_Tuple_name,
                                             is_ClassVar, get_ClassVar_arg, is_Type,
                                             is_Callable, get_Callable_info, get_union_types,
                                             is_union, is_Dict,
                                             get_Dict_name_K_V, is_Tuple, get_List_arg,
                                             is_List, is_Set, get_Set_arg, get_Set_name_V, is_Sequence,
                                             get_Sequence_arg, is_VarTuple, get_VarTuple_arg, make_Tuple, is_TupleLike,
                                             get_FixedTuple_args, is_FixedTuple, make_Union, get_Dict_args)
from .constants import (X_PYTHON_MODULE_ATT, ATT_PYTHON_NAME, SCHEMA_BYTES, GlobalsDict, JSONSchema, _SpecialForm,
                        ProcessingDict, EncounteredDict, SCHEMA_ATT, SCHEMA_ID, JSC_TYPE, JSC_STRING, JSC_NUMBER,
                        JSC_OBJECT, JSC_TITLE,
                        JSC_ADDITIONAL_PROPERTIES, JSC_DESCRIPTION, JSC_PROPERTIES, JSC_INTEGER, ID_ATT,
                        JSC_DEFINITIONS, REF_ATT, JSC_REQUIRED, X_CLASSVARS, X_CLASSATTS, JSC_BOOL, JSC_TITLE_NUMPY,
                        JSC_NULL,
                        JSC_TITLE_BYTES, JSC_ARRAY, JSC_ITEMS, JSC_DEFAULT, JSC_TITLE_DECIMAL, JSC_TITLE_DATETIME,
                        JSC_TITLE_FLOAT, JSC_TITLE_CALLABLE, JSC_TITLE_TYPE, SCHEMA_CID, JSC_PROPERTY_NAMES, JSC_ALLOF,
                        JSC_ANYOF, JSC_TITLE_SLICE, USE_REMEMBERED_CLASSES, HINTS_ATT)

from zuper_typing.my_dict import (make_dict, CustomDict, make_set, CustomSet,
                                  get_set_Set_or_CustomSet_Value, is_CustomDict,
                                  is_CustomSet, is_Dict_or_CustomDict,
                                  get_Dict_or_CustomDict_Key_Value, is_list_or_List_or_CustomList,
                                  get_list_or_List_or_CustomList_arg, get_list_or_List_or_CustomList_name,
                                  is_set_or_CustomSet, is_CustomList, get_CustomList_arg, make_list, get_CustomSet_arg,
                                  get_CustomDict_args)
from zuper_typing.my_intersection import is_Intersection, get_Intersection_args, Intersection
from .numpy_encoding import numpy_from_dict, dict_from_numpy
from .pretty import pretty_dict
from zuper_typing.subcheck import can_be_used_as2
from .types import IPCE
from zuper_typing.zeneric2 import get_name_without_brackets, replace_typevars, loglevel, RecLogger

if typing.TYPE_CHECKING:  # pragma: no cover
    pass
else:

    from zuper_typing.monkey_patching_typing import my_dataclass, RegisteredClasses

__all__ = ['object_from_ipce', 'ipce_from_object']
PASS_THROUGH = (KeyboardInterrupt, RecursionError)


# new interface
def ipce_from_object(ob, globals_: GlobalsDict = None, suggest_type=None, with_schema=True) -> IPCE:
    globals_ = globals_ or {}
    return ipce_from_object__(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)


def ipce_from_object__(ob, globals_: GlobalsDict, suggest_type=None, with_schema=True) -> IPCE:
    # logger.debug(f'ipce_from_object({ob})')
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
        if is_List(suggest_type):
            suggest_type_l = get_List_arg(suggest_type)
        else:
            # XXX should we warn?
            suggest_type_l = None  # XXX
        return [ipce_from_object(_, globals_, suggest_type=suggest_type_l,
                                 with_schema=with_schema) for _ in ob]

    if isinstance(ob, tuple):
        suggest_type_l = None  # XXX
        return [ipce_from_object(_, globals_, suggest_type=suggest_type_l,
                                 with_schema=with_schema) for _ in ob]

    if isinstance(ob, slice):
        res = {
              'start': ob.start,
              'step':  ob.step,
              'stop':  ob.stop
              }
        if with_schema:
            res[SCHEMA_ATT] = type_slice_schema()
        return res

    if isinstance(ob, set):
        return set_to_ipce(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, (dict, frozendict)):
        return dict_to_ipce(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, type):
        return type_to_schema(ob, globals_, processing={})

    if is_Any(ob) or is_List(ob) or is_Dict(ob) or is_Set(ob) or is_Tuple(ob) \
          or is_Callable(ob) or is_union(ob) or is_Sequence(ob) or is_optional(ob):
        # TODO: put more here
        return type_to_schema(ob, globals_, processing={})

    if isinstance(ob, np.ndarray):
        res = dict_from_numpy(ob)
        if with_schema:
            res[SCHEMA_ATT] = type_numpy_to_schema(type(ob), globals_, {})
        return res

    if is_dataclass(ob):
        return serialize_dataclass_instance(ob, globals_, with_schema=with_schema, suggest_type=suggest_type)

    msg = f'I do not know a way to convert object of type {type(ob)} ({ob}).'
    raise NotImplementedError(msg)


import dataclasses


def serialize_dataclass_instance(ob, globals_, with_schema: bool, suggest_type: Optional[type]):
    globals_ = dict(globals_)
    res = {}
    T = type(ob)

    if with_schema:
        res[SCHEMA_ATT] = type_to_schema(T, globals_)

    globals_[T.__name__] = T
    hints = {}

    for f in dataclasses.fields(ob):
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
                if is_optional(suggest_type):
                    continue

            if is_optional(suggest_type):
                suggest_type = get_optional_type(suggest_type)

            res[k] = ipce_from_object(v, globals_,
                                      suggest_type=suggest_type, with_schema=with_schema)
            if with_schema and isinstance(v, (list, tuple)) and is_Any(f.type):
                hints[k] = type_to_schema(type(v), globals_)
        except PASS_THROUGH:
            raise
        except BaseException as e:
            msg = f'Obtained {type(e).__name__} while serializing attribute {k}  of type {type(v)}.'
            msg += f'\nThe schema for {type(ob)} says that it should be of type {f.type}.'

            msg += '\n' + f'{v}'
            raise ValueError(msg) from e
    if hints:
        res[HINTS_ATT] = hints
    return res


def resolve_all(T, globals_):
    """
        Returns either a type or a generic alias


    :return:
    """
    if isinstance(T, type):
        return T

    if isinstance(T, str):
        T = eval_just_string(T, globals_)
        return T

    if is_forward_ref(T):
        tn = get_forward_ref_arg(T)
        return resolve_all(tn, globals_)

    if is_optional(T):
        t = get_optional_type(T)
        t = resolve_all(t, globals_)
        return Optional[t]

    # logger.debug(f'no thing to do for {T}')
    return T


def guess_type_for_naked_dict(ob: dict) -> Tuple[type, type]:
    if not ob:
        return Any, Any
    type_values = tuple(type(_) for _ in ob.values())
    type_keys = tuple(type(_) for _ in ob.keys())
    K = Any
    try:
        if len(set(type_keys)) == 1:
            K = type_keys[0]
    except:
        pass
    V = Any
    try:
        if len(set(type_values)) == 1:
            V = type_values[0]
    except:
        pass
    return K, V


def get_best_type_for_serializing_dict(ob: dict, suggest_type: Optional[type]) -> Tuple[type, type, type]:
    T = type(ob)
    if is_CustomDict(T):
        K, V = get_CustomDict_args(T)
    elif is_Dict_or_CustomDict(suggest_type):
        K, V = get_Dict_or_CustomDict_Key_Value(suggest_type)
    elif (suggest_type is None) or is_Any(suggest_type):
        K, V = guess_type_for_naked_dict(ob)
    else:  # pragma: no cover
        assert False, suggest_type

    suggest_type = Dict[K, V]
    return suggest_type, K, V


def dict_to_ipce(ob: dict, globals_: GlobalsDict, suggest_type: Optional[type], with_schema: bool):
    # assert suggest_type is not None
    res = {}
    suggest_type, K, V = get_best_type_for_serializing_dict(ob, suggest_type)
    # logger.info(f'Using suggest_type for dict = {suggest_type}')
    if with_schema:
        res[SCHEMA_ATT] = type_to_schema(suggest_type, globals_)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = ipce_from_object(v, globals_, suggest_type=V, with_schema=with_schema)
    else:
        FV = FakeValues[K, V]

        for k, v in ob.items():
            kj = ipce_from_object(k, globals_)
            if isinstance(k, int):
                h = str(k)
            else:
                h = get_sha256_base58(cbor2.dumps(kj)).decode('ascii')
            fv = FV(k, v)
            res[h] = ipce_from_object(fv, globals_, with_schema=with_schema)

    return res


def set_to_ipce(ob: set, globals_: GlobalsDict, suggest_type: Optional[type], with_schema: bool):
    if suggest_type is not None and is_Set(suggest_type):
        V = get_Set_arg(suggest_type)
    else:
        V = None

    res = {}

    if with_schema:
        if suggest_type is not None:
            res[SCHEMA_ATT] = type_to_schema(suggest_type, globals_)
        else:
            res[SCHEMA_ATT] = type_to_schema(type(ob), globals_)

    for v in ob:
        vj = ipce_from_object(v, globals_, with_schema=with_schema,
                              suggest_type=V)
        h = get_sha256_base58(cbor2.dumps(vj)).decode('ascii')

        res[h] = vj

    return res


def get_sha256_base58(contents):
    import hashlib
    m = hashlib.sha256()
    m.update(contents)
    s = m.digest()
    return base58.b58encode(s)


# ids2cid = {}


@loglevel
def object_from_ipce(mj: IPCE,
                     global_symbols: Dict,
                     encountered: Optional[dict] = None,
                     expect_type: Optional[type] = None) -> object:
    try:
        res = object_from_ipce_(mj, global_symbols, encountered=encountered, expect_type=expect_type)
        return res

    except PASS_THROUGH:
        raise

    except BaseException as e:
        msg = f'Cannot deserialize object  (expect: {expect_type})'
        msg += '\n\n' + indent(yaml.dump(mj), ' ipce ')
        # msg += '\n\n' + indent(traceback.format_exc(), '| ')
        raise TypeError(msg) from e


# @deprecated
def ipce_to_object(mj: IPCE,
                   global_symbols,
                   encountered: Optional[dict] = None,
                   expect_type: Optional[type] = None) -> object:
    res = object_from_ipce(mj, global_symbols, encountered=encountered, expect_type=expect_type)
    return res


def object_from_ipce_(mj: IPCE,
                      global_symbols,
                      encountered: Optional[dict] = None,
                      expect_type: Optional[type] = None) -> object:
    encountered = encountered or {}

    # logger.debug(f'ipce_to_object expect {expect_type} mj {mj}')
    trivial = (int, float, bool, datetime.datetime, Decimal, bytes, str)

    if isinstance(mj, trivial):
        T = type(mj)
        if expect_type is not None:
            ok = can_be_used_as2(T, expect_type, {})
            if not ok.result:
                msg = f'Found a {T}, wanted {expect_type}'
                raise ValueError(msg)
        return mj

    if isinstance(mj, list):
        if expect_type is not None:
            # logger.info(f'expect_type for list is {expect_type}')
            if is_Any(expect_type):
                suggest = None
                seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
                return seq
            elif is_TupleLike(expect_type):
                # noinspection PyTypeChecker
                return deserialize_tuple(expect_type, mj, global_symbols, encountered)
            elif is_List(expect_type):
                suggest = get_List_arg(expect_type)
                seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
                return seq
            else:
                assert False, expect_type
        else:
            suggest = None
            seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
            return seq

    if mj is None:
        if expect_type is None:
            return None
        elif expect_type is type(None):
            return None
        elif is_optional(expect_type):
            return None
        else:
            msg = f'The value is None but the expected type is {expect_type}.'
            raise TypeError(msg)  # XXX

    if expect_type is np.ndarray:
        return numpy_from_dict(mj)

    assert isinstance(mj, dict), type(mj)

    if mj.get(SCHEMA_ATT, '') == SCHEMA_ID:
        schema = cast(JSONSchema, mj)
        return schema_to_type(schema, global_symbols, encountered)

    if SCHEMA_ATT in mj:
        sa = mj[SCHEMA_ATT]
        K = schema_to_type(sa, global_symbols, encountered)
        # logger.debug(f' loaded K = {K} from {mj}')
    else:
        if expect_type is not None:
            # logger.debug('expect_type = %s' % expect_type)
            # check_isinstance(expect_type, type)
            K = expect_type
        else:
            msg = f'Cannot find a schema and expect_type=None.\n{mj}'
            raise ValueError(msg)

    # assert isinstance(K, type), K

    if is_optional(K):
        assert mj is not None  # excluded before
        K = get_optional_type(K)

        return object_from_ipce(mj,
                                global_symbols,
                                encountered,
                                expect_type=K)

    if (isinstance(K, type) and issubclass(K, dict)) or is_Dict(K) or \
          (isinstance(K, type) and issubclass(K, CustomDict)):
        return deserialize_Dict(K, mj, global_symbols, encountered)

    if (isinstance(K, type) and issubclass(K, set)) or is_Set(K) or \
          (isinstance(K, type) and issubclass(K, CustomSet)):
        return deserialize_Set(K, mj, global_symbols, encountered)

    if is_dataclass(K):
        return deserialize_dataclass(K, mj, global_symbols, encountered)

    if is_union(K):
        errors = []
        for T in get_union_types(K):
            try:
                return object_from_ipce(mj,
                                        global_symbols,
                                        encountered,
                                        expect_type=T)
            except PASS_THROUGH:
                raise
            except BaseException as e:
                errors.append(e)
        msg = f'Cannot deserialize with any of {get_union_types(K)}'
        msg += '\n'.join(str(e) for e in errors)
        raise Exception(msg)

    if is_Any(K):
        K = Dict[str, Any]
        # TODO: check that it is strings
        if isinstance(mj, dict):
            return deserialize_Dict(K, mj, global_symbols, encountered)
        msg = f'Not implemented - K = Any'
        msg += '\n\n' + indent(yaml.dump(mj), ' > ')
        raise NotImplementedError(msg)
    assert False, (type(K), K, mj, expect_type)  # pragma: no cover


def deserialize_tuple(expect_type, mj, global_symbols, encountered):
    if is_FixedTuple(expect_type):
        seq = []
        for i, ob in enumerate(mj):
            expect_type_i = expect_type.__args__[i]
            seq.append(object_from_ipce(ob, global_symbols, encountered, expect_type=expect_type_i))

        return tuple(seq)
    elif is_VarTuple(expect_type):
        T = get_VarTuple_arg(expect_type)
        seq = []
        for i, ob in enumerate(mj):
            seq.append(object_from_ipce(ob, global_symbols, encountered, expect_type=T))

        return tuple(seq)
    else:
        assert False


def deserialize_dataclass(K, mj, global_symbols, encountered):
    # assert  isinstance(K, type), K
    global_symbols = dict(global_symbols)
    global_symbols[K.__name__] = K
    # logger.debug(global_symbols)

    # logger.debug(f'Deserializing object of type {K}')
    # logger.debug(f'mj: \n' + json.dumps(mj, indent=2))
    # some data classes might have no annotations ("Empty")
    anns = getattr(K, '__annotations__', {})
    if not anns:
        pass
        # logger.warning(f'No annotations for class {K}')
    # pprint(f'annotations: {anns}')
    attrs = {}
    hints = mj.get(HINTS_ATT, {})
    # logger.info(f'hints for {K.__name__} = {hints}')

    for k, v in mj.items():
        if k in anns:
            expect_type = resolve_all(anns[k], global_symbols)
            if is_optional(expect_type):
                expect_type = get_optional_type(expect_type)

            if inspect.isabstract(expect_type):
                msg = f'Trying to instantiate abstract class for field "{k}" of class {K}'
                msg += f'\n annotation = {anns[k]}'
                msg += f'\n expect_type = {expect_type}'
                msg += f'\n\n%s' % indent(yaml.dump(mj), ' > ')
                raise TypeError(msg)

            if k in hints:
                expect_type = schema_to_type(hints[k], global_symbols, encountered)
                # logger.info(f'hint for member {k} is {expect_type} of {K.__name__}')
            # else:
            # logger.info(f'no hint for member {k} of {K.__name__}')
            try:
                attrs[k] = object_from_ipce(v, global_symbols, encountered, expect_type=expect_type)

            except PASS_THROUGH:
                raise
            except BaseException as e:
                msg = f'Cannot deserialize attribute {k} (expect: {expect_type})'
                msg += '\n\n' + indent(yaml.dump(v), '  ')
                # msg += '\n\n' + indent(traceback.format_exc(), '| ')
                raise TypeError(msg) from e

    for k, T in anns.items():
        T = resolve_all(T, global_symbols)
        if is_ClassVar(T):
            continue
        if not k in mj:
            msg = f'Cannot find field {k!r} in data. Know {sorted(mj)}'
            if is_optional(T):
                attrs[k] = None
                pass
            else:
                raise ValueError(msg)

    try:
        return K(**attrs)
    except TypeError as e:  # pragma: no cover
        msg = f'Cannot instantiate type with attrs {attrs}:\n{K}'
        msg += f'\n\n Bases: {K.__bases__}'
        anns = getattr(K, '__annotations__', 'none')
        msg += f"\n{anns}"
        df = getattr(K, '__dataclass_fields__', 'none')
        # noinspection PyUnresolvedReferences
        msg += f'\n{df}'

        msg += f'because:\n{e}'  # XXX
        raise TypeError(msg) from e


def deserialize_Dict(D, mj, global_symbols, encountered):
    if isinstance(D, type) and issubclass(D, CustomDict):
        K, V = D.__dict_type__
        ob = D()
    elif is_Dict(D):
        K, V = D.__args__
        D2 = make_dict(K, V)
        ob = D2()
    elif isinstance(D, type) and issubclass(D, dict):
        K, V = Any, Any
        ob = D()
    else:  # pragma: no cover
        msg = pretty_dict("not sure", dict(D=D))
        raise NotImplementedError(msg)

    attrs = {}

    FV = FakeValues[K, V]
    if isinstance(K, type) and issubclass(K, str):
        expect_type_V = V
    else:
        expect_type_V = FV

    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        try:
            attrs[k] = object_from_ipce(v, global_symbols, encountered,
                                        expect_type=expect_type_V)

        except (TypeError, NotImplementedError) as e:
            msg = f'Cannot deserialize element at index "{k}".'
            msg += f'\n\n D = {D}'
            msg += '\n\n' + indent(yaml.dump(mj), '> ')
            msg += f'\n\n Expected V = {expect_type_V}'

            msg += f'\n\n v = {yaml.dump(v)}'
            raise TypeError(msg) from e
    if isinstance(K, type) and issubclass(K, str):
        ob.update(attrs)
        return ob
    else:
        for k, v in attrs.items():
            # noinspection PyUnresolvedReferences
            ob[v.real_key] = v.value
        return ob


def deserialize_Set(D, mj, global_symbols, encountered):
    V = get_set_Set_or_CustomSet_Value(D)

    res = set()

    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        vob = object_from_ipce(v, global_symbols, encountered, expect_type=V)
        res.add(vob)

    T = make_set(V)
    return T(res)


class CannotFindSchemaReference(Exception):
    pass


class CannotResolveTypeVar(Exception):
    pass


schema_cache: Dict[Any, Union[type, _SpecialForm]] = {}


def schema_hash(k):
    ob_cbor = cbor2.dumps(k)
    ob_cbor_hash = hashlib.sha256(ob_cbor).digest()
    return ob_cbor_hash


def schema_to_type(schema0: JSONSchema,
                   global_symbols: Dict,
                   encountered: Dict) -> Union[type, _SpecialForm]:
    h = schema_hash([schema0, list(global_symbols), list(encountered)])
    if h in schema_cache:
        # logger.info(f'cache hit for {schema0}')
        return schema_cache[h]

    try:
        res = schema_to_type_(schema0, global_symbols, encountered)
    except (TypeError, ValueError) as e:
        msg = 'Cannot interpret schema as a type.'
        msg += '\n\n' + indent(yaml.dump(schema0), ' > ')
        msg += '\n\n' + pretty_dict('globals', global_symbols)
        msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e

    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        encountered[schema_id] = res
        # print(f'Found {schema_id} -> {res}')

    schema_cache[h] = res
    return res


def schema_to_type_(schema0: JSONSchema, global_symbols: Dict, encountered: Dict) -> Union[type, _SpecialForm]:
    # pprint('schema_to_type_', schema0=schema0)
    encountered = encountered or {}
    info = dict(global_symbols=global_symbols, encountered=encountered)
    check_isinstance(schema0, dict)
    schema = cast(JSONSchema, dict(schema0))
    # noinspection PyUnusedLocal
    metaschema = schema.pop(SCHEMA_ATT, None)
    schema_id = schema.pop(ID_ATT, None)
    if schema_id:
        if not JSC_TITLE in schema:
            pass
        else:
            cls_name = schema[JSC_TITLE]
            encountered[schema_id] = cls_name

    if schema == {}:
        return Any

    if REF_ATT in schema:
        r = schema[REF_ATT]
        if r == SCHEMA_ID:
            if schema.get(JSC_TITLE, '') == 'type':
                return type
            else:
                return Type

        if r in encountered:
            return encountered[r]
        else:
            m = f'Cannot evaluate reference {r!r}'
            msg = pretty_dict(m, info)
            raise CannotFindSchemaReference(msg)

    if JSC_ANYOF in schema:
        options = schema[JSC_ANYOF]
        args = [schema_to_type(_, global_symbols, encountered) for _ in options]
        if args and args[-1] is type(None):
            V = args[0]
            return Optional[V]
        else:
            return Union[tuple(args)]

    if JSC_ALLOF in schema:
        options = schema[JSC_ALLOF]
        args = [schema_to_type(_, global_symbols, encountered) for _ in options]
        res = Intersection[tuple(args)]
        return res

    jsc_type = schema.get(JSC_TYPE, None)
    jsc_title = schema.get(JSC_TITLE, '-not-provided-')
    if jsc_title == JSC_TITLE_NUMPY:
        return np.ndarray

    if jsc_type == JSC_STRING:
        if jsc_title == JSC_TITLE_BYTES:
            return bytes
        elif jsc_title == JSC_TITLE_DATETIME:
            return datetime.datetime
        elif jsc_title == JSC_TITLE_DECIMAL:
            return Decimal
        else:
            return str
    elif jsc_type == JSC_NULL:
        return type(None)

    elif jsc_type == JSC_BOOL:
        return bool

    elif jsc_type == JSC_NUMBER:
        if jsc_title == JSC_TITLE_FLOAT:
            return float
        else:
            return Number

    elif jsc_type == JSC_INTEGER:
        return int

    elif jsc_type == JSC_OBJECT:
        if jsc_title == JSC_TITLE_CALLABLE:
            return schema_to_type_callable(schema, global_symbols, encountered)
        elif jsc_title.startswith('Dict['):
            return schema_dict_to_DictType(schema, global_symbols, encountered)
        elif jsc_title.startswith('Set['):
            return schema_dict_to_SetType(schema, global_symbols, encountered)
        elif JSC_DEFINITIONS in schema:
            return schema_to_type_generic(schema, global_symbols, encountered)
        elif ATT_PYTHON_NAME in schema:
            tn = schema[ATT_PYTHON_NAME]
            if tn in global_symbols:
                return global_symbols[tn]
            else:
                # logger.debug(f'did not find {tn} in {global_symbols}')
                return schema_to_type_dataclass(schema, global_symbols, encountered, schema_id=schema_id)
        else:
            return schema_to_type_dataclass(schema, global_symbols, encountered, schema_id=schema_id)
        assert False, schema  # pragma: no cover
    elif jsc_type == JSC_ARRAY:
        return schema_array_to_type(schema, global_symbols, encountered)

    assert False, schema  # pragma: no cover


def schema_array_to_type(schema, global_symbols, encountered):
    items = schema['items']
    if isinstance(items, list):
        # assert len(items) > 0
        args = tuple([schema_to_type(_, global_symbols, encountered) for _ in items])

        return make_Tuple(*args)
        # if PYTHON_36:  # pragma: no cover
        #     return typing.Tuple[args]
        # else:
        #     # noinspection PyArgumentList
        #     return Tuple.__getitem__(args)
    else:
        if 'Tuple' in schema[JSC_TITLE]:

            args = schema_to_type(items, global_symbols, encountered)
            if PYTHON_36:  # pragma: no cover
                return typing.Tuple[args, ...]
            else:
                # noinspection PyArgumentList
                return Tuple.__getitem__((args, Ellipsis))
        else:

            args = schema_to_type(items, global_symbols, encountered)
            if PYTHON_36:  # pragma: no cover
                return List[args]
            else:
                # noinspection PyArgumentList
                return List[args]


def schema_dict_to_DictType(schema, global_symbols, encountered):
    K = str
    V = schema_to_type(schema[JSC_ADDITIONAL_PROPERTIES], global_symbols, encountered)
    # pprint(f'here:', d=dict(V.__dict__))
    # if issubclass(V, FakeValues):
    if isinstance(V, type) and V.__name__.startswith('FakeValues'):
        K = V.__annotations__['real_key']
        V = V.__annotations__['value']

    try:
        D = make_dict(K, V)
    except (TypeError, ValueError) as e:
        msg = f'Cannot reconstruct dict type with K = {K!r}  V = {V!r}'
        msg += '\n\n' + pretty_dict('globals', global_symbols)
        msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e
    # we never put it anyway
    # if JSC_DESCRIPTION in schema:
    #     setattr(D, '__doc__', schema[JSC_DESCRIPTION])
    return D


def schema_dict_to_SetType(schema, global_symbols, encountered):
    if not JSC_ADDITIONAL_PROPERTIES in schema:
        msg = f'Expected {JSC_ADDITIONAL_PROPERTIES!r} in {schema}'
        raise ValueError(msg)
    V = schema_to_type(schema[JSC_ADDITIONAL_PROPERTIES], global_symbols, encountered)
    return make_set(V)


def type_to_schema(T: Any, globals0: dict, processing: ProcessingDict = None) -> JSONSchema:
    # pprint('type_to_schema', T=T)
    globals_ = dict(globals0)
    processing = processing or {}
    try:
        if hasattr(T, '__name__') and T.__name__ in processing:
            return processing[T.__name__]
            # res =  cast(JSONSchema, {REF_ATT: refname})
            # return res
        if T is type:
            res = cast(JSONSchema, {
                  REF_ATT:   SCHEMA_ID,
                  JSC_TITLE: JSC_TITLE_TYPE
                  # JSC_DESCRIPTION: T.__doc__
                  })
            return res

        if T is type(None):
            res = cast(JSONSchema, {
                  SCHEMA_ATT: SCHEMA_ID,
                  JSC_TYPE:   JSC_NULL
                  })
            return res

        if isinstance(T, type):
            for klass in T.mro():
                if klass.__name__.startswith('Generic'):
                    continue
                if klass is object:
                    continue

                # globals_[klass.__name__] = klass

                globals_[get_name_without_brackets(klass.__name__)] = klass

                bindings = getattr(klass, BINDINGS_ATT, {})
                for k, v in bindings.items():
                    if hasattr(v, '__name__') and v.__name__ not in globals_:
                        globals_[v.__name__] = v
                    globals_[k.__name__] = v

        schema = type_to_schema_(T, globals_, processing)
        check_isinstance(schema, dict)
    except NotImplementedError:  # pragma: no cover
        raise
    except (ValueError, AssertionError) as e:
        m = f'Cannot get schema for type {T!r} (metatype {type(T)}'
        if hasattr(T, '__name__'):
            m += f' (name = {T.__name__!r})'
        msg = pretty_dict(m, dict(  # globals0=globals0,
              # globals=globals_,
              processing=processing))
        # msg += '\n' + traceback.format_exc()
        raise type(e)(msg) from e
    except PASS_THROUGH:
        raise
    except BaseException as e:
        m = f'Cannot get schema for {T}'
        if hasattr(T, '__name__'):
            m += f' (name = {T.__name__!r})'
            m += f' {T.__name__ in processing}'
        msg = pretty_dict(m, dict(  # globals0=globals0,
              # globals=globals_,
              processing=processing))
        raise TypeError(msg) from e

    assert_in(SCHEMA_ATT, schema)
    assert schema[SCHEMA_ATT] in [SCHEMA_ID]
    # assert_equal(schema[SCHEMA_ATT], SCHEMA_ID)

    if schema[SCHEMA_ATT] == SCHEMA_ID:
        # print(yaml.dump(schema))

        if False:
            cls = validator_for(schema)
            cls.check_schema(schema)
    return schema


KK = TypeVar('KK')
VV = TypeVar('VV')

from zuper_typing.monkey_patching_typing import my_dataclass


@my_dataclass
class FakeValues(Generic[KK, VV]):
    real_key: KK
    value: VV


def dict_to_schema(T, globals_, processing) -> JSONSchema:
    K, V = get_Dict_or_CustomDict_Key_Value(T)

    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Dict_name_K_V(K, V)
    if isinstance(K, type) and issubclass(K, str):
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(V, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        return res
    else:
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        props = FakeValues[K, V]
        res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(props, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        return res


def set_to_schema(T, globals_, processing) -> JSONSchema:
    assert is_Set(T) or (isinstance(T, type) and issubclass(T, set)), T

    V = get_set_Set_or_CustomSet_Value(T)

    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Set_name_V(V)
    res[JSC_PROPERTY_NAMES] = SCHEMA_CID
    res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(V, globals_, processing)
    res[SCHEMA_ATT] = SCHEMA_ID
    return res


def Tuple_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_TupleLike(T), T
    # args = T.__args__
    if is_VarTuple(T):
        items = get_VarTuple_arg(T)
        # if args[-1] == Ellipsis:
        #     items = args[0]
        res = cast(JSONSchema, {})
        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = type_to_schema(items, globals_, processing)
        res[JSC_TITLE] = get_Tuple_name(T)
        return res
    elif is_FixedTuple(T):
        args = get_FixedTuple_args(T)
        res = cast(JSONSchema, {})

        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = []
        res[JSC_TITLE] = get_Tuple_name(T)
        for a in args:
            res[JSC_ITEMS].append(type_to_schema(a, globals_, processing))
        return res
    else:
        assert False


def List_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_list_or_List_or_CustomList(T)
    items = get_list_or_List_or_CustomList_arg(T)
    res = cast(JSONSchema, {})
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_ARRAY
    res[JSC_ITEMS] = type_to_schema(items, globals_, processing)
    res[JSC_TITLE] = get_list_or_List_or_CustomList_name(T)
    return res


def type_callable_to_schema(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_Callable(T)
    cinfo = get_Callable_info(T)

    res = cast(JSONSchema, {
          JSC_TYPE:  JSC_OBJECT, SCHEMA_ATT: SCHEMA_ID,
          JSC_TITLE: JSC_TITLE_CALLABLE,
          'special': 'callable'
          })

    p = res[JSC_DEFINITIONS] = {}
    for k, v in cinfo.parameters_by_name.items():
        p[k] = type_to_schema(v, globals_, processing)
    p['return'] = type_to_schema(cinfo.returns, globals_, processing)
    res['ordering'] = cinfo.ordering
    # print(res)
    return res


def schema_to_type_callable(schema: JSONSchema, global_symbols: GlobalsDict, encountered: ProcessingDict):
    schema = dict(schema)
    definitions = dict(schema[JSC_DEFINITIONS])
    ret = schema_to_type(definitions.pop('return'), global_symbols, encountered)
    others = []
    for k in schema['ordering']:
        d = schema_to_type(definitions[k], global_symbols, encountered)
        if not k.startswith('__'):
            d = NamedArg(d, k)
        others.append(d)

    # noinspection PyTypeHints
    return Callable[others, ret]


def type_to_schema_(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    if T is None:
        raise ValueError('None is not a type!')

    # This can actually happen inside a Tuple (or Dict, etc.) even though
    # we have a special case for dataclass

    if is_forward_ref(T):  # pragma: no cover
        arg = get_forward_ref_arg(T)
        # if arg == MemoryJSON.__name__:
        #     return type_to_schema_(MemoryJSON, globals_, processing)
        msg = f'It is not supported to have an ForwardRef here yet: {T}'
        raise ValueError(msg)

    if isinstance(T, str):  # pragma: no cover
        msg = f'It is not supported to have a string here: {T!r}'
        raise ValueError(msg)

    # pprint('type_to_schema_', T=T)
    if T is str:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is bool:
        res = cast(JSONSchema, {JSC_TYPE: JSC_BOOL, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is Number:
        res = cast(JSONSchema, {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is float:
        res = cast(JSONSchema, {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: JSC_TITLE_FLOAT})
        return res

    if T is int:
        res = cast(JSONSchema, {JSC_TYPE: JSC_INTEGER, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is slice:
        res = type_slice_schema()
        return res

    if T is Decimal:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_DECIMAL, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is datetime.datetime:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_DATETIME, SCHEMA_ATT: SCHEMA_ID})
        return res

    if T is bytes:
        return SCHEMA_BYTES

    # we cannot use isinstance on typing.Any
    if is_Any(T):  # XXX not possible...
        res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
        return res

    if is_union(T):
        return schema_Union(T, globals_, processing)

    if is_optional(T):
        return schema_Optional(T, globals_, processing)

    if is_Dict_or_CustomDict(T):
        return dict_to_schema(T, globals_, processing)
    #
    # if isinstance(T, type) and issubclass(T, dict):  # pragma: no cover
    #     # msg = f'A regular "dict" slipped through.\n{T}'
    #     T = Dict[Any, Any]
    #     # raise TypeError(msg)
    #     return dict_to_schema(T, globals_, processing)

    # if is_Set(T) or (isinstance(T, type) and issubclass(T, set)):
    if is_set_or_CustomSet(T):
        return set_to_schema(T, globals_, processing)

    if is_Intersection(T):
        return schema_Intersection(T, globals_, processing)

    if is_Callable(T):
        return type_callable_to_schema(T, globals_, processing)

    if is_Sequence(T):
        msg = ('Translating Sequence into List')
        warnings.warn(msg)
        # raise ValueError(msg)
        V = get_Sequence_arg(T)
        T = List[V]
        return List_to_schema(T, globals_, processing)

    if is_list_or_List_or_CustomList(T):
        return List_to_schema(T, globals_, processing)

    if is_TupleLike(T):
        # noinspection PyTypeChecker
        return Tuple_to_schema(T, globals_, processing)

    assert isinstance(T, type), T

    if hasattr(T, GENERIC_ATT2) and is_generic(T):
        return type_generic_to_schema(T, globals_, processing)

    if is_dataclass(T):
        return type_dataclass_to_schema(T, globals_, processing)

    if T is np.ndarray:
        return type_numpy_to_schema(T, globals_, processing)

    msg = f'Cannot interpret this type: {T!r}'
    msg += f'\n   globals_: {globals_}'
    msg += f'\n processing: {processing}'
    raise ValueError(msg)


def is_generic(T):
    a = getattr(T, GENERIC_ATT2)
    return any(isinstance(_, TypeVar) for _ in a)


def type_numpy_to_schema(T, globals_, processing) -> JSONSchema:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_NUMPY
    res[JSC_PROPERTIES] = {
          'shape': {},  # TODO
          'dtype': {},  # TODO
          'data':  SCHEMA_BYTES
          }

    return res


def type_slice_schema() -> JSONSchema:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_SLICE
    T = type_to_schema(Optional[int], {}, {})
    res[JSC_PROPERTIES] = {
          'start': T,  # TODO
          'stop':  T,  # TODO
          'step':  T,
          }

    return res


def schema_Intersection(T, globals_, processing):
    args = get_Intersection_args(T)
    options = [type_to_schema(t, globals_, processing) for t in args]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "allOf": options})
    return res


@loglevel
def schema_to_type_generic(res: JSONSchema, global_symbols: dict, encountered: dict, rl: RecLogger = None) -> Type:
    rl = rl or RecLogger()
    # rl.pp('schema_to_type_generic', schema=res, global_symbols=global_symbols, encountered=encountered)
    assert res[JSC_TYPE] == JSC_OBJECT
    assert JSC_DEFINITIONS in res
    cls_name = res[JSC_TITLE]
    if X_PYTHON_MODULE_ATT in res:
        module_name = res[X_PYTHON_MODULE_ATT]
        k = module_name, cls_name
        if USE_REMEMBERED_CLASSES:
            if k in RegisteredClasses.klasses:
                return RegisteredClasses.klasses[k]
            else:
                pass
                # logger.info(f'cannot find generic {k}')
    else:
        module_name = None

    encountered = dict(encountered)

    required = res.get(JSC_REQUIRED, [])

    typevars: List[TypeVar] = []
    for tname, t in res[JSC_DEFINITIONS].items():
        bound = schema_to_type(t, global_symbols, encountered)
        # noinspection PyTypeHints
        if is_Any(bound):
            bound = None
        # noinspection PyTypeHints
        tv = TypeVar(tname, bound=bound)
        typevars.append(tv)
        if ID_ATT in t:
            encountered[t[ID_ATT]] = tv

    typevars: Tuple[TypeVar, ...] = tuple(typevars)
    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        base = Generic.__getitem__(typevars)
    else:
        # noinspection PyUnresolvedReferences
        base = Generic.__class_getitem__(typevars)

    fields_required = []  # (name, type, Field)
    fields_not_required = []
    for pname, v in res.get(JSC_PROPERTIES, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)

        if pname in required:
            _Field = field()
            fields_required.append((pname, ptype, _Field))
        else:
            _Field = field(default=None)
            ptype = Optional[ptype]
            fields_not_required.append((pname, ptype, _Field))

    fields = fields_required + fields_not_required
    T = make_dataclass(cls_name, fields, bases=(base,), namespace=None, init=True,
                       repr=True, eq=True, order=False,
                       unsafe_hash=False, frozen=False)

    class Placeholder:
        pass

    fix_annotations_with_self_reference(T, cls_name, Placeholder, global_symbols, encountered)

    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    # if ATT_PYTHON_NAME in res:
    #     setattr(T, '__qualname__', res[ATT_PYTHON_NAME])
    if X_PYTHON_MODULE_ATT in res:
        setattr(T, '__module__', res[X_PYTHON_MODULE_ATT])
    return T


def type_generic_to_schema(T: Type, globals_: GlobalsDict, processing_: ProcessingDict) -> JSONSchema:
    assert hasattr(T, GENERIC_ATT2)

    types2 = getattr(T, GENERIC_ATT2)
    processing2 = dict(processing_)
    globals2 = dict(globals_)

    res = cast(JSONSchema, {})
    res[SCHEMA_ATT] = SCHEMA_ID

    res[JSC_TITLE] = T.__name__
    # res[ATT_PYTHON_NAME] = T.__qualname__
    res[X_PYTHON_MODULE_ATT] = T.__module__

    res[ID_ATT] = make_url(T.__name__)

    res[JSC_TYPE] = JSC_OBJECT

    processing2[f'{T.__name__}'] = make_ref(res[ID_ATT])

    # print(f'T: {T.__name__} ')
    definitions = {}

    if hasattr(T, '__doc__') and T.__doc__:
        res[JSC_DESCRIPTION] = T.__doc__
    globals_ = dict(globals_)
    for t2 in types2:
        if not isinstance(t2, TypeVar):
            continue

        url = make_url(f'{T.__name__}/{t2.__name__}')

        # processing2[f'~{name}'] = {'$ref': url}
        processing2[f'{t2.__name__}'] = make_ref(url)
        # noinspection PyTypeHints
        globals2[t2.__name__] = t2

        bound = t2.__bound__ or Any
        schema = type_to_schema(bound, globals2, processing2)
        schema[ID_ATT] = url

        definitions[t2.__name__] = schema

        globals_[t2.__name__] = t2

    if definitions:
        res[JSC_DEFINITIONS] = definitions
    res[JSC_PROPERTIES] = properties = {}
    required = []

    for name, t in T.__annotations__.items():
        t = replace_typevars(t, bindings={}, symbols=globals_, rl=None)
        if is_ClassVar(t):
            continue
        try:
            result = eval_field(t, globals2, processing2)
        except PASS_THROUGH:
            raise
        except BaseException as e:
            msg = f'Cannot evaluate field "{name}" of class {T} annotated as {t}'
            raise Exception(msg) from e
        assert isinstance(result, Result), result
        properties[name] = result.schema
        if not result.optional:
            required.append(name)
    if required:
        res[JSC_REQUIRED] = required

    return res


def type_dataclass_to_schema(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_dataclass(T), T

    p2 = dict(processing)
    res = cast(JSONSchema, {})

    res[ID_ATT] = make_url(T.__name__)
    if hasattr(T, '__name__') and T.__name__:
        res[JSC_TITLE] = T.__name__

        p2[T.__name__] = make_ref(res[ID_ATT])

    # res[ATT_PYTHON_NAME] = T.__qualname__
    res[X_PYTHON_MODULE_ATT] = T.__module__

    res[SCHEMA_ATT] = SCHEMA_ID

    res[JSC_TYPE] = JSC_OBJECT

    if hasattr(T, '__doc__') and T.__doc__:
        res[JSC_DESCRIPTION] = T.__doc__

    res[JSC_PROPERTIES] = properties = {}
    classvars = {}
    classatts = {}

    required = []
    fields_ = getattr(T, _FIELDS)
    # noinspection PyUnusedLocal
    afield: Field

    for name, afield in fields_.items():

        t = afield.type

        try:
            if isinstance(t, str):
                t = eval_just_string(t, globals_)

            if is_ClassVar(t):
                tt = get_ClassVar_arg(t)

                result = eval_field(tt, globals_, p2)
                classvars[name] = result.schema
                the_att = getattr(T, name)

                if isinstance(the_att, type):
                    classatts[name] = type_to_schema(the_att, globals_, processing)

                else:
                    classatts[name] = ipce_from_object(the_att, globals_)

            else:

                result = eval_field(t, globals_, p2)
                if not result.optional:
                    required.append(name)
                properties[name] = result.schema

                if not result.optional:
                    if not isinstance(afield.default, dataclasses._MISSING_TYPE):
                        # logger.info(f'default for {name} is {afield.default}')
                        properties[name]['default'] = ipce_from_object(afield.default, globals_)
        except PASS_THROUGH:
            raise
        except BaseException as e:
            msg = f'Cannot write schema for attribute {name} -> {t} of type {T.__name__}'
            raise TypeError(msg) from e

    if required:  # empty is error
        res[JSC_REQUIRED] = required
    if classvars:
        res[X_CLASSVARS] = classvars
    if classatts:
        res[X_CLASSATTS] = classatts

    return res


class Result:
    schema: JSONSchema
    optional: Optional[bool] = False

    def __init__(self, schema: JSONSchema, optional: bool = None):
        self.schema = schema
        self.optional = optional


# TODO: make url generic
def make_url(x: str):
    assert isinstance(x, str), x
    return f'http://invalid.json-schema.org/{x}#'


def make_ref(x: str) -> JSONSchema:
    assert len(x) > 1, x
    assert isinstance(x, str), x
    return cast(JSONSchema, {REF_ATT: x})


def eval_field(t, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    debug_info2 = lambda: dict(globals_=globals_, processing=processing)

    if isinstance(t, str):
        te = eval_type_string(t, globals_, processing)
        return te

    if is_Type(t):
        res = cast(JSONSchema, make_ref(SCHEMA_ID))
        return Result(res)

    if is_TupleLike(t):
        res = Tuple_to_schema(t, globals_, processing)
        return Result(res)

    if is_list_or_List_or_CustomList(t):
        res = List_to_schema(t, globals_, processing)
        return Result(res)

    if is_forward_ref(t):
        tn = get_forward_ref_arg(t)
        # tt = t._eval_type(globals_, processing)
        # print(f'tn: {tn!r} tt: {tt!r}')

        return eval_type_string(tn, globals_, processing)

    if is_optional(t):
        tt = get_optional_type(t)
        result = eval_field(tt, globals_, processing)
        return Result(result.schema, optional=True)

    if is_union(t):
        return Result(schema_Union(t, globals_, processing))

    if is_Any(t):
        res = cast(JSONSchema, {})
        return Result(res)

    if is_Dict(t):
        schema = dict_to_schema(t, globals_, processing)
        return Result(schema)
    if is_Set(t):
        schema = set_to_schema(t, globals_, processing)
        return Result(schema)

    if isinstance(t, TypeVar):
        l = t.__name__
        if l in processing:
            return Result(processing[l])
        # I am not sure why this is different in Python 3.6
        if PYTHON_36 and (l in globals_):  # pragma: no cover
            T = globals_[l]
            return Result(type_to_schema(T, globals_, processing))

        m = f'Could not resolve the TypeVar {t}'
        msg = pretty_dict(m, debug_info2())
        raise CannotResolveTypeVar(msg)

    if isinstance(t, type):
        # catch recursion here
        if t.__name__ in processing:
            return eval_field(t.__name__, globals_, processing)
        else:
            schema = type_to_schema(t, globals_, processing)
            return Result(schema)

    msg = f'Could not deal with {t}'
    msg += f'\nglobals: {globals_}'
    msg += f'\nprocessing: {processing}'
    raise NotImplementedError(msg)


def schema_Union(t, globals_, processing):
    types = get_union_types(t)
    options = [type_to_schema(t, globals_, processing) for t in types]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "anyOf": options})
    return res


def schema_Optional(t, globals_, processing):
    types = [get_optional_type(t), type(None)]
    options = [type_to_schema(t, globals_, processing) for t in types]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "anyOf": options})
    return res


def eval_type_string(t: str, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    check_isinstance(t, str)
    globals2 = dict(globals_)
    debug_info = lambda: dict(t=t, globals2=pretty_dict("", globals2), processing=pretty_dict("", processing))

    if t in processing:
        schema: JSONSchema = make_ref(make_url(t))
        return Result(schema)

    elif t in globals2:
        return eval_field(globals2[t], globals2, processing)
    else:
        try:
            res = eval_just_string(t, globals2)
            return eval_field(res, globals2, processing)
        except NotImplementedError as e:  # pragma: no cover
            m = 'While evaluating string'
            msg = pretty_dict(m, debug_info())
            raise NotImplementedError(msg) from e
        except PASS_THROUGH:
            raise
        except BaseException as e:  # pragma: no cover
            m = 'Could not evaluate type string'
            msg = pretty_dict(m, debug_info())
            raise ValueError(msg) from e


def eval_just_string(t: str, globals_):
    from typing import Optional
    eval_locals = {
          'Optional': Optional, 'List': List,
          'Dict':     Dict, 'Union': Union, 'Set': typing.Set, 'Any': Any
          }
    # TODO: put more above?
    # do not pollute environment
    if t in globals_:
        return globals_[t]
    eval_globals = dict(globals_)
    try:
        res = eval(t, eval_globals, eval_locals)
        return res
    except PASS_THROUGH:
        raise
    except BaseException as e:
        m = f'Error while evaluating the string {t!r} using eval().'
        msg = pretty_dict(m, dict(eval_locals=eval_locals, eval_globals=eval_globals))
        raise type(e)(msg) from e


@loglevel
def schema_to_type_dataclass(res: JSONSchema, global_symbols: dict, encountered: EncounteredDict,
                             schema_id=None, rl: RecLogger = None) -> Type:
    # rl = rl or RecLogger()
    # rl.pp('schema_to_type_dataclass', res=res) #, global_symbols=global_symbols, encountered=encountered)
    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]
    if X_PYTHON_MODULE_ATT in res:
        module_name = res[X_PYTHON_MODULE_ATT]

        k = module_name, cls_name
        if USE_REMEMBERED_CLASSES:
            if k in RegisteredClasses.klasses:
                # logger.error(f'We can use the class {k}')
                # logger.info(f'using the cached dataclass {k}')
                return RegisteredClasses.klasses[k]
            else:
                pass
                # logger.info(f'cannot find dataclass {k}')

    else:
        module_name = None

    # It's already done by the calling function
    # if ID_ATT in res:
    #     # encountered[res[ID_ATT]] = ForwardRef(cls_name)
    #     encountered[res[ID_ATT]] = cls_name

    # @dataclass
    # class Placeholder:
    #     pass
    #
    Placeholder = type(f'PlaceholderFor{cls_name}', (), {})

    encountered[schema_id] = Placeholder
    required = res.get(JSC_REQUIRED, [])

    fields = []  # (name, type, Field)
    for pname, v in res.get(JSC_PROPERTIES, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)

        if pname in required:
            _Field = field()
        else:
            _Field = field(default=None)
            ptype = Optional[ptype]
        _Field.name = pname
        if JSC_DEFAULT in v:
            default_value = object_from_ipce(v[JSC_DEFAULT], global_symbols, expect_type=ptype)
            _Field.default = default_value

        fields.append((pname, ptype, _Field))

    # pprint('making dataclass with fields', fields=fields, res=res)
    for pname, v in res.get(X_CLASSVARS, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)
        fields.append((pname, ClassVar[ptype], field()))

    # _MISSING_TYPE should be first (default fields last)
    # XXX: not tested
    def has_default(x):
        return not isinstance(x[2].default, dataclasses._MISSING_TYPE)

    fields = sorted(fields, key=has_default, reverse=False)
    #
    # for _, _, f in fields:
    #     logger.info(f'{f.name} {has_default((0,0,f))}')
    unsafe_hash = True
    try:
        T = make_dataclass(cls_name, fields, bases=(), namespace=None,
                           init=True, repr=True, eq=True, order=False,
                           unsafe_hash=unsafe_hash, frozen=False)
    except TypeError:  # pragma: no cover

        msg = 'Cannot make dataclass with fields:'
        for f in fields:
            msg += f'\n {f}'
        logger.error(msg)
        raise

    fix_annotations_with_self_reference(T, cls_name, Placeholder, global_symbols, encountered)

    for pname, v in res.get(X_CLASSATTS, {}).items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = schema_to_type(cast(JSONSchema, v), global_symbols, encountered)
        else:
            interpreted = object_from_ipce(v, global_symbols)
        setattr(T, pname, interpreted)

    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    else:
        # the original one did not have it
        setattr(T, '__doc__', None)

    if module_name is not None:
        setattr(T, '__module__', module_name)
    # if ATT_PYTHON_NAME in res:
    #     setattr(T, '__qualname__', res[ATT_PYTHON_NAME])
    return T


def recursive_type_subst(T, f, ignore=()):
    if T in ignore:
        return T
    r = lambda X: recursive_type_subst(X, f, ignore + (T,))
    if is_optional(T):
        a = get_optional_type(T)
        a2 = r(a)
        # logger.info(f'optional {a} -> {a2}')
        if a == a2:
            return T
        return Optional[a2]
    elif is_forward_ref(T):
        return f(T)
    elif is_union(T):
        ts0 = get_union_types(T)
        ts = tuple(r(_) for _ in ts0)
        # logger.info(f'ts0 {ts0} -> {ts}')
        if ts0 == ts:
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
        return Dict[K, V]
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
            return T

        T2 = my_dataclass(type(T.__name__, (), {
              '__annotations__': annotations,
              '__module__':      T.__module__,
              '__doc__':         getattr(T, '__doc__', None)
              }))

        return T2
        # for f in dataclasses.fields(T):
        #     f.type = T.__annotations__[f.name]
        # return T
    else:
        return f(T)


def fix_annotations_with_self_reference(T, cls_name, Placeholder, global_symbols, encountered):
    # print('fix_annotations_with_self_reference')
    # logger.info(f'fix_annotations_with_self_reference {cls_name}, placeholder: {Placeholder}')
    # logger.info(f'encountered: {encountered}')
    # logger.info(f'global_symbols: {global_symbols}')

    def f(M):
        # print((M, Placeholder, M is Placeholder, M == Placeholder, id(M), id(Placeholder)))
        if hasattr(M, '__name__') and M.__name__ == Placeholder.__name__:
            return T
        if M == Placeholder:
            return T
        elif is_forward_ref(M):
            arg = get_forward_ref_arg(M)
            if arg == cls_name:
                return T
            else:
                return M
        else:
            return M

    def f2(M):
        # print(f'fix_annotation({T}, {cls_name}, {Placeholder})  {M} ')
        r = f(M)
        # if is_dataclass(M):

        if is_dataclass(M):
            d0 = getattr(M, '__doc__', 'NO DOC')
            d1 = getattr(r, '__doc__', 'NO DOC')
        else:
            d0 = d1 = None
        # logger.info(f'f2 for {cls_name}: M = {M} -> {r}')
        # print(f'fix_annotation({T}, {cls_name}, {Placeholder})  {M} {d0!r} -> {r} {d1!r}')
        return r

    for k, v0 in T.__annotations__.items():
        v = recursive_type_subst(v0, f2)
        # logger.info(f'annotation {k} {v0} -> {v}')
        T.__annotations__[k] = v
        # d0 = getattr(v0, '__doc__', 'NO DOC')
        # d1 = getattr(v, '__doc__', 'NO DOC')
        # assert_equal(d0, d1)

    for f in dataclasses.fields(T):
        f.type = T.__annotations__[f.name]

    # logger.info(pretty_dict(f'annotations resolved for {T}', T.__annotations__))
#
