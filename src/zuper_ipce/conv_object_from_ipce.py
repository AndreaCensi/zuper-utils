import datetime
import inspect
import traceback
from dataclasses import Field, fields, is_dataclass, MISSING, replace
from decimal import Decimal
from typing import cast, Dict, Optional, Set, Type

import numpy as np
import yaml

from zuper_commons.fs import write_ustring_to_utf8_file
from zuper_ipce.conv_typelike_from_ipce import typelike_from_ipce_sr
from zuper_ipce.exceptions import IPCE_PASS_THROUGH, ZDeserializationErrorSchema
from zuper_ipce.types import is_unconstrained
from zuper_typing.annotations_tricks import (
    get_FixedTuple_args,
    get_Optional_arg,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_ClassVar,
    is_FixedTuple,
    is_Optional,
    is_TupleLike,
    is_Union,
    is_VarTuple,
)
from zuper_typing.exceptions import ZTypeError, ZValueError
from zuper_typing.my_dict import (
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_DictLike,
    is_ListLike,
    is_SetLike,
    make_dict,
    make_list,
    make_set,
)
from zuper_typing.my_intersection import get_Intersection_args, is_Intersection
from .constants import (
    HINTS_ATT,
    IEDO,
    IEDS,
    JSC_TITLE,
    JSC_TITLE_TYPE,
    JSONSchema,
    SCHEMA_ATT,
    SCHEMA_ID,
)
from .numpy_encoding import numpy_array_from_ipce
from .structures import FakeValues
from .types import IPCE, TypeLike


def object_from_ipce(
    mj: IPCE, expect_type: TypeLike = object, *, opt: Optional[IEDO] = None
) -> object:
    assert expect_type is not None
    if opt is None:
        opt = IEDO()
    ieds = IEDS({}, {})

    try:
        res = object_from_ipce_(mj, expect_type=expect_type, ieds=ieds, opt=opt)
        return res
    except IPCE_PASS_THROUGH:
        raise
    except BaseException as e:
        msg = f"Cannot deserialize object"
        if isinstance(mj, dict) and "$schema" in mj:
            schema = mj["$schema"]
        else:
            schema = None

        prefix = f"object_{id(mj)}"
        fn = write_out_yaml(prefix + "_data", mj)
        msg += f"\n object data in {fn}"
        if schema:
            fn = write_out_yaml(prefix + "_schema", schema)
            msg += f"\n object schema in {fn}"

        raise ZValueError(msg, expect_type=expect_type) from e


def object_from_ipce_(
    mj: IPCE, expect_type: TypeLike, *, ieds: IEDS, opt: IEDO
) -> object:
    assert expect_type is not None

    if is_Optional(expect_type):
        return object_from_ipce_optional(mj, expect_type, ieds=ieds, opt=opt)

    if is_Union(expect_type):
        return object_from_ipce_union(mj, expect_type, ieds=ieds, opt=opt)

    if is_Intersection(expect_type):
        return object_from_ipce_intersection(mj, expect_type, ieds=ieds, opt=opt)
    # logger.debug(f'ipce_to_object expect {expect_type} mj {mj}')
    trivial = (int, float, bool, datetime.datetime, Decimal, bytes, str)

    if expect_type in trivial:
        if not isinstance(mj, expect_type):
            msg = "Expected trivial expect_type @expect_type, got @mj_yaml."
            raise ZValueError(msg, expect_type=expect_type, mj_yaml=mj)
        else:
            return mj

    if isinstance(mj, trivial):
        # if check_types:  # pragma: no cover
        T = type(mj)
        if (
            expect_type is not None
            and not is_Any(expect_type)
            and not expect_type is object
        ):
            msg = f"Found an object of type @T, but wanted @expect_type"
            raise ZValueError(msg, mj=mj, T=T, expect_type=expect_type)
        return mj

    if isinstance(mj, list):
        return object_from_ipce_list(mj, expect_type, ieds=ieds, opt=opt)

    if mj is None:
        if expect_type is None:
            return None
        elif expect_type is type(None):
            return None
        elif is_Any(expect_type):
            return None
        elif expect_type is object:
            return None
        else:
            msg = f"The value is None but the expected type is @expect_type."
            raise ZValueError(msg, expect_type=expect_type)

    assert isinstance(mj, dict), type(mj)

    from .conv_typelike_from_ipce import typelike_from_ipce_sr

    if mj.get(SCHEMA_ATT, "") == SCHEMA_ID:
        schema = cast(JSONSchema, mj)

        sr = typelike_from_ipce_sr(schema, ieds=ieds, opt=opt)
        return sr.res
    if mj.get(JSC_TITLE, None) == JSC_TITLE_TYPE:
        schema = cast(JSONSchema, mj)
        sr = typelike_from_ipce_sr(schema, ieds=ieds, opt=opt)
        return sr.res

    if SCHEMA_ATT in mj:
        sa = mj[SCHEMA_ATT]
        R = typelike_from_ipce_sr(sa, ieds=ieds, opt=opt)
        K = R.res
        # logger.debug(f' loaded K = {K} from {mj}')
    else:
        if expect_type is not None:
            K = expect_type
        else:
            msg = f"Cannot find a schema and expect_type=None."
            raise ZValueError(msg, mj_yaml=mj)

    if K is np.ndarray:
        return numpy_array_from_ipce(mj)

    if is_DictLike(K):
        K = cast(Type[Dict], K)
        return object_from_ipce_dict(mj, K, ieds=ieds, opt=opt)

    if is_SetLike(K):
        K = cast(Type[Set], K)
        res = object_from_ipce_SetLike(mj, K, ieds=ieds, opt=opt)
        return res

    if is_dataclass(K):
        return object_from_ipce_dataclass_instance(mj, K, ieds=ieds, opt=opt)

    if K is slice:
        return object_from_ipce_slice(mj)

    if is_unconstrained(K):
        if looks_like_set(mj):
            st = Set[object]
            res = object_from_ipce_SetLike(mj, st, ieds=ieds, opt=opt)
            return res
        else:
            msg = "No schema found and very ambiguous."
            raise ZDeserializationErrorSchema(msg=msg, mj=mj)
            # st = Dict[str, object]
            #
            # return object_from_ipce_dict(mj, st, ieds=ieds, opt=opt)

    msg = f"Invalid type or type suggestion."

    raise ZValueError(msg, K=K)


def looks_like_set(d: dict):
    return len(d) > 0 and all(k.startswith("set:") for k in d)


def object_from_ipce_slice(mj) -> slice:
    start = mj["start"]
    stop = mj["stop"]
    step = mj["step"]
    return slice(start, stop, step)


def object_from_ipce_list(mj: IPCE, expect_type, *, ieds: IEDS, opt: IEDO) -> IPCE:
    def rec(x, TT: TypeLike) -> object:
        return object_from_ipce_(x, ieds=ieds, expect_type=TT, opt=opt)

    # logger.info(f'expect_type for list is {expect_type}')
    from zuper_ipce.conv_ipce_from_object import is_unconstrained

    if is_unconstrained(expect_type):
        suggest = object
        seq = [rec(_, suggest) for _ in mj]
        T = make_list(object)
        return T(seq)
    elif is_TupleLike(expect_type):
        return object_from_ipce_tuple(mj, expect_type, ieds=ieds, opt=opt)
    elif is_ListLike(expect_type):
        suggest = get_ListLike_arg(expect_type)
        seq = [rec(_, suggest) for _ in mj]
        T = make_list(suggest)
        return T(seq)

    else:
        msg = f"The object is a list, but expected different"
        raise ZValueError(msg, expect_type=expect_type, mj=mj)


def object_from_ipce_optional(
    mj: IPCE, expect_type: TypeLike, *, ieds: IEDS, opt: IEDO
) -> IPCE:
    if mj is None:
        return mj
    K = get_Optional_arg(expect_type)

    return object_from_ipce_(mj, K, ieds=ieds, opt=opt)


def object_from_ipce_union(
    mj: IPCE, expect_type: TypeLike, *, ieds: IEDS, opt: IEDO
) -> IPCE:
    errors = []
    ts = get_Union_args(expect_type)
    for T in ts:
        try:
            return object_from_ipce_(mj, T, ieds=ieds, opt=opt)
        except BaseException:
            errors.append(dict(T=T, e=traceback.format_exc()))
    msg = f"Cannot deserialize with any type."
    fn = write_out_yaml(f"object{id(mj)}", mj)
    msg += f"\n ipce in {fn}"
    raise ZValueError(msg, ts=ts, errors=errors)


def object_from_ipce_intersection(
    mj: IPCE, expect_type: TypeLike, *, ieds: IEDS, opt: IEDO
) -> IPCE:
    errors = {}
    ts = get_Intersection_args(expect_type)
    for T in ts:
        try:
            return object_from_ipce_(mj, T, ieds=ieds, opt=opt)
        except BaseException:
            errors[str(T)] = traceback.format_exc()
    msg = f"Cannot deserialize with any of @ts"
    fn = write_out_yaml(f"object{id(mj)}", mj)
    msg += f"\n ipce in {fn}"
    raise ZValueError(msg, errors=errors, ts=ts)


def object_from_ipce_tuple(mj: IPCE, expect_type: TypeLike, *, ieds: IEDS, opt: IEDO):
    if is_FixedTuple(expect_type):
        seq = []
        ts = get_FixedTuple_args(expect_type)
        for expect_type_i, ob in zip(ts, mj):
            r = object_from_ipce_(ob, expect_type_i, ieds=ieds, opt=opt)
            seq.append(r)

        return tuple(seq)
    elif is_VarTuple(expect_type):
        T = get_VarTuple_arg(expect_type)
        seq = []
        for i, ob in enumerate(mj):
            r = object_from_ipce_(ob, T, ieds=ieds, opt=opt)
            seq.append(r)

        return tuple(seq)
    else:
        assert False


def get_class_fields(K) -> Dict[str, Field]:
    class_fields: Dict[str, Field] = {}
    for f in fields(K):
        class_fields[f.name] = f
    return class_fields


def add_to_globals(ieds: IEDS, name: str, val: object) -> IEDS:
    g = dict(ieds.global_symbols)
    g[name] = val
    return replace(ieds, global_symbols=g)


def object_from_ipce_dataclass_instance(
    mj: IPCE, K: TypeLike, *, ieds: IEDS, opt: IEDO
):
    ieds = add_to_globals(ieds, K.__name__, K)

    anns = getattr(K, "__annotations__", {})

    attrs = {}
    hints = mj.get(HINTS_ATT, {})
    # logger.info(f'hints for {K.__name__} = {hints}')

    for k, v in mj.items():
        if k not in anns:
            continue

        et_k = anns[k]

        if inspect.isabstract(et_k):  # pragma: no cover
            msg = f"Trying to instantiate abstract class for field {k!r} of class {K.__name__}."
            raise ZValueError(msg, K=K, expect_type=et_k, mj=mj, annotation=anns[k])

        if k in hints:
            R = typelike_from_ipce_sr(hints[k], ieds=ieds, opt=opt)

            et_k = R.res

        try:
            attrs[k] = object_from_ipce_(v, et_k, ieds=ieds, opt=opt)

        except BaseException as e:  # pragma: no cover
            msg = f"Cannot deserialize attribute {k!r} of {K.__name__}."

            fn = write_out_yaml(f"instance_of_{K.__name__}_attribute_{k}", v)
            msg += f"\n mj[{k!r}] in {fn}"
            fn = write_out_yaml(f"instance_of_{K.__name__}", mj)
            msg += f"\n mj in {fn}"

            raise ZValueError(
                msg,
                K_annotations=K.__annotations__,
                expect_type=et_k,
                ann_K=anns[k],
                K_name=K.__name__,
            ) from e

    class_fields = get_class_fields(K)

    for k, T in anns.items():
        if is_ClassVar(T):
            continue
        if not k in mj:
            f = class_fields[k]
            if f.default != MISSING:
                attrs[k] = f.default
            elif f.default_factory != MISSING:
                attrs[k] = f.default_factory()
            else:
                msg = (
                    f"Cannot find field {k!r} in data for class {K.__name__} "
                    f"and no default available"
                )
                raise ZValueError(msg, anns=anns, T=T, known=sorted(mj), f=f)

    for k, v in attrs.items():
        assert not isinstance(v, Field), (k, v)
    try:
        return K(**attrs)
    except TypeError as e:  # pragma: no cover
        msg = f"Cannot instantiate type {K.__name__}."
        raise ZTypeError(msg, K=K, attrs=attrs, bases=K.__bases__, fields=anns) from e


def ignore_aliases(self, data) -> bool:
    _ = self
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
    safe = ["additionalProperties", "properties", "__module__"]
    if isinstance(data, str) and data in safe:
        return True


def write_out_yaml(prefix: str, v: object) -> str:
    yaml.Dumper.ignore_aliases = ignore_aliases
    # d = oyaml_dump(v)
    d = yaml.dump(v)
    fn = f"errors/{prefix}.yaml"
    write_ustring_to_utf8_file(d, fn)
    return fn


def object_from_ipce_dict(mj: IPCE, D: Type[Dict], *, ieds: IEDS, opt: IEDO):
    assert is_DictLike(D), D
    K, V = get_DictLike_args(D)
    D = make_dict(K, V)
    ob = D()

    attrs = {}

    FV = FakeValues[K, V]
    if isinstance(K, type) and (issubclass(K, str) or issubclass(K, int)):
        et_V = V
    else:
        et_V = FV

    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        try:
            attrs[k] = object_from_ipce_(v, et_V, ieds=ieds, opt=opt)

        except (TypeError, NotImplementedError) as e:  # pragma: no cover
            msg = f'Cannot deserialize element at index "{k}".'
            raise ZTypeError(msg, expect_type_V=et_V, v=v, D=D, mj_yaml=mj) from e

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


def object_from_ipce_SetLike(mj: IPCE, D: Type[Set], *, ieds: IEDS, opt: IEDO):
    V = get_SetLike_arg(D)

    res = set()

    # logger.info(f'loading SetLike wiht V = {V}')
    for k, v in mj.items():
        if k == SCHEMA_ATT:
            continue

        vob = object_from_ipce_(v, V, ieds=ieds, opt=opt)

        # logger.info(f'loaded k = {k} vob = {vob}')
        res.add(vob)

    T = make_set(V)
    return T(res)
