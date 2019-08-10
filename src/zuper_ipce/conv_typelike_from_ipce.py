import dataclasses
import datetime
from dataclasses import field, make_dataclass
from decimal import Decimal
from numbers import Number
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, Tuple, Type, TypeVar, cast

import numpy as np

from zuper_commons.types import check_isinstance
from zuper_ipce import logger
from zuper_ipce.assorted_recursive_type_subst import recursive_type_subst
from zuper_ipce.constants import (ATT_PYTHON_NAME, EncounteredDict, GlobalsDict, ID_ATT, JSC_ADDITIONAL_PROPERTIES,
                                  JSC_ALLOF, JSC_ANYOF, JSC_ARRAY, JSC_BOOL, JSC_DEFAULT, JSC_DEFINITIONS,
                                  JSC_DESCRIPTION, JSC_INTEGER, JSC_NULL, JSC_NUMBER, JSC_OBJECT, JSC_PROPERTIES,
                                  JSC_REQUIRED, JSC_STRING, JSC_TITLE, JSC_TITLE_BYTES, JSC_TITLE_CALLABLE,
                                  JSC_TITLE_DATETIME, JSC_TITLE_DECIMAL, JSC_TITLE_FLOAT, JSC_TITLE_NUMPY,
                                  JSC_TITLE_SLICE, JSC_TYPE, JSONSchema, ProcessingDict, REF_ATT, SCHEMA_ATT, SCHEMA_ID,
                                  X_CLASSATTS, X_CLASSVARS, X_PYTHON_MODULE_ATT)
from zuper_ipce.pretty import pretty_dict
from zuper_ipce.structures import CannotFindSchemaReference
from zuper_ipce.types import TypeLike
from zuper_typing.annotations_tricks import (get_ForwardRef_arg, is_Any, is_ForwardRef, make_Tuple, make_Union,
                                             make_VarTuple)
from zuper_typing.constants import PYTHON_36
from zuper_typing.monkey_patching_typing import MyNamedArg, get_remembered_class, remember_created_class
from zuper_typing.my_dict import make_dict, make_set, make_list
from zuper_typing.my_intersection import Intersection
from zuper_typing.zeneric2 import RecLogger, loglevel


@dataclasses.dataclass
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
    # if use_schema_cache:
    #     h = schema_hash([schema0, list(global_symbols), list(encountered)])
    #     if h in schema_cache:
    #         # logger.info(f'cache hit for {schema0}')
    #         return schema_cache[h]
    # else:
    #     h = None

    try:
        sre = typelike_from_ipce_sr_(schema0, global_symbols, encountered)
        assert isinstance(sre, SRE), (schema0, sre)
        res = sre.res
    except (TypeError, ValueError) as e:
        msg = 'Cannot interpret schema as a type.'
        # msg += '\n\n' + indent(yaml.dump(schema0)[:400], ' > ')
        # msg += '\n\n' + pretty_dict('globals', global_symbols)
        # msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e

    if ID_ATT in schema0:
        schema_id = schema0[ID_ATT]
        encountered[schema_id] = res
        # print(f'Found {schema_id} -> {res}')

    # if use_schema_cache:
    #     schema_cache[h] = res
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
            else:
                return SRE(Type)

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
        # elif JSC_DEFINITIONS in schema:
        #     return typelike_from_ipce_dataclass(schema, global_symbols, encountered)
        # elif ATT_PYTHON_NAME in schema:
        #     tn = schema[ATT_PYTHON_NAME]
        #     if tn in global_symbols:
        #         return global_symbols[tn]
        #     else:
        #         # logger.debug(f'did not find {tn} in {global_symbols}')
        #         return typelike_from_ipce_dataclass(schema, global_symbols, encountered, schema_id=schema_id)
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
    except (TypeError, ValueError) as e:
        msg = f'Cannot reconstruct dict type with K = {K!r}  V = {V!r}'
        msg += '\n\n' + pretty_dict('globals', global_symbols)
        msg += '\n\n' + pretty_dict('encountered', encountered)
        raise TypeError(msg) from e
    # we never put it anyway
    # if JSC_DESCRIPTION in schema:
    #     setattr(D, '__doc__', schema[JSC_DESCRIPTION])
    return SRE(D, used)


def typelike_from_ipce_SetType(schema, global_symbols, encountered):
    if not JSC_ADDITIONAL_PROPERTIES in schema:
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
    ret = f(definitions.pop('return'))
    others = []
    for k in schema['ordering']:
        d = f(definitions[k])
        if not k.startswith('__'):
            d = MyNamedArg(d, k)
        others.append(d)

    # noinspection PyTypeHints
    res = Callable[others, ret]
    # logger.info(f'typelike_from_ipce_Callable: {schema} \n others =  {others}\n res = {res}')
    return SRE(res, used)


@loglevel
def typelike_from_ipce_dataclass(res: JSONSchema, global_symbols: dict, encountered: EncounteredDict,
                                 schema_id=None, rl: RecLogger = None) -> SRE:
    used = {}

    def f(x):
        sre = typelike_from_ipce_sr(x, global_symbols, encountered)
        used.update(sre.used)
        return sre.res

    assert res[JSC_TYPE] == JSC_OBJECT
    cls_name = res[JSC_TITLE]

    if (not X_PYTHON_MODULE_ATT in res) or not ATT_PYTHON_NAME in res:
        msg = f'Cannot find attributes for {cls_name}: \n {res}'
        raise ValueError(msg)
    module_name = res[X_PYTHON_MODULE_ATT]
    qual_name = res[ATT_PYTHON_NAME]
    try:
        res = get_remembered_class(module_name, qual_name)
        return SRE(res)
    except KeyError:
        pass

    definitions = res.get(JSC_DEFINITIONS, {})
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
    required = res.get(JSC_REQUIRED, [])

    fields = []  # (name, type, Field)

    properties = res.get(JSC_PROPERTIES, {})
    # if 'order' in res:
    names = res.get('order', list(properties))
    # assert_equal(set(names), set(properties), msg=yaml.dump(res))
    # else:
    #     names = list(properties)
    #
    from zuper_ipce.conv_object_from_ipce import object_from_ipce
    # logger.info(f'reading {cls_name} names {names}')
    for pname in names:
        if pname not in properties:
            continue
        v = properties[pname]
        ptype = f(v)
        # logger.info(f'got for pname {pname} {v} -> ptype {ptype}')
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
        ptype = f(v)
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
    from zuper_ipce.conv_object_from_ipce import object_from_ipce
    for pname, v in res.get(X_CLASSATTS, {}).items():
        if isinstance(v, dict) and SCHEMA_ATT in v and v[SCHEMA_ATT] == SCHEMA_ID:
            interpreted = f(cast(JSONSchema, v))
        else:
            interpreted = object_from_ipce(v, global_symbols)
        setattr(T, pname, interpreted)

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

    return SRE(T, used)


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
def fix_annotations_with_self_reference(T, cls_name, Placeholder):
    # print('fix_annotations_with_self_reference')
    # logger.info(f'fix_annotations_with_self_reference {cls_name}, placeholder: {Placeholder}')
    # logger.info(f'encountered: {encountered}')
    # logger.info(f'global_symbols: {global_symbols}')

    def f(M):
        # print((M, Placeholder, M is Placeholder, M == Placeholder, id(M), id(Placeholder)))
        if hasattr(M, '__name__') and M.__name__ == Placeholder.__name__:
            return T
        elif M == Placeholder:
            return T
        elif is_ForwardRef(M):
            arg = get_ForwardRef_arg(M)
            if arg == cls_name:
                return T
            else:
                return M
        else:
            return M

    f.__name__ = f'replacer_for_{cls_name}'
    # def f2(M):
    #     # print(f'fix_annotation({T}, {cls_name}, {Placeholder})  {M} ')
    #     r = f(M)
    #     # if is_dataclass(M):
    #
    #     if is_dataclass(M):
    #         d0 = getattr(M, '__doc__', 'NO DOC')
    #         d1 = getattr(r, '__doc__', 'NO DOC')
    #     else:
    #         d0 = d1 = None
    #     # logger.info(f'f2 for {cls_name}: M = {M} -> {r}')
    #     # print(f'fix_annotation({T}, {cls_name}, {Placeholder})  {M} {d0!r} -> {r} {d1!r}')
    #     return r

    # from zuper_ipcl.debug_print_ import  debug_print

    anns2 = {}

    anns: dict = T.__annotations__
    for k, v0 in anns.items():
        v = recursive_type_subst(v0, f)
        # d = debug_print(dict(v0=v0, v=v))
        # logger.info(f'annotation for {cls_name} ({Placeholder.__name__}) argument {k}\n{d}')
        anns2[k] = v
    T.__annotations__ = anns2
    # s = debug_print(v)
    # if Placeholder.__name__ in s:
    #     raise ValueError(s)
    # d0 = getattr(v0, '__doc__', 'NO DOC')
    # d1 = getattr(v, '__doc__', 'NO DOC')
    # assert_equal(d0, d1)

    for f in dataclasses.fields(T):
        f.type = T.__annotations__[f.name]

    # logger.info(pretty_dict(f'annotations resolved for {T} ({Placeholder})', T.__annotations__))
