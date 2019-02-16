import json
import sys
import typing
from dataclasses import make_dataclass, _FIELDS, field, Field, dataclass, is_dataclass
from numbers import Number
from typing import Type, Dict, Any, TypeVar, Optional, NewType, ClassVar, cast, Union, \
    Generic, List, Tuple, Callable

_SpecialForm = Any
from contracts import check_isinstance
from jsonschema.validators import validator_for, validate
from mypy_extensions import NamedArg
from nose.tools import assert_in

from zuper_json.my_dict import make_dict, CustomDict
from zuper_json.my_intersection import is_Intersection, get_Intersection_args, Intersection
from zuper_json.register import hash_from_string
from .annotations_tricks import is_optional, get_optional_type, is_forward_ref, get_forward_ref_arg, is_Any, \
    is_ClassVar, get_ClassVar_arg, is_Type, is_Callable, get_Callable_info, get_union_types, is_union, is_Dict, \
    get_Dict_name_K_V, is_Tuple
from .constants import SCHEMA_ATT, SCHEMA_ID, JSC_TYPE, JSC_STRING, JSC_NUMBER, JSC_OBJECT, JSC_TITLE, \
    JSC_ADDITIONAL_PROPERTIES, JSC_DESCRIPTION, JSC_PROPERTIES, GENERIC_ATT, BINDINGS_ATT, JSC_INTEGER, \
    ID_ATT, JSC_DEFINITIONS, REF_ATT, JSC_REQUIRED, X_CLASSVARS, X_CLASSATTS, JSC_BOOL
from .pretty import pretty_dict
from .types import MemoryJSON

JSONSchema = NewType('JSONSchema', dict)
GlobalsDict = Dict[str, Any]
ProcessingDict = Dict[str, Any]
EncounteredDict = Dict[str, str]

PYTHON_36 = sys.version_info[1] == 6


def object_to_ipce(ob, globals_: GlobalsDict, suggest_type=None) -> MemoryJSON:
    res = object_to_ipce_(ob, globals_, suggest_type)
    # print(indent(json.dumps(res, indent=3), '|', ' res: -'))
    if isinstance(res, dict) and SCHEMA_ATT in res:

        schema = res[SCHEMA_ATT]

        # print(json.dumps(schema, indent=2))
        # print(json.dumps(res, indent=2))

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


import pybase64


def object_to_ipce_(ob, globals_: GlobalsDict, suggest_type: Type = None) -> MemoryJSON:
    """
        Converts to an in-memory JSON representation

    """
    if ob is None:
        msg = 'It should never be possible to serialize null; rather, the attribute is omitted.'
        raise TypeError(msg)

    if isinstance(ob, list):
        # msg = 'Do not support lists yet'
        # raise TypeError(msg)
        suggest_type_l = None  # ZXX
        return [object_to_ipce(_, globals_, suggest_type_l) for _ in ob]

    if isinstance(ob, tuple):
        suggest_type_l = None  # ZXX
        return [object_to_ipce(_, globals_, suggest_type_l) for _ in ob]
        # msg = 'Do not support tuples yet'
        # raise TypeError(msg)

    if isinstance(ob, bytes):
        # res = base58.b58encode(ob)
        # return res.decode()
        res = pybase64.b64encode(ob)
        # logger.debug(f'Decoding bytes of len {len(res)}')
        res = str(res, encoding='ascii')
        # logger.debug(f'done')
        # res = res.decode('ascii')

        return {'base64': res, SCHEMA_ATT: SCHEMA_BYTES}

        # msg = 'Do not support bytes yet'
        # raise TypeError(msg)

    if isinstance(ob, (int, str, float)):
        return ob

    if isinstance(ob, dict):
        return dict_to_ipce(ob, globals_, suggest_type)

    if isinstance(ob, type):
        return type_to_schema(ob, globals_, processing={})

    res = {}
    #
    # D = getattr(ob, '__dict__', None)
    # if D is None:
    #     msg = f'No __dict__ for {ob!r}'
    #     raise ValueError(msg)
    annotations = getattr(type(ob), '__annotations__', {})
    for k, ann in annotations.items():
        if is_ClassVar(ann):
            continue
        v = getattr(ob, k)
        if v is None:
            continue
        try:
            res[k] = object_to_ipce(v, globals_, suggest_type=ann)
        except BaseException as e:
            msg = f'Cannot serialize attribute {k}  = {v}'
            msg += f'\nType {type(ob)} has annotated it as {ann}'
            raise Exception(msg) from e
    res[SCHEMA_ATT] = type_to_schema(type(ob), globals_)
    return res


def dict_to_ipce(ob, globals_, suggest_type):
    res = {}
    if is_Dict(suggest_type):
        K, V = suggest_type.__args__
    elif issubclass(suggest_type, CustomDict):
        K, V = suggest_type.__dict_type__
    else:  # pragma: no cover
        assert False, suggest_type
    # T = suggest_type or type(ob)
    res[SCHEMA_ATT] = type_to_schema(suggest_type, globals_)
    if issubclass(K, str):
        for k, v in ob.items():
            res[k] = object_to_ipce(v, globals_, suggest_type=None)
    else:
        FV = FakeValues[K, V]
        for k, v in ob.items():
            vj = object_to_ipce(v, globals_)
            kj = object_to_ipce(k, globals_)
            h = hash_from_string(json.dumps(kj)).hash

            fv = FV(kj, vj)
            res[h] = object_to_ipce(fv, globals_)

    return res


def ipce_to_object(mj: MemoryJSON, global_symbols, encountered: dict = None,
                   expect_type=None) -> object:
    encountered = encountered or {}
    if isinstance(mj, (int, str, float, bool)):
        return mj

    if isinstance(mj, list):
        if expect_type and is_Tuple(expect_type):
            return deserialize_tuple(expect_type, mj, global_symbols, encountered)
        else:
            seq = [ipce_to_object(_, global_symbols, encountered) for _ in mj]
            return seq

    assert isinstance(mj, dict)

    if SCHEMA_ATT not in mj:
        msg = f'Cannot find a schema.\n{mj}'
        raise ValueError(msg)

    sa = mj[SCHEMA_ATT]
    if sa == SCHEMA_ID:
        # msg = f'Trying to instantiate a schema?\n{mj}'
        # raise NotImplementedError(msg)
        return schema_to_type(mj, global_symbols, encountered)

    K = schema_to_type(sa, global_symbols, encountered)

    assert isinstance(K, type), K

    # if K is type:
    #     # we expect a schema
    #     return schema_to_type(mj, global_symbols, encountered)

    if K is bytes:
        data = mj['base64']
        res = pybase64.b64decode(data)
        assert isinstance(res, bytes)
        return res

    if issubclass(K, dict):
        return deserialize_Dict(K, mj, global_symbols, encountered)

    if is_dataclass(K):
        return deserialize_dataclass(K, mj, global_symbols, encountered)

    assert False, K  # pragma: no cover


def deserialize_tuple(expect_type, mj, global_symbols, encountered):
    seq = []
    for i, ob in enumerate(mj):
        expect_type_i = expect_type.__args__[i]
        seq.append(ipce_to_object(ob, global_symbols, encountered, expect_type=expect_type_i))

    return tuple(seq)


def deserialize_dataclass(K, mj, global_symbols, encountered):
    # some data classes might have no annotations ("Empty")
    anns = getattr(K, '__annotations__', {})

    attrs = {}
    for k, v in mj.items():
        if k in anns:
            expect_type = K.__annotations__[k]
            attrs[k] = ipce_to_object(v, global_symbols, encountered, expect_type=expect_type)

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
        raise TypeError(msg) from e


def deserialize_Dict(D, mj, global_symbols, encountered):
    attrs = {}
    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue
        attrs[k] = ipce_to_object(v, global_symbols, encountered)

    # pprint('here', D=D)
    if issubclass(D, CustomDict):
        K, V = D.__dict_type__
        # pprint(K=K, V=V)

        if issubclass(K, str):
            ob = D()
            ob.update(attrs)
            return ob
        else:
            ob = D()
            for k, v in attrs.items():
                ob[v.real_key] = v.value
            return ob
        # if V.__name__.startswith('FakeValues'):
        #     realK = V.__annotations__['real_key']
        #     realV = V.__annotations__['value']
        #     ob = make_dict(realK, realV)()
        #     for a in attrs.items():
        #         ob[a.real_key] = a.value
        #     return ob
        # elif issubclass(K, str):
        #     ob = D()
        #     ob.update(attrs)
        #     return ob
        # else:
        #     msg = pretty_dict("here", dict(K=K, V=V, attrs=attrs))
        #     raise NotImplementedError(msg)

    else:  # pragma: no cover
        msg = pretty_dict("not sure", dict(D=D, attrs=attrs))
        raise NotImplementedError(msg)


ATT_PYTHON_NAME = '__qualname__'


class CannotFindSchemaReference(ValueError):
    pass


class CannotResolveTypeVar(ValueError):
    pass


def schema_to_type(schema0: JSONSchema, global_symbols: Dict, encountered: Dict) -> Union[Type, _SpecialForm]:
    res = schema_to_type_(schema0, global_symbols, encountered)
    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        encountered[schema_id] = res
        # print(f'Found {schema_id} -> {res}')

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
    # if ID_ATT in res:
    #     encountered[res[ID_ATT]] = ForwardRef(cls_name)
    if schema_id:
        # print(f'Processing {schema_id}')
        if not JSC_TITLE in schema:
            pass
            # msg = f'No title for id: {schema0}'
            # raise Exception(msg)
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
    if schema0 == SCHEMA_BYTES:
        return bytes

    elif jsc_type == JSC_STRING:
        return str
    elif jsc_type == JSC_BOOL:
        return bool

    elif jsc_type == JSC_NUMBER:
        return Number

    elif jsc_type == JSC_INTEGER:
        return int

    elif jsc_type == JSC_OBJECT:
        if schema.get(JSC_TITLE, '') == 'Callable':
            return schema_to_type_callable(schema, global_symbols, encountered)
        if schema.get(JSC_TITLE, '').startswith('Dict'):
            return schema_dict_to_DictType(schema, global_symbols, encountered)
        elif JSC_DEFINITIONS in schema:
            return schema_to_type_generic(schema, global_symbols, encountered)
        elif ATT_PYTHON_NAME in schema:
            tn = schema[ATT_PYTHON_NAME]
            if tn in global_symbols:
                return global_symbols[tn]
            else:
                return schema_to_type_dataclass(schema, global_symbols, encountered)

        assert False, schema  # pragma: no cover
    elif jsc_type == "array":
        return schema_array_to_type(schema, global_symbols, encountered)

    # pprint(schema=schema, schema0=schema0)
    assert False, schema  # pragma: no cover


def schema_array_to_type(schema, global_symbols, encountered):
    items = schema['items']
    if isinstance(items, list):
        assert len(items) > 0
        args = tuple([schema_to_type(_, global_symbols, encountered) for _ in items])

        if PYTHON_36:
            return typing.Tuple[args]
        else:
            return Tuple.__getitem__(args)
    else:
        args = schema_to_type(items, global_symbols, encountered)
        if PYTHON_36:
            return typing.Tuple[args, ...]
        else:
            return Tuple.__getitem__((args, Ellipsis))


def schema_dict_to_DictType(schema, global_symbols, encountered):
    K = str
    V = schema_to_type(schema[JSC_ADDITIONAL_PROPERTIES], global_symbols, encountered)
    # pprint(f'here:', d=dict(V.__dict__))
    # if issubclass(V, FakeValues):
    if V.__name__.startswith('FakeValues'):
        K = V.__annotations__['real_key']
        V = V.__annotations__['value']
    D = make_dict(K, V)
    if JSC_DESCRIPTION in schema:
        setattr(D, '__doc__', schema[JSC_DESCRIPTION])
    return D


def type_to_schema(T: Any, globals0: dict, processing: ProcessingDict = None) -> JSONSchema:
    # pprint('type_to_schema', T=T)
    globals_ = dict(globals0)
    try:
        if T is type:
            res: JSONSchema = {REF_ATT: SCHEMA_ID,
                               JSC_TITLE: 'type'
                               # JSC_DESCRIPTION: T.__doc__
                               }
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
                    if v.__name__ not in globals_:
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


SCHEMA_BYTES: JSONSchema = {JSC_TYPE: JSC_OBJECT,
                            SCHEMA_ATT: SCHEMA_ID,
                            JSC_PROPERTIES: {"base64": {JSC_TYPE: JSC_STRING}}}

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
    if issubclass(K, str):
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


def type_Type_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    # res: JSONSchema = {}
    # res[ATT_PYTHON_NAME] = T.__qualname__
    # res[SCHEMA_ATT] = SCHEMA_ID
    raise NotImplementedError()


def Tuple_to_schema(T, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_Tuple(T)
    args = T.__args__
    if args[-1] == Ellipsis:
        items = args[0]
        res: JSONSchema = {}
        res[SCHEMA_ATT] = SCHEMA_ID
        res["type"] = "array"
        res["items"] = type_to_schema(items, globals_, processing)
        res['title'] = 'Tuple'
        return res
    else:
        res: JSONSchema = {}

        res[SCHEMA_ATT] = SCHEMA_ID
        res["type"] = "array"
        res["items"] = []
        res['title'] = 'Tuple'
        for a in args:
            res['items'].append(type_to_schema(a, globals_, processing))
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
        res: JSONSchema = {JSC_TYPE: JSC_NUMBER, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is int:
        res: JSONSchema = {JSC_TYPE: JSC_INTEGER, SCHEMA_ATT: SCHEMA_ID}
        return res

    if T is bytes:
        return SCHEMA_BYTES

    # we cannot use isinstance on typing.Any
    if is_Any(T):  # XXX not possible...
        res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID}
        return res
    # ) or (T is type)
    # put this check before "issubclass" because of typing weirdness

    if is_union(T):
        return schema_Union(T, globals_, processing)

    if is_Dict(T) or (isinstance(T, type) and issubclass(T, CustomDict)):
        return dict_to_schema(T, globals_, processing)

    if is_optional(T):
        msg = f'Should not be needed to have an Optional here yet: {T}'
        raise AssertionError(msg)

    if is_forward_ref(T):
        msg = f'It is not supported to have an ForwardRef here yet: {T}'
        raise ValueError(msg)
        # name = get_forward_ref_arg(T)

    if is_Intersection(T):
        return schema_Intersection(T, globals_, processing)

    if isinstance(T, str):
        msg = f'It is not supported to have a string here: {T!r}'
        raise ValueError(msg)

    if is_Callable(T):
        return type_callable_to_schema(T, globals_, processing)

    if is_Tuple(T):
        return Tuple_to_schema(T, globals_, processing)

    if is_Type(T):
        return type_Type_to_schema(T, globals_, processing)

    assert isinstance(T, type), T

    # if issubclass(T, CustomDict):
    #     K, V = getattr(T, '__dict_type__')
    #     res = {JSC_TYPE: JSC_OBJECT}
    #     res[JSC_TITLE] = 'Dict[%s,%s]' % (K.__name__, V.__name__)
    #     res[JSC_PROPERTIES] = {"$schema": {}}  # XXX
    #     res[JSC_ADDITIONAL_PROPERTIES] = type_to_schema(V, globals_, processing)
    #     res[SCHEMA_ATT] = SCHEMA_ID
    #     return res

    if issubclass(T, dict):
        msg = f'A regular "dict" slipped through.\n{T}'
        raise TypeError(msg)

    # print(T)
    # print(T.__annotations__)
    # print(getattr(T, _FIELDS))
    if hasattr(T, GENERIC_ATT) and getattr(T, GENERIC_ATT) is not None:
        return type_generic_to_schema(T, globals_, processing)

    if is_dataclass(T):
        return type_dataclass_to_schema(T, globals_, processing)

    msg = 'Cannot interpret this type. (not a dataclass): %s' % T
    raise ValueError(msg)


def schema_Intersection(T, globals_, processing):
    args = get_Intersection_args(T)
    options = [type_to_schema(t, globals_, processing) for t in args]
    res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID, "allOf": options}
    return res


# class MyTypeVar(TypeVar):
#     def __repr__(self):
#         return f'~{self.__name__}(<:{self.__bound__}'

def schema_to_type_generic(res: JSONSchema, global_symbols: dict, encountered: dict) -> Type:
    assert res[JSC_TYPE] == JSC_OBJECT
    assert JSC_DEFINITIONS in res
    cls_name = res[JSC_TITLE]

    encountered = dict(encountered)
    if ID_ATT in res:
        encountered[res[ID_ATT]] = cls_name
        # encountered[res[ID_ATT]] = ForwardRef(cls_name)

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
    if PYTHON_36:
        base = Generic.__getitem__(typevars)
    else:
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
    # setattr(T, '__annotations__', fields)

    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    if ATT_PYTHON_NAME in res:
        setattr(T, '__qualname__', res[ATT_PYTHON_NAME])
    if X_PYTHON_MODULE_ATT in res:
        setattr(T, '__module__', res[X_PYTHON_MODULE_ATT])
    return T


X_PYTHON_MODULE_ATT = '__module__'


def type_generic_to_schema(T: Type, globals_: GlobalsDict, processing_: ProcessingDict) -> JSONSchema:
    assert hasattr(T, GENERIC_ATT)

    types = getattr(T, GENERIC_ATT)
    processing2 = dict(processing_)
    globals2 = dict(globals_)

    res: JSONSchema = {}
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_OBJECT
    res[JSC_TITLE] = T.__name__

    res[ID_ATT] = make_url(T.__name__)
    processing2[f'{T.__name__}'] = make_ref(res[ID_ATT])

    # print(f'T: {T.__name__} ')
    res[X_PYTHON_MODULE_ATT] = T.__module__
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

        result = eval_field(t, globals2, processing2)
        assert isinstance(result, Result), result
        properties[name] = result.schema
        if not result.optional:
            required.append(name)
    if required:
        res[JSC_REQUIRED] = required

    res[ATT_PYTHON_NAME] = T.__qualname__
    return res


def type_dataclass_to_schema(T: Type, globals_: GlobalsDict, processing: ProcessingDict) -> JSONSchema:
    assert is_dataclass(T), T
    # if not hasattr(T, _FIELDS):
    #     msg = f'The type {T} does not look like a Dataclass to me.'
    #     raise ValueError(msg)

    p2 = dict(processing)
    res: JSONSchema = {}
    res[ATT_PYTHON_NAME] = T.__qualname__
    res[SCHEMA_ATT] = SCHEMA_ID
    res[JSC_TYPE] = JSC_OBJECT
    res[ID_ATT] = make_url(T.__name__)
    if hasattr(T, '__name__') and T.__name__:
        res[JSC_TITLE] = T.__name__

        p2[T.__name__] = make_ref(res[ID_ATT])

    if hasattr(T, '__doc__') and T.__doc__:
        res[JSC_DESCRIPTION] = T.__doc__

    res[JSC_PROPERTIES] = properties = {}
    classvars = {}
    classatts = {}

    required = []
    fields_ = getattr(T, _FIELDS)
    # noinspection PyUnusedLocal
    afield: Field

    # hints = get_type_hints(T)
    # print(f'type hints {hints}')
    for name, afield in fields_.items():

        t = afield.type
        # print(f'{name} -> {t}')
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

    if required:  # empty is error
        res[JSC_REQUIRED] = required
    if classvars:
        res[X_CLASSVARS] = classvars
    if classatts:
        res[X_CLASSATTS] = classatts

    res[X_PYTHON_MODULE_ATT] = T.__module__
    return res


@dataclass
class Result:
    schema: JSONSchema
    optional: Optional[bool] = False


# TODO: make url generic
def make_url(x: str):
    assert isinstance(x, str), x
    return f'http://censi.org/{x}#'


def make_ref(x: str):
    assert len(x) > 1, x
    assert isinstance(x, str), x
    return {REF_ATT: x}


def eval_field(t, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    # print(pretty_dict(f'evaluating field {t!r}', dict(processing=processing, globals_=globals_)))
    debug_info2 = lambda: dict(globals_=globals_, processing=processing)

    # if is_ClassVar(t):
    #     msg = f'Should not be here: {t}'
    #     raise AssertionError(msg)

    if is_Type(t):
        res: JSONSchema = make_ref(SCHEMA_ID)
        return Result(res)

    if isinstance(t, type):
        # catch recursion here
        if t.__name__ in processing:
            return eval_field(t.__name__, globals_, processing)
        else:
            schema = type_to_schema(t, globals_, processing)
            return Result(schema)

    if is_Tuple(t):
        res = Tuple_to_schema(t, globals_, processing)
        return Result(res)

    if isinstance(t, str):
        te = eval_type_string(t, globals_, processing)
        return te

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
        # l = '~' +t.__name__
        l = t.__name__
        if l in processing:
            return Result(processing[l])
        if l in globals_:

            T = globals_[l]
            # return Result(T)
            return Result(type_to_schema(T, globals_, processing))
            # return eval_field(T, globals_, processing)

        else:
            m = f'Could not resolve the TypeVar {t}'
            msg = pretty_dict(m, debug_info2())
            raise CannotResolveTypeVar(msg)

    assert False, t  # pragma: no cover


def schema_Union(t, globals_, processing):
    types = get_union_types(t)
    options = [type_to_schema(t, globals_, processing) for t in types]
    res: JSONSchema = {SCHEMA_ATT: SCHEMA_ID, "anyOf": options}
    return res


def eval_type_string(t: str, globals_: GlobalsDict, processing: ProcessingDict) -> Result:
    globals2 = dict(globals_)
    # for k, v in processing.items():
    #     if k not in globals2:
    #         globals2[k] = make_ref(v) # {"$ref": f"{v}#"}

    debug_info = lambda: dict(t=t, globals2=pretty_dict("", globals2), processing=pretty_dict("", processing))

    if t in processing:
        schema: JSONSchema = make_ref(make_url(t))
        return Result(schema)

    elif t in globals2:
        # return globals2[t]
        return eval_field(globals2[t], globals2, processing)
    else:
        try:
            from typing import Optional
            eval_locals = {'Optional': Optional}
            # TODO: put more above?
            # do not pollute environment
            eval_globals = dict(globals2)
            # eval_globals['Optional'] = Optional
            # eval_locals.update(eval_globals)
            try:
                res = eval(t, eval_globals, eval_locals)
            except BaseException as e:
                m = f'Error while evaluating the string {t!r} using eval().'
                msg = pretty_dict(m, dict(eval_locals=eval_locals, eval_globals=eval_globals, info=debug_info()))
                raise type(e)(msg) from e

            return eval_field(res, globals2, processing)
        except NotImplementedError as e:
            m = 'While evaluating string'
            msg = pretty_dict(m, debug_info())
            raise NotImplementedError(msg) from e
        except BaseException as e:
            m = 'Could not evaluate type string'
            msg = pretty_dict(m, debug_info())
            raise ValueError(msg) from e


def schema_to_type_dataclass(res: JSONSchema, global_symbols: dict, encountered: EncounteredDict) -> Type:
    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]

    if ID_ATT in res:
        # encountered[res[ID_ATT]] = ForwardRef(cls_name)
        encountered[res[ID_ATT]] = cls_name

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

        fields.append((pname, ptype, _Field))

    for pname, v in res.get(X_CLASSVARS, {}).items():
        ptype = schema_to_type(v, global_symbols, encountered)
        fields.append((pname, ClassVar[ptype], field()))

    T = make_dataclass(cls_name, fields, bases=(), namespace=None, init=True, repr=True, eq=True, order=False,
                       unsafe_hash=False, frozen=False)

    for pname, v in res.get(X_CLASSATTS, {}).items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = schema_to_type(cast(JSONSchema, v), global_symbols, encountered)
        else:
            interpreted = ipce_to_object(v, global_symbols)
        setattr(T, pname, interpreted)

    # setattr(T, '__annotations__', fields)

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
