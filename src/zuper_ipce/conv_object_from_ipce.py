import datetime
import inspect
import traceback
from dataclasses import Field, is_dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, cast, List

import numpy as np
import yaml

from zuper_commons.fs import write_ustring_to_utf8_file
from zuper_commons.text import indent, pretty_dict
from zuper_ipce.utils_text import oyaml_dump
from zuper_typing.annotations_tricks import (get_FixedTuple_args, get_Optional_arg, get_Union_args, get_VarTuple_arg,
                                             is_Any, is_ClassVar, is_FixedTuple, is_Optional, is_TupleLike, is_Union,
                                             is_VarTuple)
from zuper_typing.my_dict import (get_DictLike_args, get_ListLike_arg, get_SetLike_arg, is_DictLike, is_ListLike,
                                  is_SetLike, make_dict, make_set, make_list)
from .constants import (HINTS_ATT, JSC_TITLE, JSC_TITLE_TYPE, JSONSchema, SCHEMA_ATT, SCHEMA_ID)
from .numpy_encoding import numpy_array_from_ipce
from .structures import FakeValues
from .types import IPCE


def object_from_ipce(mj: IPCE,
                     global_symbols: Dict,
                     encountered: Optional[dict] = None,
                     expect_type: Optional[type] = None) -> object:
    try:
        res = object_from_ipce_(mj, global_symbols, encountered=encountered, expect_type=expect_type)
        return res

    except BaseException as e:
        msg = f'Cannot deserialize object (expect: {expect_type})'
        if isinstance(mj, dict) and '$schema' in mj:
            schema = mj['$schema']
        else:
            schema = None

        prefix = f'object_{id(mj)}'
        fn = write_out_yaml(prefix + '_data', mj)
        msg += f'\n object data in {fn}'
        if schema:
            fn = write_out_yaml(prefix + '_schema', schema)
            msg += f'\n object schema in {fn}'

        # if False:

        # if isinstance(mj, dict) and '$schema' in mj:
        #     schema = mj.pop('$schema')
        # else:
        #     schema = None

        # msg += '\n\n' + indent(yaml.dump(mj)[:1000], ' ipce ')
        # msg += '\n\n' + indent(traceback.format_exc(), '| ')
        raise TypeError(msg) from e


def object_from_ipce_(mj: IPCE,
                      global_symbols,
                      encountered: Optional[dict] = None,
                      expect_type: Optional[type] = None) -> object:
    if encountered is None:
        encountered = {}

    if is_Optional(expect_type):
        return object_from_ipcl_optional(expect_type, mj, global_symbols, encountered)

    if is_Union(expect_type):
        return object_from_ipcl_union(expect_type, mj, global_symbols, encountered)

    # logger.debug(f'ipce_to_object expect {expect_type} mj {mj}')
    trivial = (int, float, bool, datetime.datetime, Decimal, bytes, str)

    if expect_type in trivial:
        if not isinstance(mj, expect_type):
            msg = f'Expected trivial expect_type = {expect_type}, got {mj!r}'
            raise TypeError(msg)
        else:
            return mj

    if isinstance(mj, trivial):
        # if check_types:  # pragma: no cover
        T = type(mj)
        if expect_type is not None and not is_Any(expect_type) and not expect_type is object:
            msg = f'Found {mj}, an object of type {T}, but wanted {expect_type}'
            raise ValueError(msg)
        return mj

    if isinstance(mj, list):
        return object_from_ipce_list(mj, global_symbols, encountered, expect_type)

    if mj is None:
        if expect_type is None:
            return None
        elif expect_type is type(None):
            return None
        elif is_Any(expect_type):
            return None
        else:
            msg = f'The value is None but the expected type is {expect_type}.'
            raise TypeError(msg)  # XXX

    assert isinstance(mj, dict), type(mj)
    from .conv_typelike_from_ipce import typelike_from_ipce
    if mj.get(SCHEMA_ATT, '') == SCHEMA_ID:
        schema = cast(JSONSchema, mj)
        return typelike_from_ipce(schema, global_symbols, encountered)
    if mj.get(JSC_TITLE, None) == JSC_TITLE_TYPE:
        schema = cast(JSONSchema, mj)
        return typelike_from_ipce(schema, global_symbols, encountered)

    if SCHEMA_ATT in mj:
        sa = mj[SCHEMA_ATT]
        K = typelike_from_ipce(sa, global_symbols, encountered)
        # logger.debug(f' loaded K = {K} from {mj}')
    else:
        if expect_type is not None:
            # logger.debug('expect_type = %s' % expect_type)
            # check_isinstance(expect_type, type)
            K = expect_type
        else:
            msg = f'Cannot find a schema and expect_type=None.\n{mj}'
            raise ValueError(msg)

    if K is np.ndarray:
        return numpy_array_from_ipce(mj)

    if is_DictLike(K):
        return object_from_ipce_dict(K, mj, global_symbols, encountered)

    if is_SetLike(K):
        res = object_from_ipce_SetLike(K, mj, global_symbols, encountered)
        return res

    if is_dataclass(K):
        return object_from_ipce_dataclass_instance(K, mj, global_symbols, encountered)

    if K is slice:
        return object_from_ipce_slice(mj)

    if is_Any(K):
        if looks_like_set(mj):
            res = object_from_ipce_SetLike(None, mj, global_symbols, encountered)
            return res

        # logger.error(f'fall back on unknown (K={K}) for {id(mj)} = {mj}')
        # raise Exception()
        K = Dict[str, Any]

        return object_from_ipce_dict(K, mj, global_symbols, encountered)

        #
        # msg = f'Not implemented - K = Any'
        # msg += '\n\n' + indent(yaml.dump(mj), ' > ')
        # raise NotImplementedError(msg)

    msg = f'Invalid type or type suggestion {K}'
    raise TypeError(msg)
    # assert False, (type(K), K, mj, expect_type)  # pragma: no cover


def looks_like_set(d: dict):
    return len(d) > 0 and all(k.startswith('set:') for k in d)


def object_from_ipce_slice(mj) -> slice:
    start = mj['start']
    stop = mj['stop']
    step = mj['step']
    return slice(start, stop, step)


def object_from_ipce_list(mj, global_symbols, encountered, expect_type) -> IPCE:
    if expect_type is not None:
        # logger.info(f'expect_type for list is {expect_type}')
        if is_Any(expect_type):
            suggest = None
            seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
            T = make_list(Any)
            return T(seq)
        elif is_TupleLike(expect_type):
            # noinspection PyTypeChecker
            return object_from_ipce_tuple(expect_type, mj, global_symbols, encountered)
        elif is_ListLike(expect_type):
            suggest = get_ListLike_arg(expect_type)
            seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
            T = make_list(suggest)
            return T(seq)

        else:
            msg = f'The object is a list, but expected {expect_type}.\nOb: {mj}'
            raise TypeError(msg)
    else:
        suggest = None
        seq = [object_from_ipce(_, global_symbols, encountered, expect_type=suggest) for _ in mj]
        T = make_list(Any)
        return T(seq)


def object_from_ipcl_optional(expect_type, mj, global_symbols, encountered) -> IPCE:
    if mj is None:
        return mj
    K = get_Optional_arg(expect_type)

    return object_from_ipce(mj,
                            global_symbols,
                            encountered,
                            expect_type=K)


def object_from_ipcl_union(expect_type, mj, global_symbols, encountered) -> IPCE:
    errors = {}
    ts = get_Union_args(expect_type)
    for T in ts:
        try:
            return object_from_ipce(mj,
                                    global_symbols,
                                    encountered,
                                    expect_type=T)
        except BaseException:
            errors[str(T)] = traceback.format_exc()
    msg = f'Cannot deserialize with any of {ts}'
    fn = write_out_yaml(f'object{id(mj)}', mj)
    msg += f'\n ipce in {fn}'
    msg += '\n\n' + pretty_dict('tries', errors)

    # msg += '\n'.join(str(e) for e in errors)
    raise ValueError(msg)


def object_from_ipce_tuple(expect_type, mj, global_symbols, encountered):
    if is_FixedTuple(expect_type):
        seq = []
        ts = get_FixedTuple_args(expect_type)
        for expect_type_i, ob in zip(ts, mj):
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


def object_from_ipce_dataclass_instance(K, mj, global_symbols, encountered):
    # assert  isinstance(K, type), K
    global_symbols = dict(global_symbols)
    global_symbols[K.__name__] = K

    from .conv_typelike_from_ipce import typelike_from_ipce

    anns = getattr(K, '__annotations__', {})

    attrs = {}
    hints = mj.get(HINTS_ATT, {})
    # logger.info(f'hints for {K.__name__} = {hints}')

    for k, v in mj.items():
        if k in anns:
            expect_type = anns[k]

            # if is_Optional(expect_type):
            #     expect_type = get_Optional_arg(expect_type)

            if inspect.isabstract(expect_type):  # pragma: no cover
                msg = f'Trying to instantiate abstract class for field "{k}" of class {K}'
                msg += f'\n annotation = {anns[k]}'
                msg += f'\n expect_type = {expect_type}'
                msg += f'\n\n%s' % indent(oyaml_dump(mj), ' > ')
                raise TypeError(msg)

            if k in hints:
                expect_type = typelike_from_ipce(hints[k], global_symbols, encountered)

            try:
                attrs[k] = object_from_ipce(v, global_symbols, encountered, expect_type=expect_type)

            except BaseException as e:  # pragma: no cover
                msg = f'Cannot deserialize attribute {k!r} of {K.__name__} (expect: {expect_type})'
                msg += f'\n annotations of class {K.__name__} = {K.__annotations__}'
                msg += f'\n anns[{k!r}] = {anns[k]}'
                fn = write_out_yaml(f'instance_of_{K.__name__}_attribute_{k}', v)
                msg += f'\n mj[{k!r}] in {fn}'
                fn = write_out_yaml(f'instance_of_{K.__name__}', mj)
                msg += f'\n mj in {fn}'
                # msg += '\n\n' + indent(yaml.dump(v)[:400], '  ')
                # msg += '\n\n' + indent(traceback.format_exc(), '| ')

                raise TypeError(msg) from e
    # for k, v in attrs.items():
    #     assert not isinstance(v, Field), (k, v)
    for k, T in anns.items():
        if is_ClassVar(T):
            continue
        if not k in mj:
            if hasattr(K, k):  # default - XXX
                V = getattr(K, k)
                if isinstance(V, Field):
                    logger.error(oyaml_dump(mj))
                    from zuper_ipcl.debug_print_ import debug_print
                    logger.error(f'dict: {debug_print(dict(K.__dict__))}')
                    logger.error(f'anns: {debug_print(K.__annotations__)}')
                    # V = V.default
                    raise Exception((k, V))
                # logger.info(f'setting default {V}')
                attrs[k] = V
            # elif is_Optional(T):
            #     attrs[k] = None
            #     pass
            else:
                msg = f'Cannot find field {k!r} in data for class {K}. (T = {T}) Know {sorted(mj)}'
                msg += f'\n annotations: {anns}'
                raise ValueError(msg)
    for k, v in attrs.items():
        assert not isinstance(v, Field), (k, v)
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


from . import logger


def ignore_aliases(self, data):
    if data is None:
        return True
    if isinstance(data, tuple) and data == ():
        return True
    if isinstance(data, list) and len(data) == 0:
        return True
    if isinstance(data, (bool, int, float)):
        return True
    if isinstance(data, str) and len(data) < 10:
        return True
    safe = ['additionalProperties', 'properties', '__module__']
    if isinstance(data, str) and data in safe:
        return True

def write_out_yaml(prefix, v):
    yaml.Dumper.ignore_aliases = ignore_aliases
    # d = oyaml_dump(v)
    d = yaml.dump(v)
    fn = f'errors/{prefix}.yaml'
    write_ustring_to_utf8_file(d, fn)
    return fn


def object_from_ipce_dict(D, mj, global_symbols, encountered):
    K, V = get_DictLike_args(D)
    D = make_dict(K, V)
    ob = D()

    attrs = {}

    FV = FakeValues[K, V]
    if isinstance(K, type) and (issubclass(K, str) or issubclass(K, int)):
        expect_type_V = V
    else:
        expect_type_V = FV

    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        try:
            attrs[k] = object_from_ipce(v, global_symbols, encountered,
                                        expect_type=expect_type_V)

        except (TypeError, NotImplementedError) as e:  # pragma: no cover
            msg = f'Cannot deserialize element at index "{k}".'
            msg += f'\n\n D = {D}'
            msg += '\n\n' + indent(oyaml_dump(mj), '> ')
            msg += f'\n\n Expected V = {expect_type_V}'

            msg += f'\n\n v = {oyaml_dump(v)}'
            raise TypeError(msg) from e
    if isinstance(K, type) and issubclass(K, str):
        ob.update(attrs)
        return ob
    elif isinstance(K, type) and issubclass(K, int):
        attrs = {int(k): v for k, v in attrs.items()}
        ob.update(attrs)
        return ob
    else:
        for k, v in attrs.items():
            # noinspection PyUnresolvedReferences
            ob[v.real_key] = v.value
        return ob


def object_from_ipce_SetLike(D, mj, global_symbols, encountered):
    if D is None:
        V = Any
    else:
        V = get_SetLike_arg(D)

    res = set()

    # logger.info(f'loading SetLike wiht V = {V}')
    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        vob = object_from_ipce(v, global_symbols, encountered, expect_type=V)

        # logger.info(f'loaded k = {k} vob = {vob}')
        res.add(vob)

    T = make_set(V)
    return T(res)
