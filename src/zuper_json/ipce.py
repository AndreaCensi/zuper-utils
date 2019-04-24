import hashlib
import inspect
import traceback
import typing
from dataclasses import make_dataclass, _FIELDS, field, Field, dataclass, is_dataclass
from numbers import Number
from typing import Type, Dict, Any, TypeVar, Optional, ClassVar, cast, Union, \
    Generic, List, Tuple, Callable

import base58
import cbor2
import numpy as np
from mypy_extensions import NamedArg
from nose.tools import assert_in
from decimal import Decimal
from contracts import check_isinstance, raise_desc, indent
from jsonschema.validators import validator_for, validate
from .annotations_tricks import is_optional, get_optional_type, is_forward_ref, get_forward_ref_arg, is_Any, \
    is_ClassVar, get_ClassVar_arg, is_Type, is_Callable, get_Callable_info, get_union_types, is_union, is_Dict, \
    get_Dict_name_K_V, is_Tuple, get_List_arg, is_List
from .base64_utils import decode_bytes_base64, is_encoded_bytes_base64
from .constants import X_PYTHON_MODULE_ATT, ATT_PYTHON_NAME, SCHEMA_BYTES, GlobalsDict, JSONSchema, _SpecialForm, \
    ProcessingDict, EncounteredDict, SCHEMA_ATT, SCHEMA_ID, JSC_TYPE, JSC_STRING, JSC_NUMBER, JSC_OBJECT, JSC_TITLE, \
    JSC_ADDITIONAL_PROPERTIES, JSC_DESCRIPTION, JSC_PROPERTIES, GENERIC_ATT, BINDINGS_ATT, JSC_INTEGER, ID_ATT, \
    JSC_DEFINITIONS, REF_ATT, JSC_REQUIRED, X_CLASSVARS, X_CLASSATTS, JSC_BOOL, PYTHON_36, JSC_TITLE_NUMPY, JSC_NULL, \
    JSC_TITLE_BYTES, JSC_ARRAY, JSC_ITEMS, JSC_DEFAULT
from .my_dict import make_dict, CustomDict
from .my_intersection import is_Intersection, get_Intersection_args, Intersection
from .numpy_encoding import numpy_from_dict, dict_from_numpy
from .pretty import pretty_dict
from .types import MemoryJSON


def object_to_ipce(ob, globals_: GlobalsDict, suggest_type=None, with_schema=True) -> MemoryJSON:
    # logger.debug(f'object_to_ipce({ob})')
    res = object_to_ipce_(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)
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


def object_to_ipce_(ob, globals_: GlobalsDict, with_schema: bool, suggest_type: Type = None,
                    ) -> MemoryJSON:
    """
        Converts to an in-memory JSON representation

    """
    if isinstance(ob, (int, str, float, type(None))):
        return ob

    if isinstance(ob, list):
        suggest_type_l = None  # XXX
        return [object_to_ipce(_, globals_, suggest_type=suggest_type_l, with_schema=with_schema) for _ in ob]

    if isinstance(ob, tuple):
        suggest_type_l = None  # XXX
        return [object_to_ipce(_, globals_, suggest_type=suggest_type_l, with_schema=with_schema) for _ in ob]

    if isinstance(ob, bytes):
        # json will later be converted
        return ob

    if isinstance(ob, dict):
        return dict_to_ipce(ob, globals_, suggest_type=suggest_type, with_schema=with_schema)

    if isinstance(ob, type):
        return type_to_schema(ob, globals_, processing={})

    if is_Any(ob) or is_List(ob) or is_Dict(ob):
        # TODO: put more here
        return type_to_schema(ob, globals_, processing={})

    if isinstance(ob, np.ndarray):
        res = dict_from_numpy(ob)
        if with_schema:
            res[SCHEMA_ATT] = type_numpy_to_schema(type(ob), globals_, {})
        return res

    if isinstance(ob, Decimal):
        return ob

    return serialize_dataclass(ob, globals_, with_schema=with_schema)


import dataclasses


def serialize_dataclass(ob, globals_, with_schema: bool):
    globals_ = dict(globals_)
    res = {}
    T = type(ob)
    the_schema = type_to_schema(T, globals_)

    if with_schema:
        res[SCHEMA_ATT] = the_schema

    globals_[T.__name__] = K

    for f in dataclasses.fields(ob):
        k = f.name
        ann = f.type
        ann = resolve_all(ann, globals_)

        if is_ClassVar(ann):
            continue

        v = getattr(ob, k)

        if v is None:
            if is_optional(ann):
                continue
            # else:
            #     print('v is None but not optional: %s %s' % (ann, (ann).__dict__))
        try:
            if is_optional(ann):
                ann = get_optional_type(ann)
            res[k] = object_to_ipce(v, globals_, suggest_type=ann, with_schema=with_schema)
        except BaseException as e:
            msg = f'Cannot serialize attribute {k} = {v} of type {type(k)}.'
            msg += f'\nThe schema for {type(ob)} says that it should be of type {ann}.'
            raise Exception(msg) from e
    return res


def resolve_all(T, globals_):
    """
        Returns either a type or a genericalias


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


def dict_to_ipce(ob, globals_, suggest_type: type, with_schema: bool):
    # assert suggest_type is not None
    res = {}
    # pprint('suggest_type ', suggest_type=suggest_type)

    if is_Dict(suggest_type):
        # noinspection PyUnresolvedReferences
        K, V = suggest_type.__args__
    elif isinstance(suggest_type, type) and issubclass(suggest_type, CustomDict):
        K, V = suggest_type.__dict_type__
    elif (suggest_type is None) or is_Any(suggest_type):
        all_str = all(type(_) is str for _ in ob)
        if all_str:
            K = str
        else:
            K = Any
        V = Any
        suggest_type = Dict[K, V]
    else:  # pragma: no cover
        assert False, suggest_type

    if with_schema:
        res[SCHEMA_ATT] = type_to_schema(suggest_type, globals_)

    if isinstance(K, type) and issubclass(K, str):
        for k, v in ob.items():
            res[k] = object_to_ipce(v, globals_, suggest_type=None, with_schema=with_schema)
    else:
        FV = FakeValues[K, V]
        for k, v in ob.items():
            # vj = object_to_ipce(v, globals_)
            kj = object_to_ipce(k, globals_)
            if isinstance(k, int):
                h = str(k)
            else:
                h = get_sha256_base58(cbor2.dumps(kj)).decode('ascii')
                # from zuper_ipce.register import hash_from_string
                # h = hash_from_string(json.dumps(kj)).hash
            # pprint(kj=kj, vj=vj)
            fv = FV(k, v)
            res[h] = object_to_ipce(fv, globals_, with_schema=with_schema)

    return res


def get_sha256_base58(contents):
    import hashlib
    m = hashlib.sha256()
    m.update(contents)
    s = m.digest()
    return base58.b58encode(s)


def ipce_to_object(mj: MemoryJSON,
                   global_symbols,
                   encountered: Optional[dict] = None,
                   expect_type: Optional[type] = None) -> object:
    encountered = encountered or {}

    # logger.debug(f'ipce_to_object expect {expect_type} mj {mj}')

    if isinstance(mj, (int, float, bool, Decimal)):
        return mj

    if isinstance(mj, list):
        if expect_type and is_Tuple(expect_type):
            return deserialize_tuple(expect_type, mj, global_symbols, encountered)
        else:
            seq = [ipce_to_object(_, global_symbols, encountered) for _ in mj]
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

    if expect_type is bytes:
        if isinstance(mj, bytes):
            return mj
        # elif isinstance(mj, dict):
        #
        #     data = mj['base64']
        #     res = pybase64.b64decode(data)
        #     assert isinstance(res, bytes)
        #     return res
        elif isinstance(mj, str) and is_encoded_bytes_base64(mj):
            # This should not be necessary anymore
            return decode_bytes_base64(mj)
        else:
            assert False, mj

    # note str at the end, because it could be encoded bytes/array

    if isinstance(mj, str):
        if is_encoded_bytes_base64(mj):
            return decode_bytes_base64(mj)
        else:
            return mj

    assert isinstance(mj, dict), type(mj)

    if mj.get(SCHEMA_ATT, '') == SCHEMA_ID:
        schema: JSONSchema = mj
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
        K = get_optional_type(K)

        return ipce_to_object(mj,
                              global_symbols,
                              encountered,
                              expect_type=K)

    if (isinstance(K, type) and issubclass(K, dict)) or is_Dict(K) or \
            (isinstance(K, type) and issubclass(K, CustomDict)):
        # logger.info(f'deserialize as dict ')
        return deserialize_Dict(K, mj, global_symbols, encountered)
    else:
        pass
        # logger.info(f'{K} is not dict ')
    if is_dataclass(K):
        return deserialize_dataclass(K, mj, global_symbols, encountered)

    if is_union(K):
        errors = []
        for T in get_union_types(K):
            try:
                return ipce_to_object(mj,
                                      global_symbols,
                                      encountered,
                                      expect_type=T)
            except BaseException as e:
                errors.append(e)
        msg = f'Cannot deserialize with any of {get_union_types(K)}'
        msg += '\n'.join(str(e) for e in errors)
        raise Exception(msg)

    assert False, (type(K), K, mj, expect_type)  # pragma: no cover


def deserialize_tuple(expect_type, mj, global_symbols, encountered):
    seq = []
    for i, ob in enumerate(mj):
        expect_type_i = expect_type.__args__[i]
        seq.append(ipce_to_object(ob, global_symbols, encountered, expect_type=expect_type_i))

    return tuple(seq)


def deserialize_dataclass(K, mj, global_symbols, encountered):
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
    for k, v in mj.items():
        if k in anns:
            expect_type = anns[k]
            expect_type = resolve_all(expect_type, global_symbols)
            if is_optional(expect_type):
                expect_type = get_optional_type(expect_type)

            if inspect.isabstract(expect_type):
                msg = f'Trying to instantiate abstract class {expect_type} for field "{k}" of class {K}'

                raise_desc(Exception, msg, annotation=anns[k])

            try:
                attrs[k] = ipce_to_object(v, global_symbols, encountered, expect_type=expect_type)
            except BaseException as e:
                msg = f'Cannot deserialize attribute {k} (expect: {expect_type})'
                msg += f'\nvalue: {v!r}'
                msg += '\n\n' + indent(traceback.format_exc(), '| ')
                raise Exception(msg) from e

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

    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        if issubclass(K, str):
            attrs[k] = ipce_to_object(v, global_symbols, encountered, expect_type=V)
        else:
            attrs[k] = ipce_to_object(v, global_symbols, encountered, expect_type=FV)

    if isinstance(K, type) and issubclass(K, str):
        ob.update(attrs)
        return ob
    else:
        for k, v in attrs.items():
            # noinspection PyUnresolvedReferences
            ob[v.real_key] = v.value
        return ob


class CannotFindSchemaReference(ValueError):
    pass


class CannotResolveTypeVar(ValueError):
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

    res = schema_to_type_(schema0, global_symbols, encountered)
    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        encountered[schema_id] = res
        # print(f'Found {schema_id} -> {res}')

    schema_cache[h] = res
    return res


def schema_to_type_(schema0: JSONSchema, global_symbols: Dict, encountered: Dict) -> Union[Type, _SpecialForm]:
    # pprint('schema_to_type_', schema0=schema0)
    encountered = encountered or {}
    info = dict(global_symbols=global_symbols, encountered=encountered)
    check_isinstance(schema0, dict)
    schema: JSONSchema = dict(schema0)
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

    if "anyOf" in schema:
        options = schema["anyOf"]
        args = [schema_to_type(_, global_symbols, encountered) for _ in options]
        return Union[tuple(args)]

    if "allOf" in schema:
        options = schema["allOf"]
        args = [schema_to_type(_, global_symbols, encountered) for _ in options]
        res = Intersection[tuple(args)]
        return res

    jsc_type = schema.get(JSC_TYPE, None)
    jsc_title = schema.get(JSC_TITLE, '-not-provided-')
    if jsc_title == JSC_TITLE_NUMPY:
        return np.ndarray
    if schema0 == SCHEMA_BYTES:
        return bytes

    if jsc_type == JSC_STRING:
        if jsc_title == JSC_TITLE_BYTES:
            return bytes
        elif jsc_title == 'decimal':
            return Decimal
        else:
            return str
    elif jsc_type == JSC_NULL:
        return type(None)

    elif jsc_type == JSC_BOOL:
        return bool

    elif jsc_type == JSC_NUMBER:
        if jsc_title == 'float':
            return float
        else:
            return Number

    elif jsc_type == JSC_INTEGER:
        return int

    elif jsc_type == JSC_OBJECT:
        if jsc_title == 'Callable':
            return schema_to_type_callable(schema, global_symbols, encountered)
        if jsc_title.startswith('Dict'):
            return schema_dict_to_DictType(schema, global_symbols, encountered)
        elif JSC_DEFINITIONS in schema:
            return schema_to_type_generic(schema, global_symbols, encountered)
        elif ATT_PYTHON_NAME in schema:
            tn = schema[ATT_PYTHON_NAME]
            if tn in global_symbols:
                return global_symbols[tn]
            else:
                # logger.debug(f'did not find {tn} in {global_symbols}')
                return schema_to_type_dataclass(schema, global_symbols, encountered)

        assert False, schema  # pragma: no cover
    elif jsc_type == JSC_ARRAY:
        return schema_array_to_type(schema, global_symbols, encountered)

    assert False, schema  # pragma: no cover


def schema_array_to_type(schema, global_symbols, encountered):
    items = schema['items']
    if isinstance(items, list):
        assert len(items) > 0
        args = tuple([schema_to_type(_, global_symbols, encountered) for _ in items])

        if PYTHON_36:  # pragma: no cover
            return typing.Tuple[args]
        else:
            # noinspection PyArgumentList
            return Tuple.__getitem__(args)
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
    D = make_dict(K, V)
    # we never put it anyway
    # if JSC_DESCRIPTION in schema:
    #     setattr(D, '__doc__', schema[JSC_DESCRIPTION])
    return D


JSC_TITLE_TYPE = 'type'


def type_to_schema(T: Any, globals0: dict, processing: ProcessingDict = None) -> JSONSchema:
    # pprint('type_to_schema', T=T)
    globals_ = dict(globals0)
    try:
        if T is type:
            res: JSONSchema = {REF_ATT: SCHEMA_ID,
                               JSC_TITLE: JSC_TITLE_TYPE
                               # JSC_DESCRIPTION: T.__doc__
                               }
            return res

        if T is type(None):
            res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID,
                               JSC_TYPE: JSC_NULL}
            return res

        if isinstance(T, type):
            for K in T.mro():
                if K.__name__.startswith('Generic'):
                    continue
                if K is object:
                    continue

                globals_[K.__name__] = K

                bindings = getattr(K, BINDINGS_ATT, {})
                for k, v in bindings.items():
                    if hasattr(v, '__name__') and v.__name__ not in globals_:
                        globals_[v.__name__] = v
                    globals_[k.__name__] = v

        processing = processing or {}
        schema = type_to_schema_(T, globals_, processing)
        check_isinstance(schema, dict)
    except (ValueError, NotImplementedError, AssertionError) as e:
        m = f'Cannot get schema for {T}'
        msg = pretty_dict(m, dict(  # globals0=globals0,
                # globals=globals_,
                processing=processing))
        msg += '\n' + traceback.format_exc()
        raise type(e)(msg) from e
    except BaseException as e:
        m = f'Cannot get schema for {T}'
        msg = pretty_dict(m, dict(  # globals0=globals0,
                # globals=globals_,
                processing=processing))
        raise TypeError(msg) from e

    assert_in(SCHEMA_ATT, schema)
    assert schema[SCHEMA_ATT] in [SCHEMA_ID]
    # assert_equal(schema[SCHEMA_ATT], SCHEMA_ID)
    if schema[SCHEMA_ATT] == SCHEMA_ID:
        cls = validator_for(schema)
        cls.check_schema(schema)
    return schema


K = TypeVar('K')
V = TypeVar('V')


@dataclass
class FakeValues(Generic[K, V]):
    real_key: K
    value: V


def dict_to_schema(T, globals_, processing) -> JSONSchema:
    assert is_Dict(T) or issubclass(T, CustomDict)

    if is_Dict(T):
        K, V = T.__args__
    elif issubclass(T, CustomDict):
        K, V = T.__dict_type__
    else:  # pragma: no cover
        assert False

    res: JSONSchema = {JSC_TYPE: JSC_OBJECT}
    res[JSC_TITLE] = get_Dict_name_K_V(K, V)
    if isinstance(K, type) and issubclass(K, str):
        res[JSC_PROPERTIES] = {"$schema": {}}  # XXX
        res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(V, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        return res
    else:
        res[JSC_PROPERTIES] = {"$schema": {}}  # XXX
        props = FakeValues[K, V]
        res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(props, globals_, processing)
        res[SCHEMA_ATT] = SCHEMA_ID
        return res


def Tuple_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_Tuple(T)
    args = T.__args__
    if args[-1] == Ellipsis:
        items = args[0]
        res: JSONSchema = {}
        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = type_to_schema(items, globals_, processing)
        res[JSC_TITLE] = 'Tuple'
        return res
    else:
        res: JSONSchema = {}

        res[SCHEMA_ATT] = SCHEMA_ID
        res[JSC_TYPE] = JSC_ARRAY
        res[JSC_ITEMS] = []
        res[JSC_TITLE] = 'Tuple'
        for a in args:
            res[JSC_ITEMS].append(type_to_schema(a, globals_, processing))
        return res


def List_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_List(T)
    items = get_List_arg(T)
    res: JSONSchema = {}
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_ARRAY
    res[JSC_ITEMS] = type_to_schema(items, globals_, processing)
    res[JSC_TITLE] = 'List'
    return res


def type_callable_to_schema(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_Callable(T)
    cinfo = get_Callable_info(T)
    # res: JSONSchema = {JSC_TYPE: X_TYPE_FUNCTION, SCHEMA_ATT: X_SCHEMA_ID}
    res: JSONSchema = {JSC_TYPE: JSC_OBJECT, SCHEMA_ATT: SCHEMA_ID,
                       JSC_TITLE: "Callable",
                       'special': 'callable'}

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
        if not k.startswith('#'):
            d = NamedArg(d, k)
        others.append(d)

    # noinspection PyTypeHints
    return Callable[others, ret]


def type_to_schema_(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    if is_optional(T):  # pragma: no cover
        msg = f'Should not be needed to have an Optional here yet: {T}'
        raise AssertionError(msg)

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
        res: JSONSchema = {JSC_TYPE: JSC_STRING, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is bool:
        res: JSONSchema = {JSC_TYPE: JSC_BOOL, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is Number:
        res: JSONSchema = {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is float:
        res: JSONSchema = {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID, JSC_TITLE: "float"}
        return res

    if T is int:
        res: JSONSchema = {JSC_TYPE: JSC_INTEGER, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is Decimal:
        res: JSONSchema = {JSC_TYPE: JSC_STRING, JSC_TITLE: "decimal", SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is bytes:
        return SCHEMA_BYTES

    # we cannot use isinstance on typing.Any
    if is_Any(T):  # XXX not possible...
        res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID}
        return res

    if is_union(T):
        return schema_Union(T, globals_, processing)

    if is_Dict(T) or (isinstance(T, type) and issubclass(T, CustomDict)):
        return dict_to_schema(T, globals_, processing)

    if is_Intersection(T):
        return schema_Intersection(T, globals_, processing)

    if is_Callable(T):
        return type_callable_to_schema(T, globals_, processing)

    if is_List(T):
        return List_to_schema(T, globals_, processing)

    if is_Tuple(T):
        return Tuple_to_schema(T, globals_, processing)

    assert isinstance(T, type), T

    if issubclass(T, dict):  # pragma: no cover
        msg = f'A regular "dict" slipped through.\n{T}'
        raise TypeError(msg)

    if hasattr(T, GENERIC_ATT) and getattr(T, GENERIC_ATT) is not None:
        return type_generic_to_schema(T, globals_, processing)

    if is_dataclass(T):
        return type_dataclass_to_schema(T, globals_, processing)

    if T is np.ndarray:
        return type_numpy_to_schema(T, globals_, processing)

    msg = 'Cannot interpret this type. (not a dataclass): %s' % T
    raise ValueError(msg)


def type_numpy_to_schema(T, globals_, processing) -> JSONSchema:
    res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID}
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = JSC_TITLE_NUMPY
    res[JSC_PROPERTIES] = {
        'shape': {},  # TODO
        'dtype': {},  # TODO
        'data': SCHEMA_BYTES
    }

    return res


def schema_Intersection(T, globals_, processing):
    args = get_Intersection_args(T)
    options = [type_to_schema(t, globals_, processing) for t in args]
    res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID, "allOf": options}
    return res


def schema_to_type_generic(res: JSONSchema, global_symbols: dict, encountered: dict) -> Type:
    assert res[JSC_TYPE] == JSC_OBJECT
    assert JSC_DEFINITIONS in res
    cls_name = res[JSC_TITLE]

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

    fields = []  # (name, type, Field)
    for pname, v in res.get(JSC_PROPERTIES, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)

        if pname in required:
            _Field = field()
        else:
            _Field = field(default=None)
            ptype = Optional[ptype]

        fields.append((pname, ptype, _Field))

    T = make_dataclass(cls_name, fields, bases=(base,), namespace=None, init=True, repr=True, eq=True, order=False,
                       unsafe_hash=False, frozen=False)

    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    if ATT_PYTHON_NAME in res:
        setattr(T, '__qualname__', res[ATT_PYTHON_NAME])
    if X_PYTHON_MODULE_ATT in res:
        setattr(T, '__module__', res[X_PYTHON_MODULE_ATT])
    return T


def type_generic_to_schema(T: Type, globals_: GlobalsDict, processing_: ProcessingDict) -> JSONSchema:
    assert hasattr(T, GENERIC_ATT)

    types = getattr(T, GENERIC_ATT)
    processing2 = dict(processing_)
    globals2 = dict(globals_)

    res: JSONSchema = {}
    res[SCHEMA_ATT] = SCHEMA_ID

    res[JSC_TITLE] = T.__name__
    res[ATT_PYTHON_NAME] = T.__qualname__
    res[X_PYTHON_MODULE_ATT] = T.__module__

    res[ID_ATT] = make_url(T.__name__)

    res[JSC_TYPE] = JSC_OBJECT

    processing2[f'{T.__name__}'] = make_ref(res[ID_ATT])

    # print(f'T: {T.__name__} ')
    res[JSC_DEFINITIONS] = definitions = {}

    if hasattr(T, '__doc__') and T.__doc__:
        res[JSC_DESCRIPTION] = T.__doc__

    for name, bound in types.items():
        url = make_url(f'{T.__name__}/{name}')

        # processing2[f'~{name}'] = {'$ref': url}
        processing2[f'{name}'] = make_ref(url)
        # noinspection PyTypeHints
        globals2[name] = TypeVar(name, bound=bound)

        schema = type_to_schema(bound, globals2, processing2)
        schema[ID_ATT] = url

        definitions[name] = schema

    res[JSC_PROPERTIES] = properties = {}
    required = []
    for name, t in T.__annotations__.items():
        if is_ClassVar(t):
            continue

        try:
            result = eval_field(t, globals2, processing2)
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
    res: JSONSchema = {}

    res[ID_ATT] = make_url(T.__name__)
    if hasattr(T, '__name__') and T.__name__:
        res[JSC_TITLE] = T.__name__

        p2[T.__name__] = make_ref(res[ID_ATT])

    res[ATT_PYTHON_NAME] = T.__qualname__
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
                classatts[name] = object_to_ipce(the_att, globals_)

        else:

            result = eval_field(t, globals_, p2)
            if not result.optional:
                required.append(name)
            properties[name] = result.schema

            if not result.optional:
                if not isinstance(afield.default, dataclasses._MISSING_TYPE):
                    # logger.info(f'default for {name} is {afield.default}')
                    properties[name]['default'] = object_to_ipce(afield.default, globals_)

    if required:  # empty is error
        res[JSC_REQUIRED] = required
    if classvars:
        res[X_CLASSVARS] = classvars
    if classatts:
        res[X_CLASSATTS] = classatts

    return res


@dataclass
class Result:
    schema: JSONSchema
    optional: Optional[bool] = False


# TODO: make url generic
def make_url(x: str):
    assert isinstance(x, str), x
    return f'http://invalid.json-schema.org/{x}#'


def make_ref(x: str):
    assert len(x) > 1, x
    assert isinstance(x, str), x
    return {REF_ATT: x}


def eval_field(t, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    debug_info2 = lambda: dict(globals_=globals_, processing=processing)

    if isinstance(t, str):
        te = eval_type_string(t, globals_, processing)
        return te

    if is_Type(t):
        res: JSONSchema = make_ref(SCHEMA_ID)
        return Result(res)

    if is_Tuple(t):
        res = Tuple_to_schema(t, globals_, processing)
        return Result(res)

    if is_List(t):
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
        schema: JSONSchema = {}
        return Result(schema)

    if is_Dict(t):
        schema = dict_to_schema(t, globals_, processing)
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

    assert False, t  # pragma: no cover


def schema_Union(t, globals_, processing):
    types = get_union_types(t)
    options = [type_to_schema(t, globals_, processing) for t in types]
    res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID, "anyOf": options}
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
        except BaseException as e:  # pragma: no cover
            m = 'Could not evaluate type string'
            msg = pretty_dict(m, debug_info())
            raise ValueError(msg) from e


def eval_just_string(t: str, globals_):
    from typing import Optional
    eval_locals = {'Optional': Optional}
    # TODO: put more above?
    # do not pollute environment
    if t in globals_:
        return globals_[t]
    eval_globals = dict(globals_)
    try:
        res = eval(t, eval_globals, eval_locals)
        return res
    except BaseException as e:
        m = f'Error while evaluating the string {t!r} using eval().'
        msg = pretty_dict(m, dict(eval_locals=eval_locals, eval_globals=eval_globals))
        raise type(e)(msg) from e


def schema_to_type_dataclass(res: JSONSchema, global_symbols: dict, encountered: EncounteredDict) -> Type:
    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]
    # It's already done by the calling function
    # if ID_ATT in res:
    #     # encountered[res[ID_ATT]] = ForwardRef(cls_name)
    #     encountered[res[ID_ATT]] = cls_name

    required = res.get(JSC_REQUIRED, [])

    fields = []  # (name, type, Field)
    for pname, v in res.get(JSC_PROPERTIES, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)
        # assert isinstance(ptype)
        if pname in required:
            _Field = field()
        else:
            _Field = field(default=None)
            ptype = Optional[ptype]

        if JSC_DEFAULT in v:
            default_value = ipce_to_object(v[JSC_DEFAULT], global_symbols, expect_type=ptype)
            _Field.default = default_value

        fields.append((pname, ptype, _Field))

    for pname, v in res.get(X_CLASSVARS, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)
        fields.append((pname, ClassVar[ptype], field()))

    unsafe_hash = True
    T = make_dataclass(cls_name, fields, bases=(), namespace=None, init=True, repr=True, eq=True, order=False,
                       unsafe_hash=unsafe_hash, frozen=False)

    for pname, v in res.get(X_CLASSATTS, {}).items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = schema_to_type(cast(JSONSchema, v), global_symbols, encountered)
        else:
            interpreted = ipce_to_object(v, global_symbols)
        setattr(T, pname, interpreted)

    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    else:
        # the original one did not have it
        setattr(T, '__doc__', None)

    if ATT_PYTHON_NAME in res:
        setattr(T, '__qualname__', res[ATT_PYTHON_NAME])

    if X_PYTHON_MODULE_ATT in res:
        setattr(T, '__module__', res[X_PYTHON_MODULE_ATT])
    return T
