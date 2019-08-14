import dataclasses
import datetime
from dataclasses import dataclass, field, make_dataclass
from decimal import Decimal
from numbers import Number
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, Tuple, TypeVar, cast

import numpy as np
import yaml

from zuper_commons.types import check_isinstance
from zuper_typing.annotations_tricks import (is_Any, is_ForwardRef, make_Tuple, make_Union,
                                             make_VarTuple)
from zuper_typing.constants import PYTHON_36
from zuper_typing.monkey_patching_typing import MyNamedArg, get_remembered_class, remember_created_class
from zuper_typing.my_dict import make_dict, make_list, make_set
from zuper_typing.my_intersection import Intersection
from . import logger
from .assorted_recursive_type_subst import recursive_type_subst
from .constants import (ATT_PYTHON_NAME, CALLABLE_ORDERING, CALLABLE_RETURN, EncounteredDict, GlobalsDict, ID_ATT,
                        JSC_ADDITIONAL_PROPERTIES, JSC_ALLOF, JSC_ANYOF, JSC_ARRAY, JSC_BOOL, JSC_DEFAULT,
                        JSC_DEFINITIONS, JSC_DESCRIPTION, JSC_INTEGER, JSC_NULL, JSC_NUMBER, JSC_OBJECT, JSC_PROPERTIES,
                        JSC_REQUIRED, JSC_STRING, JSC_TITLE, JSC_TITLE_BYTES, JSC_TITLE_CALLABLE, JSC_TITLE_DATETIME,
                        JSC_TITLE_DECIMAL, JSC_TITLE_FLOAT, JSC_TITLE_NUMPY, JSC_TITLE_SLICE, JSC_TYPE, JSONSchema,
                        ProcessingDict, REF_ATT, SCHEMA_ATT, SCHEMA_ID, X_CLASSATTS, X_CLASSVARS, X_ORDER,
                        X_PYTHON_MODULE_ATT)
from .pretty import pretty_dict
from .structures import CannotFindSchemaReference
from .types import TypeLike


@dataclass
class SRE:
    res: TypeLike
    used: Dict[str, Any] = dataclasses.field(default_factory=dict)


def typelike_from_ipce(schema0: JSONSchema,
                       global_symbols: Dict,
                       encountered: Dict) -> TypeLike:
    sre = typelike_from_ipce_sr(schema0, global_symbols, encountered)
    return sre.res


def typelike_from_ipce_sr(schema0: JSONSchema,
                          global_symbols: Dict,
                          encountered: Dict) -> SRE:
    try:
        sre = typelike_from_ipce_sr_(schema0, global_symbols, encountered)
        assert isinstance(sre, SRE), (schema0, sre)
        res = sre.res
    except (TypeError, ValueError) as e:  # pragma: no cover
        msg = 'Cannot interpret schema as a type.'
        # msg += '\n\n' + indent(yaml.dump(schema0)[:400], ' > ')
        # msg += '\n\n' + pretty_dict('globals', global_symbols)
        # msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e

    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        encountered[schema_id] = res

    return sre


def typelike_from_ipce_sr_(schema0: JSONSchema, global_symbols: Dict, encountered: Dict) -> SRE:
    # pprint('schema_to_type_', schema0=schema0)
    # encountered = encountered or {}
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
        return SRE(Any)

    if REF_ATT in schema:
        r = schema[REF_ATT]
        if r == SCHEMA_ID:
            if schema.get(JSC_TITLE, '') == 'type':
                return SRE(type)
            else:  # pragma: no cover
                raise NotImplementedError(schema)
                # return SRE(Type)

        if r in encountered:
            res = encountered[r]
            return SRE(res, {r: res})
        else:
            m = f'Cannot evaluate reference {r!r}'
            msg = pretty_dict(m, info)
            raise CannotFindSchemaReference(msg)

    if JSC_ANYOF in schema:
        return typelike_from_ipce_Union(schema, global_symbols, encountered)

    if JSC_ALLOF in schema:
        return typelike_from_ipce_Intersection(schema, global_symbols, encountered)

    jsc_type = schema.get(JSC_TYPE, None)
    jsc_title = schema.get(JSC_TITLE, '-not-provided-')
    if jsc_title == JSC_TITLE_NUMPY:
        res = np.ndarray
        return SRE(res)

    if jsc_type == JSC_STRING:
        if jsc_title == JSC_TITLE_BYTES:
            return SRE(bytes)
        elif jsc_title == JSC_TITLE_DATETIME:
            return SRE(datetime.datetime)
        elif jsc_title == JSC_TITLE_DECIMAL:
            return SRE(Decimal)
        else:
            return SRE(str)
    elif jsc_type == JSC_NULL:
        return SRE(type(None))

    elif jsc_type == JSC_BOOL:
        return SRE(bool)

    elif jsc_type == JSC_NUMBER:
        if jsc_title == JSC_TITLE_FLOAT:
            return SRE(float)
        else:
            return SRE(Number)

    elif jsc_type == JSC_INTEGER:
        return SRE(int)

    elif jsc_type == JSC_OBJECT:
        if jsc_title == JSC_TITLE_CALLABLE:
            return typelike_from_ipce_Callable(schema, global_symbols, encountered)
        elif jsc_title.startswith('Dict['):
            return typelike_from_ipce_DictType(schema, global_symbols, encountered)
        elif jsc_title.startswith('Set['):
            return typelike_from_ipce_SetType(schema, global_symbols, encountered)
        elif jsc_title == JSC_TITLE_SLICE:
            return SRE(slice)
        else:
            return typelike_from_ipce_dataclass(schema, global_symbols, encountered, schema_id=schema_id)
        assert False, schema  # pragma: no cover
    elif jsc_type == JSC_ARRAY:
        return typelike_from_ipce_array(schema, global_symbols, encountered)

    assert False, schema  # pragma: no cover


def typelike_from_ipce_Union(schema, global_symbols, encountered) -> SRE:
    options = schema[JSC_ANYOF]
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    args = [f(_) for _ in options]
    if args and args[-1] is type(None):
        V = args[0]
        res = Optional[V]
    else:
        res = make_Union(*args)
    return SRE(res, used)


def typelike_from_ipce_Intersection(schema, global_symbols, encountered) -> SRE:
    options = schema[JSC_ALLOF]
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    args = [f(_) for _ in options]
    res = Intersection[tuple(args)]  # XXX
    return SRE(res, used)


def typelike_from_ipce_array(schema, global_symbols, encountered) -> SRE:
    assert schema[JSC_TYPE] == JSC_ARRAY
    items = schema['items']
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    if isinstance(items, list):
        # assert len(items) > 0
        args = tuple([f(_) for _ in items])
        res = make_Tuple(*args)

    else:
        if schema[JSC_TITLE].startswith('Tuple['):
            V = f(items)
            res = make_VarTuple(V)

        else:
            V = f(items)
            res = make_list(V)

    # logger.info(f'found list like: {res}')
    return SRE(res, used)


def typelike_from_ipce_DictType(schema, global_symbols, encountered) -> SRE:
    K = str
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    V = f(schema[JSC_ADDITIONAL_PROPERTIES])
    # pprint(f'here:', d=dict(V.__dict__))
    # if issubclass(V, FakeValues):
    if isinstance(V, type) and V.__name__.startswith('FakeValues'):
        K = V.__annotations__['real_key']
        V = V.__annotations__['value']

    try:
        D = make_dict(K, V)
    except (TypeError, ValueError) as e:  # pragma: no cover
        msg = f'Cannot reconstruct dict type with K = {K!r}  V = {V!r}'
        msg += '\n\n' + pretty_dict('globals', global_symbols)
        msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e
    # we never put it anyway
    # if JSC_DESCRIPTION in schema:
    #     setattr(D, '__doc__', schema[JSC_DESCRIPTION])
    return SRE(D, used)


def typelike_from_ipce_SetType(schema, global_symbols, encountered):
    if not JSC_ADDITIONAL_PROPERTIES in schema:  # pragma: no cover
        msg = f'Expected {JSC_ADDITIONAL_PROPERTIES!r} in {schema}'
        raise ValueError(msg)
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    V = f(schema[JSC_ADDITIONAL_PROPERTIES])
    res = make_set(V)
    return SRE(res, used)


def typelike_from_ipce_Callable(schema: JSONSchema, global_symbols: GlobalsDict, encountered: ProcessingDict):
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    schema = dict(schema)
    definitions = dict(schema[JSC_DEFINITIONS])
    ret = f(definitions.pop(CALLABLE_RETURN))
    others = []
    for k in schema[CALLABLE_ORDERING]:
        d = f(definitions[k])
        if not k.startswith('__'):
            d = MyNamedArg(d, k)
        others.append(d)

    # noinspection PyTypeHints
    res = Callable[others, ret]
    # logger.info(f'typelike_from_ipce_Callable: {schema} \n others =  {others}\n res = {res}')
    return SRE(res, used)


import json


def typelike_from_ipce_dataclass(res: JSONSchema, global_symbols: dict, encountered: EncounteredDict,
                                 schema_id=None) -> SRE:
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]

    definitions = res.get(JSC_DEFINITIONS, {})

    required = res.get(JSC_REQUIRED, [])

    properties = res.get(JSC_PROPERTIES, {})
    classvars = res.get(X_CLASSVARS, {})
    classatts = res.get(X_CLASSATTS, {})

    if (not X_PYTHON_MODULE_ATT in res) or not ATT_PYTHON_NAME in res:  # pragma: no cover
        msg = f'Cannot find attributes for {cls_name}: \n {res}'
        raise ValueError(msg)
    module_name = res[X_PYTHON_MODULE_ATT]
    qual_name = res[ATT_PYTHON_NAME]

    try:
        res = get_remembered_class(module_name, qual_name)
        return SRE(res)
    except KeyError:
        pass

    typevars: List[TypeVar] = []
    for tname, t in definitions.items():
        bound = f(t)
        # noinspection PyTypeHints
        if is_Any(bound):
            bound = None
        # noinspection PyTypeHints
        tv = TypeVar(tname, bound=bound)
        typevars.append(tv)
        if ID_ATT in t:
            encountered[t[ID_ATT]] = tv

    if typevars:
        typevars2: Tuple[TypeVar, ...] = tuple(typevars)

        # TODO: typevars
        if PYTHON_36:  # pragma: no cover
            # noinspection PyUnresolvedReferences
            base = Generic.__getitem__(typevars2)
        else:
            # noinspection PyUnresolvedReferences
            base = Generic.__class_getitem__(typevars2)
        bases = (base,)
    else:
        bases = ()

    Placeholder = type(f'PlaceholderFor{cls_name}', (), {})

    encountered[schema_id] = Placeholder

    fields = []  # (name, type, Field)

    names = res.get(X_ORDER, list(properties))
    # assert_equal(set(names), set(properties), msg=yaml.dump(res))
    # else:
    #     names = list(properties)
    #

    from .conv_object_from_ipce import object_from_ipce
    # logger.info(f'reading {cls_name} names {names}')
    other_set_attr = {}
    for pname in names:
        if pname in properties:
            v = properties[pname]
            ptype = f(v)
            _Field = field()
            _Field.name = pname
            has_default = JSC_DEFAULT in v
            if has_default:
                default_value = object_from_ipce(v[JSC_DEFAULT], global_symbols, expect_type=ptype)
                _Field.default = default_value
                assert not isinstance(default_value, dataclasses.Field)
                other_set_attr[pname] = default_value
            else:
                if not pname in required:
                    msg = f'Field {pname!r} is not required but I did not find a default'
                    msg += '\n\n' + yaml.dump(res)
                    raise Exception(msg)
            fields.append((pname, ptype, _Field))
        elif pname in classvars:
            v = classvars[pname]
            ptype = f(v)
            logger.info(f'ipce classvar: {pname} {ptype}')
            fields.append((pname, ClassVar[ptype], field()))
        elif pname in classatts:  # pragma: no cover
            msg = f'Found {pname} in classatts but not in classvars: \n {json.dumps(res, indent=3)}'
            raise ValueError(msg)
        else:  # pragma: no cover
            msg = f'Cannot find {pname!r} either in properties ({list(properties)}) or classvars ({list(classvars)}) ' \
                  f'or classatts {list(classatts)}'
            raise ValueError(msg)

    # _MISSING_TYPE should be first (default fields last)
    # XXX: not tested
    def has_default(x):
        return not isinstance(x[2].default, dataclasses._MISSING_TYPE)

    fields = sorted(fields, key=has_default, reverse=False)
    #
    # for _, _, the_field in fields:
    #     logger.info(f'- {the_field.name} {the_field}')
    unsafe_hash = True
    try:
        T = make_dataclass(cls_name, fields, bases=bases, namespace=None,
                           init=True, repr=True, eq=True, order=False,
                           unsafe_hash=unsafe_hash, frozen=False)
    except TypeError:  # pragma: no cover

        msg = 'Cannot make dataclass with fields:'
        for f in fields:
            msg += f'\n {f}'
        logger.error(msg)
        raise

    fix_annotations_with_self_reference(T, cls_name, Placeholder)
    from .conv_object_from_ipce import object_from_ipce
    for pname, v in classatts.items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = f(cast(JSONSchema, v))
        else:
            interpreted = object_from_ipce(v, global_symbols)
        assert not isinstance(interpreted, dataclasses.Field)
        setattr(T, pname, interpreted)
    for k, v in other_set_attr.items():
        assert not isinstance(v, dataclasses.Field)
        setattr(T, k, v)
    if JSC_DESCRIPTION in res:
        setattr(T, '__doc__', res[JSC_DESCRIPTION])
    else:
        # the original one did not have it
        setattr(T, '__doc__', None)

    # if module_name is not None:
    setattr(T, '__module__', module_name)
    # if ATT_PYTHON_NAME in res:
    setattr(T, '__qualname__', qual_name)
    # else:
    #     raise Exception(f'could not find ATT_PYTHON_NAME in {res}')

    # logger.info(f'created T with qual {T.__qualname__}')
    if schema_id in used:
        used.pop(schema_id)
    if not used:
        remember_created_class(T)

    assert not 'varargs' in T.__dict__
    return SRE(T, used)


def fix_annotations_with_self_reference(T, cls_name, Placeholder):
    # print('fix_annotations_with_self_reference')
    # logger.info(f'fix_annotations_with_self_reference {cls_name}, placeholder: {Placeholder}')
    # logger.info(f'encountered: {encountered}')
    # logger.info(f'global_symbols: {global_symbols}')

    def f(M):
        assert not is_ForwardRef(M)
        if M is Placeholder:
            return T
        # elif hasattr(M, '__name__') and M.__name__ == Placeholder.__name__:
        #     return T
        else:
            return M

    f.__name__ = f'replacer_for_{cls_name}'

    anns2 = {}

    anns: dict = T.__annotations__
    for k, v0 in anns.items():
        v = recursive_type_subst(v0, f)

        anns2[k] = v
    T.__annotations__ = anns2

    for f in dataclasses.fields(T):
        f.type = T.__annotations__[f.name]

#
# @loglevel
# def typelike_from_ipce_generic(res: JSONSchema, global_symbols: dict, encountered: dict, rl: RecLogger = None) ->
# Type:
#     rl = rl or RecLogger()
#     # rl.pp('schema_to_type_generic', schema=res, global_symbols=global_symbols, encountered=encountered)
#     assert res[JSC_TYPE] == JSC_OBJECT
#     assert JSC_DEFINITIONS in res
#     cls_name = res[JSC_TITLE]
#     if X_PYTHON_MODULE_ATT in res:
#         module_name = res[X_PYTHON_MODULE_ATT]
#         k = module_name, cls_name
#         if USE_REMEMBERED_CLASSES:
#             if k in RegisteredClasses.klasses:
#                 return RegisteredClasses.klasses[k]
#             else:
#                 pass
#                 # logger.info(f'cannot find generic {k}')
#     else:
#         module_name = None
#
#     encountered = dict(encountered)
#
#     required = res.get(JSC_REQUIRED, [])
#
#     typevars: List[TypeVar] = []
#     for tname, t in res[JSC_DEFINITIONS].items():
#         bound = typelike_from_ipce(t, global_symbols, encountered)
#         # noinspection PyTypeHints
#         if is_Any(bound):
#             bound = None
#         # noinspection PyTypeHints
#         tv = TypeVar(tname, bound=bound)
#         typevars.append(tv)
#         if ID_ATT in t:
#             encountered[t[ID_ATT]] = tv
#
#     typevars: Tuple[TypeVar, ...] = tuple(typevars)
#     # TODO: typevars
#     if PYTHON_36:  # pragma: no cover
#         # noinspection PyUnresolvedReferences
#         base = Generic.__getitem__(typevars)
#     else:
#         # noinspection PyUnresolvedReferences
#         base = Generic.__class_getitem__(typevars)
#
#     fields_required = []  # (name, type, Field)
#     fields_not_required = []
#     for pname, v in res.get(JSC_PROPERTIES, {}).items():
#         ptype = typelike_from_ipce(v, global_symbols, encountered)
#
#         if pname in required:
#             _Field = field()
#             fields_required.append((pname, ptype, _Field))
#         else:
#             _Field = field(default=None)
#             ptype = Optional[ptype]
#             fields_not_required.append((pname, ptype, _Field))
#
#     fields = fields_required + fields_not_required
#     T = make_dataclass(cls_name, fields, bases=(base,), namespace=None, init=True,
#                        repr=True, eq=True, order=False,
#                        unsafe_hash=False, frozen=False)
#
#     class Placeholder:
#         pass
#
#     # XXX: not sure
#     fix_annotations_with_self_reference(T, cls_name, Placeholder)
#
#     if JSC_DESCRIPTION in res:
#         setattr(T, '__doc__', res[JSC_DESCRIPTION])
#     # if ATT_PYTHON_NAME in res:
#     #     setattr(T, '__qualname__', res[ATT_PYTHON_NAME])
#     if X_PYTHON_MODULE_ATT in res:
#         setattr(T, '__module__', res[X_PYTHON_MODULE_ATT])
#     return T
