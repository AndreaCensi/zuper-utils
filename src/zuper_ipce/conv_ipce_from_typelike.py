import copy
import dataclasses
import datetime
import typing
import warnings
from decimal import Decimal
from dataclasses import is_dataclass, _FIELDS, Field
from numbers import Number
from typing import Any, cast, Type, List, Optional, TypeVar, Dict, Union

import numpy as np
from nose.tools import assert_in

from zuper_commons.types import check_isinstance

from zuper_ipce.constants import (ProcessingDict, JSONSchema, use_ipce_from_typelike_cache, REF_ATT, SCHEMA_ID,
                                  JSC_TITLE, JSC_TITLE_TYPE, SCHEMA_ATT, JSC_TYPE, JSC_NULL, PASS_THROUGH, JSC_OBJECT,
                                  JSC_PROPERTIES, JSC_ADDITIONAL_PROPERTIES, JSC_PROPERTY_NAMES, SCHEMA_CID,
                                  GlobalsDict, JSC_ARRAY, JSC_ITEMS, JSC_TITLE_CALLABLE, JSC_DEFINITIONS, JSC_STRING,
                                  JSC_BOOL, JSC_NUMBER, JSC_TITLE_FLOAT, JSC_INTEGER, JSC_TITLE_DECIMAL,
                                  JSC_TITLE_DATETIME, SCHEMA_BYTES, JSC_TITLE_NUMPY, JSC_TITLE_SLICE, ID_ATT,
                                  ATT_PYTHON_NAME, X_PYTHON_MODULE_ATT, JSC_DESCRIPTION, JSC_REQUIRED, X_CLASSVARS,
                                  X_CLASSATTS)
from zuper_ipce.schema_utils import get_all_refs, make_url, make_ref
from zuper_ipce.structures import FakeValues, Result, CannotResolveTypeVar
from zuper_ipce.ipce_attr import has_ipce_repr_attr, get_ipce_repr_attr, set_ipce_repr_attr
from zuper_ipce.ipce_spec import sorted_dict_with_cbor_ordering, assert_canonical_ipce
from zuper_ipce.pretty import pretty_dict
from zuper_typing.annotations_tricks import (get_Dict_name_K_V, get_Set_name_V, is_TupleLike, is_VarTuple,
                                             get_VarTuple_arg, get_Tuple_name, is_FixedTuple, get_FixedTuple_args,
                                             is_Callable, get_Callable_info, is_ForwardRef, get_ForwardRef_arg, is_Any,
                                             is_Union, is_Optional, is_Sequence, get_Sequence_arg, is_ClassVar,
                                             get_ClassVar_arg, get_Union_args, get_Optional_arg, is_Type)
from zuper_typing.constants import BINDINGS_ATT, GENERIC_ATT2, PYTHON_36
from zuper_typing.my_dict import (is_DictLike, get_DictLike_args, is_SetLike, get_SetLike_arg, is_ListLike,
                                  get_ListLike_arg, get_ListLike_name)
from zuper_typing.my_intersection import is_Intersection, get_Intersection_args
from zuper_typing.zeneric2 import get_name_without_brackets


def ipce_from_typelike(T: Any, globals0: dict, processing: ProcessingDict = None) -> JSONSchema:
    # pprint('type_to_schema', T=T)
    globals_ = dict(globals0)
    processing = processing or {}
    processing_refs = list(get_all_refs(processing))

    if hasattr(T, '__name__'):
        if T.__name__ in processing:
            return processing[T.__name__]

        if use_ipce_from_typelike_cache:
            if has_ipce_repr_attr(T, []):
                schema = get_ipce_repr_attr(T, [])
                # logger.info(f'T: {T.__name__} {schema["title"]}')
                return schema
            if has_ipce_repr_attr(T, processing_refs):
                schema = get_ipce_repr_attr(T, processing_refs)
                # logger.info(f'T: {T.__name__} {schema["title"]}')
                return schema

    try:

        if T is type:
            res = cast(JSONSchema, {
                  REF_ATT:   SCHEMA_ID,
                  JSC_TITLE: JSC_TITLE_TYPE
                  # JSC_DESCRIPTION: T.__doc__
                  })
            res = sorted_dict_with_cbor_ordering(res)
            return res

        if T is type(None):
            res = cast(JSONSchema, {
                  SCHEMA_ATT: SCHEMA_ID,
                  JSC_TYPE:   JSC_NULL
                  })
            res = sorted_dict_with_cbor_ordering(res)
            return res

        if isinstance(T, type):
            for klass in T.mro():
                if klass.__name__.startswith('Generic'):
                    continue
                if klass is object:
                    continue

                globals_[get_name_without_brackets(klass.__name__)] = klass

                bindings = getattr(klass, BINDINGS_ATT, {})
                for k, v in bindings.items():
                    if hasattr(v, '__name__') and v.__name__ not in globals_:
                        globals_[v.__name__] = v
                    globals_[k.__name__] = v

        schema = ipce_from_typelike_(T, globals_, processing)
        check_isinstance(schema, dict)
        # if '$ref' in schema:
        #     pass
        # else:
        #
        #     in_proc = set(get_all_refs(processing))
        #     # for k, v in processing.items():
        #     #     if isinstance(v, dict) and '$ref' in v:
        #     #
        #     refs_in_proc = in_proc & refs
        #     if refs_in_proc:
        #         logger.info(f'For {T} obtained refs_in_proc = {refs_in_proc}; not setting cache.')
        #     else:
        # # logger.info(f'processing = {processing}')
        # # if not processing:
        #     # if not is_Union(T):  # XXX
        #
        refs_in_schema = set(get_all_refs(schema))

        refs_in_proc = [x for x in processing_refs if x in refs_in_schema]
        if not refs_in_proc:
            set_ipce_repr_attr(T, [], schema)
        else:
            set_ipce_repr_attr(T, processing_refs, schema)
        # else:
        #     logger.info(f'ignorning setting cache for {T} because {processing}')

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
    try:
        assert_canonical_ipce(schema)
    except ValueError as e:
        msg = f'Invalid schema for {T}'
        raise ValueError(msg) from e
    return schema


def ipce_from_typelike_dict(T, globals_, processing) -> JSONSchema:
    assert is_DictLike(T), T
    K, V = get_DictLike_args(T)
    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Dict_name_K_V(K, V)
    if isinstance(K, type) and issubclass(K, str):
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        res[JSC_ADDITIONAL_PROPERTIES] = ipce_from_typelike(V, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        res = sorted_dict_with_cbor_ordering(res)
        return res
    else:
        res[JSC_PROPERTIES] = {SCHEMA_ATT: {}}  # XXX
        props = FakeValues[K, V]
        res[JSC_ADDITIONAL_PROPERTIES] = ipce_from_typelike(props, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        res = sorted_dict_with_cbor_ordering(res)
        return res


def ipce_from_typelike_SetLike(T, globals_, processing) -> JSONSchema:
    assert is_SetLike(T), T
    V = get_SetLike_arg(T)
    res = cast(JSONSchema, {JSC_TYPE: JSC_OBJECT})
    res[JSC_TITLE] = get_Set_name_V(V)
    res[JSC_PROPERTY_NAMES] = SCHEMA_CID
    res[JSC_ADDITIONAL_PROPERTIES] = ipce_from_typelike(V, globals_, processing)
    res[SCHEMA_ATT] = SCHEMA_ID
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_TupleLike(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_TupleLike(T), T

    if is_VarTuple(T):
        items = get_VarTuple_arg(T)
        # if args[-1] == Ellipsis:
        #     items = args[0]
        res = cast(JSONSchema, {})
        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = ipce_from_typelike(items, globals_, processing)
        res[JSC_TITLE] = get_Tuple_name(T)
        res = sorted_dict_with_cbor_ordering(res)
        return res
    elif is_FixedTuple(T):
        args = get_FixedTuple_args(T)
        res = cast(JSONSchema, {})

        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = []
        res[JSC_TITLE] = get_Tuple_name(T)
        for a in args:
            res[JSC_ITEMS].append(ipce_from_typelike(a, globals_, processing))
        res = sorted_dict_with_cbor_ordering(res)
        return res
    else:
        assert False


def ipce_from_typelike_ListLike(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_ListLike(T), T
    items = get_ListLike_arg(T)
    res = cast(JSONSchema, {})
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_ARRAY
    res[JSC_ITEMS] = ipce_from_typelike(items, globals_, processing)
    res[JSC_TITLE] = get_ListLike_name(T)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_Callable(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_Callable(T), T
    cinfo = get_Callable_info(T)

    res = cast(JSONSchema, {
          JSC_TYPE:  JSC_OBJECT, SCHEMA_ATT: SCHEMA_ID,
          JSC_TITLE: JSC_TITLE_CALLABLE,
          'special': 'callable'
          })

    p = res[JSC_DEFINITIONS] = {}
    for k, v in cinfo.parameters_by_name.items():
        p[k] = ipce_from_typelike(v, globals_, processing)
    p['return'] = ipce_from_typelike(cinfo.returns, globals_, processing)
    res['ordering'] = list(cinfo.ordering)
    # print(res)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    if T is None:
        raise ValueError('None is not a type!')

    # This can actually happen inside a Tuple (or Dict, etc.) even though
    # we have a special case for dataclass

    if is_ForwardRef(T):  # pragma: no cover
        arg = get_ForwardRef_arg(T)
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
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is bool:
        res = cast(JSONSchema, {JSC_TYPE: JSC_BOOL, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is Number:
        res = cast(JSONSchema, {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is float:
        res = cast(JSONSchema, {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: JSC_TITLE_FLOAT})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is int:
        res = cast(JSONSchema, {JSC_TYPE: JSC_INTEGER, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is slice:
        res = ipce_from_typelike_slice()
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is Decimal:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_DECIMAL, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is datetime.datetime:
        res = cast(JSONSchema, {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_DATETIME, SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if T is bytes:
        res = SCHEMA_BYTES
        res = sorted_dict_with_cbor_ordering(res)
        return res

    # we cannot use isinstance on typing.Any
    if is_Any(T):  # XXX not possible...
        res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
        res = sorted_dict_with_cbor_ordering(res)
        return res

    if is_Union(T):
        return ipce_from_typelike_Union(T, globals_, processing)

    if is_Optional(T):
        return ipce_from_typelike_Optional(T, globals_, processing)

    if is_DictLike(T):
        return ipce_from_typelike_dict(T, globals_, processing)

    if is_SetLike(T):
        return ipce_from_typelike_SetLike(T, globals_, processing)

    if is_Intersection(T):
        return ipce_from_typelike_Intersection(T, globals_, processing)

    if is_Callable(T):
        return ipce_from_typelike_Callable(T, globals_, processing)

    if is_Sequence(T):
        msg = ('Translating Sequence into List')
        warnings.warn(msg)
        # raise ValueError(msg)
        V = get_Sequence_arg(T)
        T = List[V]
        return ipce_from_typelike_ListLike(T, globals_, processing)

    if is_ListLike(T):
        return ipce_from_typelike_ListLike(T, globals_, processing)

    if is_TupleLike(T):
        # noinspection PyTypeChecker
        return ipce_from_typelike_TupleLike(T, globals_, processing)

    assert isinstance(T, type), T

    # if hasattr(T, GENERIC_ATT2) and is_generic(T):
    #     return ipce_from_typelike_generic(T, globals_, processing)

    if is_dataclass(T):
        return ipce_from_typelike_dataclass(T, globals_, processing)

    if T is np.ndarray:
        return ipce_from_typelike_ndarray(T, globals_, processing)

    msg = f'Cannot interpret this type: {T!r}'
    msg += f'\n   globals_: {globals_}'
    msg += f'\n processing: {processing}'
    raise ValueError(msg)


def ipce_from_typelike_ndarray(T, globals_, processing) -> JSONSchema:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_NUMPY
    res[JSC_PROPERTIES] = {
          'shape': {},  # TODO
          'dtype': {},  # TODO
          'data':  SCHEMA_BYTES
          }
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_slice() -> JSONSchema:
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID})
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_SLICE
    T = ipce_from_typelike(Optional[int], {}, {})
    properties = {
          'start': T,  # TODO
          'stop':  T,  # TODO
          'step':  T,
          }
    res[JSC_PROPERTIES] = sorted_dict_with_cbor_ordering(properties)
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_Intersection(T, globals_, processing):
    args = get_Intersection_args(T)
    options = [ipce_from_typelike(t, globals_, processing) for t in args]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "allOf": options})
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_dataclass(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    # from zuper_ipcl.debug_print_ import debug_print
    # d = {'processing': processing, 'globals_': globals_}
    # logger.info(f'type_dataclass_to_schema: {T} {debug_print(d)}')
    assert is_dataclass(T), T
    globals2 = dict(globals_)
    p2 = dict(processing)
    res = cast(JSONSchema, {})

    res[ID_ATT] = make_url(T.__name__)
    if hasattr(T, '__name__') and T.__name__:
        res[JSC_TITLE] = T.__name__

        p2[T.__name__] = make_ref(res[ID_ATT])

    if not hasattr(T, '__qualname__'):
        raise Exception(T)
    res[ATT_PYTHON_NAME] = T.__qualname__
    res[X_PYTHON_MODULE_ATT] = T.__module__
    # res[X_PYTHON_MODULE_ATT] = T.__qualname__

    res[SCHEMA_ATT] = SCHEMA_ID

    res[JSC_TYPE] = JSC_OBJECT

    if hasattr(T, '__doc__') and T.__doc__:
        res[JSC_DESCRIPTION] = T.__doc__

    if hasattr(T, GENERIC_ATT2):
        definitions = {}
        types2 = getattr(T, GENERIC_ATT2)
        for t2 in types2:
            if not isinstance(t2, TypeVar):
                continue

            url = make_url(f'{T.__name__}/{t2.__name__}')

            # processing2[f'~{name}'] = {'$ref': url}
            p2[f'{t2.__name__}'] = make_ref(url)
            # noinspection PyTypeHints
            globals2[t2.__name__] = t2

            bound = t2.__bound__ or Any
            schema = ipce_from_typelike(bound, globals2, p2)
            schema = copy.copy(schema)
            schema[ID_ATT] = url

            definitions[t2.__name__] = schema

            globals_[t2.__name__] = t2

        if definitions:
            res[JSC_DEFINITIONS] = sorted_dict_with_cbor_ordering(definitions)

    properties = {}
    classvars = {}
    classatts = {}

    required = []
    fields_ = getattr(T, _FIELDS)
    # noinspection PyUnusedLocal
    afield: Field
    from zuper_ipce.conv_ipce_from_object import ipce_from_object

    names = list(fields_)
    ordered = sorted(names)

    for name in ordered:
        afield = fields_[name]

        t = afield.type

        try:
            if isinstance(t, str):
                t = eval_just_string(t, globals_)

            if is_ClassVar(t):
                tt = get_ClassVar_arg(t)

                result = eval_field(tt, globals2, p2)
                classvars[name] = result.schema

                if hasattr(T, name):
                    # special case
                    the_att = getattr(T, name)

                    if isinstance(the_att, type):
                        classatts[name] = ipce_from_typelike(the_att, globals2, processing)

                    else:
                        classatts[name] = ipce_from_object(the_att, globals2)

            else:

                result = eval_field(t, globals2, p2)
                if not result.optional:
                    required.append(name)
                # result.schema['qui'] = 1
                properties[name] = result.schema

                if not result.optional:
                    if not isinstance(afield.default, dataclasses._MISSING_TYPE):
                        # logger.info(f'default for {name} is {afield.default}')
                        properties[name] = copy.copy(properties[name])
                        properties[name]['default'] = ipce_from_object(afield.default, globals2)
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

    if properties:
        res[JSC_PROPERTIES] = sorted_dict_with_cbor_ordering(properties)

    res['order'] = names

    res = sorted_dict_with_cbor_ordering(res)
    # res['sroted'] = 1
    return res


def ipce_from_typelike_Union(t, globals_, processing):
    types = get_Union_args(t)
    options = [ipce_from_typelike(t, globals_, processing) for t in types]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "anyOf": options})
    res = sorted_dict_with_cbor_ordering(res)
    return res


def ipce_from_typelike_Optional(t, globals_, processing):
    types = [get_Optional_arg(t), type(None)]
    options = [ipce_from_typelike(t, globals_, processing) for t in types]
    res = cast(JSONSchema, {SCHEMA_ATT: SCHEMA_ID, "anyOf": options})
    res = sorted_dict_with_cbor_ordering(res)
    return res


#
# def ipce_from_typelike_generic(T: Type, globals_: GlobalsDict, processing_: ProcessingDict) -> JSONSchema:
#     assert hasattr(T, GENERIC_ATT2)
#
#     types2 = getattr(T, GENERIC_ATT2)
#     processing2 = dict(processing_)
#     globals2 = dict(globals_)
#
#     res = cast(JSONSchema, {})
#     res[SCHEMA_ATT] = SCHEMA_ID
#
#     res[JSC_TITLE] = T.__name__
#     # res[ATT_PYTHON_NAME] = T.__qualname__
#     res[X_PYTHON_MODULE_ATT] = T.__module__
#
#     res[ID_ATT] = make_url(T.__name__)
#
#     res[JSC_TYPE] = JSC_OBJECT
#
#     processing2[f'{T.__name__}'] = make_ref(res[ID_ATT])
#
#     # print(f'T: {T.__name__} ')
#     definitions = {}
#
#     if hasattr(T, '__doc__') and T.__doc__:
#         res[JSC_DESCRIPTION] = T.__doc__
#     globals_ = dict(globals_)
#     for t2 in types2:
#         if not isinstance(t2, TypeVar):
#             continue
#
#         url = make_url(f'{T.__name__}/{t2.__name__}')
#
#         # processing2[f'~{name}'] = {'$ref': url}
#         processing2[f'{t2.__name__}'] = make_ref(url)
#         # noinspection PyTypeHints
#         globals2[t2.__name__] = t2
#
#         bound = t2.__bound__ or Any
#         schema = ipce_from_typelike(bound, globals2, processing2)
#         schema = copy.copy(schema)
#         schema[ID_ATT] = url
#
#         definitions[t2.__name__] = schema
#
#         globals_[t2.__name__] = t2
#
#     if definitions:
#         res[JSC_DEFINITIONS] = definitions
#     properties = {}
#     required = []
#
#     # names = list(T.__annotations__)
#     # ordered = sorted(names)
#     original_order = []
#     for name, t in T.__annotations__.items():
#         t = replace_typevars(t, bindings={}, symbols=globals_, rl=None)
#         if is_ClassVar(t):
#             continue
#         try:
#             result = eval_field(t, globals2, processing2)
#         except PASS_THROUGH:
#             raise
#         except BaseException as e:
#             msg = f'Cannot evaluate field "{name}" of class {T} annotated as {t}'
#             raise Exception(msg) from e
#         assert isinstance(result, Result), result
#         properties[name] = result.schema
#         original_order.append(name)
#         if not result.optional:
#             required.append(name)
#     if required:
#         res[JSC_REQUIRED] = sorted(required)
#
#     sorted_vars = sorted(original_order)
#     res[JSC_PROPERTIES] = {k: properties[k] for k in sorted_vars}
#     res['order'] = original_order
#     res = sorted_dict_with_cbor_ordering(res)
#     return res
def eval_field(t, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    debug_info2 = lambda: dict(globals_=globals_, processing=processing)

    if isinstance(t, str):
        te = eval_type_string(t, globals_, processing)
        return te

    if is_Type(t):
        res = cast(JSONSchema, make_ref(SCHEMA_ID))
        return Result(res)

    if is_TupleLike(t):
        res = ipce_from_typelike_TupleLike(t, globals_, processing)
        return Result(res)

    if is_ListLike(t):
        res = ipce_from_typelike_ListLike(t, globals_, processing)
        return Result(res)

    if is_DictLike(t):
        schema = ipce_from_typelike_dict(t, globals_, processing)
        return Result(schema)

    if is_SetLike(t):
        schema = ipce_from_typelike_SetLike(t, globals_, processing)
        return Result(schema)

    if is_ForwardRef(t):
        tn = get_ForwardRef_arg(t)
        return eval_type_string(tn, globals_, processing)

    if is_Optional(t):
        tt = get_Optional_arg(t)
        result = eval_field(tt, globals_, processing)
        return Result(result.schema, optional=True)

    if is_Union(t):
        return Result(ipce_from_typelike_Union(t, globals_, processing))

    if is_Any(t):
        res = cast(JSONSchema, {'$schema': 'http://json-schema.org/draft-07/schema#'})
        return Result(res)

    if isinstance(t, TypeVar):
        l = t.__name__
        if l in processing:
            return Result(processing[l])
        # I am not sure why this is different in Python 3.6
        if PYTHON_36 and (l in globals_):  # pragma: no cover
            T = globals_[l]
            return Result(ipce_from_typelike(T, globals_, processing))

        m = f'Could not resolve the TypeVar {t}'
        msg = pretty_dict(m, debug_info2())
        raise CannotResolveTypeVar(msg)

    if isinstance(t, type):
        # catch recursion here
        if t.__name__ in processing:
            return eval_field(t.__name__, globals_, processing)
        else:
            schema = ipce_from_typelike(t, globals_, processing)
            return Result(schema)

    msg = f'Could not deal with {t}'
    msg += f'\nglobals: {globals_}'
    msg += f'\nprocessing: {processing}'
    raise NotImplementedError(msg)


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
