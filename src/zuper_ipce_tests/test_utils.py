import json
from dataclasses import is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast, Iterator, List, Optional, Tuple, Type, Union

import cbor2
from nose.tools import assert_equal

from zuper_commons.fs import write_bytes_to_file, write_ustring_to_utf8_file
from zuper_ipce import (
    IEDO,
    IESO,
    ipce_from_object,
    ipce_from_typelike,
    logger,
    typelike_from_ipce,
)
from zuper_ipce.constants import IEDS
from zuper_ipce.conv_object_from_ipce import object_from_ipce, object_from_ipce_
from zuper_ipce.json_utils import (
    decode_bytes_before_json_deserialization,
    encode_bytes_before_json_serialization,
)
from zuper_ipce.pretty import pretty_dict
from zuper_ipce.utils_text import oyaml_dump
from zuper_typing import dataclass
from zuper_typing.aliases import TypeLike
from zuper_typing.annotations_tricks import (
    get_ClassVar_arg,
    get_fields_including_static,
    get_FixedTuple_args,
    get_NewType_arg,
    get_NewType_name,
    get_Optional_arg,
    get_Type_arg,
    get_TypeVar_name,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_ClassVar,
    is_FixedTuple,
    is_NewType,
    is_Optional,
    is_Type,
    is_TypeVar,
    is_Union,
    is_VarTuple,
)
from zuper_typing.exceptions import ZValueError
from zuper_typing.logging import ztinfo
from zuper_typing.my_dict import (
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_DictLike,
    is_ListLike,
    is_SetLike,
)
from zuper_typing.my_intersection import get_Intersection_args, is_Intersection


def assert_type_roundtrip(
    T, *, use_globals: Optional[dict] = None, expect_type_equal: bool = True
):
    if use_globals is None:
        use_globals = {}

    schema0 = ipce_from_typelike(T, globals0=use_globals)

    # why 2?
    schema = ipce_from_typelike(T, globals0=use_globals)
    save_object(T, ipce=schema)

    # logger.info(debug_print('schema', schema=schema))
    iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)
    T2 = typelike_from_ipce(schema, iedo=iedo)

    # TODO: in 3.6 does not hold for Dict, Union, etc.
    # if hasattr(T, '__qualname__'):
    #     assert hasattr(T, '__qualname__')
    #     assert T2.__qualname__ == T.__qualname__, (T2.__qualname__, T.__qualname__)

    # if False:
    #     rl.pp('\n\nschema', schema=json.dumps(schema, indent=2))
    #     rl.pp(f"\n\nT ({T})  the original one", **getattr(T, '__dict__', {}))
    #     rl.pp(f"\n\nT2 ({T2}) - reconstructed from schema ", **getattr(T2, '__dict__', {}))

    # pprint("schema", schema=json.dumps(schema, indent=2))

    ztinfo("assert_type_roundtrip", T=T, schema=schema, T2=T2)

    assert_equal(schema, schema0)
    if expect_type_equal:
        # assert_same_types(T, T)
        # assert_same_types(T2, T)
        assert_equivalent_types(T, T2, assume_yes=set())

    schema2 = ipce_from_typelike(T2, globals0=use_globals)
    if schema != schema2:  # pragma: no cover
        msg = "Different schemas"
        d = {
            "T": T,
            "T.qual": T.__qualname__,
            "TAnn": T.__annotations__,
            "Td": T.__dict__,
            "schema": schema0,
            "T2": T2,
            "T2.qual": T2.__qualname__,
            "TAnn2": T2.__annotations__,
            "Td2": T2.__dict__,
            "schema2": schema2,
        }
        msg = pretty_dict(msg, d)
        # print(msg)
        with open("tmp1.json", "w") as f:
            f.write(json.dumps(schema, indent=2))
        with open("tmp2.json", "w") as f:
            f.write(json.dumps(schema2, indent=2))

        # assert_equal(schema, schema2)
        raise AssertionError(msg)
    return T2


#
#
# def debug(s, **kwargs):
#     ss = pretty_dict(s, kwargs)
#     logger.debug(ss)


class NotEquivalentException(ZValueError):
    pass


def assert_equivalent_types(T1: TypeLike, T2: TypeLike, assume_yes: set):
    # debug(f'equivalent', T1=T1, T2=T2)
    key = (id(T1), id(T2))
    if key in assume_yes:
        return
    assume_yes = set(assume_yes)
    assume_yes.add(key)
    try:
        # print(f'assert_equivalent_types({T1},{T2})')
        if T1 is T2:
            # logger.debug('same by equality')
            return
        # if hasattr(T1, '__dict__'):
        #     debug('comparing',
        #           T1=f'{T1!r}',
        #           T2=f'{T2!r}',
        #           T1_dict=T1.__dict__, T2_dict=T2.__dict__)

        # for these builtin we cannot set/get the attrs
        # if not isinstance(T1, typing.TypeVar) and (not isinstance(T1, ForwardRef)) and not is_Dict(T1):

        if is_dataclass(T1):
            if not is_dataclass(T2):
                raise NotEquivalentException(T1=T1, T2=T2)

            for k in ["__name__", "__module__", "__doc__"]:
                msg = f"Difference for {k} of {T1} ({type(T1)}) and {T2} ({type(T2)}"
                v1 = getattr(T1, k, ())
                v2 = getattr(T2, k, ())
                if v1 != v2:
                    raise NotEquivalentException(msg, v1=v1, v2=v2)
                # assert_equal(, , msg=msg)

            fields1 = get_fields_including_static(T1)
            fields2 = get_fields_including_static(T2)
            if list(fields1) != list(fields2):
                msg = f"Different fields"
                raise NotEquivalentException(msg, fields1=fields1, fields2=fields2)

            ann1 = getattr(T1, "__annotations__", {})
            ann2 = getattr(T2, "__annotations__", {})

            # redundant with above
            # if list(ann1) != list(ann2):
            #     msg = f'Different fields: {list(fields1)} != {list(fields2)}'
            #     raise NotEquivalent(msg)

            for k in fields1:
                t1 = fields1[k].type
                t2 = fields2[k].type
                # debug(
                #     f"checking the fields {k}",
                #     t1=f"{t1!r}",
                #     t2=f"{t2!r}",
                #     t1_ann=f"{T1.__annotations__[k]!r}",
                #     t2_ann=f"{T2.__annotations__[k]!r}",
                # )
                try:
                    assert_equivalent_types(t1, t2, assume_yes=assume_yes)
                except NotEquivalentException as e:
                    msg = f"Could not establish the annotation {k!r} to be equivalent"
                    raise NotEquivalentException(
                        msg,
                        t1=t1,
                        t2=t2,
                        t1_ann=T1.__annotations__[k],
                        t2_ann=T2.__annotations__[k],
                        t1_att=getattr(T1, k, "no attribute"),
                        t2_att=getattr(T2, k, "no attribute"),
                    ) from e

                d1 = fields1[k].default
                d2 = fields2[k].default
                if d1 != d2:
                    msg = f"Defaults for {k!r} are different."
                    raise NotEquivalentException(msg, d1=d1, d2=d2)
                #
                # d1 = fields1[k].default_factory
                # d2 = fields2[k].default
                # if d1 != d2:
                #     msg = f"Defaults for {k!r} are different."
                #     raise NotEquivalentException(msg, d1=d1, d2=d2)

            for k in ann1:
                t1 = ann1[k]
                t2 = ann2[k]
                try:
                    assert_equivalent_types(t1, t2, assume_yes=assume_yes)
                except NotEquivalentException as e:
                    msg = f"Could not establish the annotation {k!r} to be equivalent"
                    raise NotEquivalentException(
                        msg,
                        t1=t1,
                        t2=t2,
                        t1_ann=T1.__annotations__[k],
                        t2_ann=T2.__annotations__[k],
                        t1_att=getattr(T1, k, "no attribute"),
                        t2_att=getattr(T2, k, "no attribute"),
                    ) from e

        # for k in ['__annotations__']:
        #     assert_equivalent_types(getattr(T1, k, None), getattr(T2, k, None))

        # if False:
        #     if hasattr(T1, 'mro'):
        #         if len(T1.mro()) != len(T2.mro()):
        #             msg = pretty_dict('Different mros', dict(T1=T1.mro(), T2=T2.mro()))
        #             raise AssertionError(msg)
        #
        #         for m1, m2 in zip(T1.mro(), T2.mro()):
        #             if m1 is T1 or m2 is T2: continue
        #             assert_equivalent_types(m1, m2, assume_yes=set())
        elif is_ClassVar(T1):
            if not is_ClassVar(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_ClassVar_arg(T1)
            t2 = get_ClassVar_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        elif is_Optional(T1):
            if not is_Optional(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_Optional_arg(T1)
            t2 = get_Optional_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        elif is_Union(T1):
            if not is_Union(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            ts1 = get_Union_args(T1)
            ts2 = get_Union_args(T2)
            for t1, t2 in zip(ts1, ts2):
                assert_equivalent_types(t1, t2, assume_yes)
        elif is_Intersection(T1):
            if not is_Intersection(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            ts1 = get_Intersection_args(T1)
            ts2 = get_Intersection_args(T2)
            for t1, t2 in zip(ts1, ts2):
                assert_equivalent_types(t1, t2, assume_yes)
        elif is_FixedTuple(T1):
            if not is_FixedTuple(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            ts1 = get_FixedTuple_args(T1)
            ts2 = get_FixedTuple_args(T2)
            for t1, t2 in zip(ts1, ts2):
                assert_equivalent_types(t1, t2, assume_yes)
        elif is_VarTuple(T1):
            if not is_VarTuple(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_VarTuple_arg(T1)
            t2 = get_VarTuple_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        elif is_SetLike(T1):
            if not is_SetLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_SetLike_arg(T1)
            t2 = get_SetLike_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        elif is_ListLike(T1):
            T1 = cast(Type[List], T1)
            if not is_ListLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            T2 = cast(Type[List], T2)
            t1 = get_ListLike_arg(T1)
            t2 = get_ListLike_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        elif is_DictLike(T1):
            if not is_DictLike(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1, u1 = get_DictLike_args(T1)
            t2, u2 = get_DictLike_args(T2)
            assert_equivalent_types(t1, t2, assume_yes)
            assert_equivalent_types(u1, u2, assume_yes)
        elif is_Any(T1):
            if not is_Any(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
        elif is_TypeVar(T1):
            if not is_TypeVar(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            n1 = get_TypeVar_name(T1)
            n2 = get_TypeVar_name(T2)
            if n1 != n2:
                raise NotEquivalentException(n1=n1, n2=n2)
        elif T1 in (int, str, bool, Decimal, datetime, float, type):
            if T1 != T2:
                raise NotEquivalentException(T1=T1, T2=T2)
        elif is_NewType(T1):
            if not is_NewType(T2):
                raise NotEquivalentException(T1=T1, T2=T2)

            n1 = get_NewType_name(T1)
            n2 = get_NewType_name(T2)
            if n1 != n2:
                raise NotEquivalentException(T1=T1, T2=T2)

            o1 = get_NewType_arg(T1)
            o2 = get_NewType_arg(T2)
            assert_equivalent_types(o1, o2, assume_yes)
        elif is_Type(T1):
            if not is_Type(T2):
                raise NotEquivalentException(T1=T1, T2=T2)
            t1 = get_Type_arg(T1)
            t2 = get_Type_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)

        else:
            raise NotImplementedError((T1, T2))

    except NotEquivalentException as e:
        # logger.error(e)
        msg = f"Could not establish the two types to be equivalent."
        raise NotEquivalentException(msg, T1=T1, T2=T2) from e
    # assert T1 == T2
    # assert_equal(T1.mro(), T2.mro())


def save_object(x: object, ipce: object):
    # noinspection PyBroadException
    try:
        import zuper_ipcl
    except:
        return
    # print(f"saving {x}")
    _x2 = object_from_ipce(ipce)
    ipce_bytes = cbor2.dumps(ipce, canonical=True, value_sharing=True)
    from zuper_ipcl.cid2mh import get_cbor_dag_hash_bytes
    from zuper_ipcl.debug_print_ import debug_print

    digest = get_cbor_dag_hash_bytes(ipce_bytes)
    dn = "test_objects"
    # if not os.path.exists(dn):
    #     os.makedirs(dn)
    fn = os.path.join(dn, digest + ".ipce.cbor.gz")
    if os.path.exists(fn):
        pass
    else:
        fn = os.path.join(dn, digest + ".ipce.cbor")
        write_bytes_to_file(ipce_bytes, fn)
        # fn = os.path.join(dn, digest + '.ipce.yaml')
        # write_ustring_to_utf8_file(yaml.dump(y1), fn)
        fn = os.path.join(dn, digest + ".object.ansi")
        s = debug_print(x)  # '\n\n as ipce: \n\n' + debug_print(ipce) \
        write_ustring_to_utf8_file(s, fn)
        fn = os.path.join(dn, digest + ".ipce.yaml")
        s = oyaml_dump(ipce)
        write_ustring_to_utf8_file(s, fn)


import os


def assert_object_roundtrip(
    x1,
    *,
    use_globals: Optional[dict] = None,
    expect_equality=True,
    works_without_schema=True,
):
    """

        expect_equality: if __eq__ is preserved

        Will not be preserved if use_globals = {}
        because a new Dataclass will be created
        and different Dataclasses with the same fields do not compare equal.

    """
    if use_globals is None:
        use_globals = {}
    ieds = IEDS(use_globals, {})
    iedo = IEDO(use_remembered_classes=False, remember_deserialized_classes=False)

    y1 = ipce_from_object(x1, globals_=use_globals)
    y1_cbor: bytes = cbor2.dumps(y1)

    save_object(x1, ipce=y1)

    y1 = cbor2.loads(y1_cbor)

    y1e = encode_bytes_before_json_serialization(y1)
    y1es = json.dumps(y1e, indent=2)

    y1esl = decode_bytes_before_json_deserialization(json.loads(y1es))

    y1eslo = object_from_ipce_(y1esl, object, ieds=ieds, iedo=iedo)

    x1b = object_from_ipce_(y1, object, ieds=ieds, iedo=iedo)

    x1bj = ipce_from_object(x1b, globals_=use_globals)

    check_equality(x1, x1b, expect_equality)

    if y1 != x1bj:  # pragma: no cover
        msg = pretty_dict(
            "Round trip not obtained",
            dict(x1bj_json=oyaml_dump(x1bj), y1_json=oyaml_dump(y1)),
        )
        # assert_equal(y1, x1bj, msg=msg)
        if "propertyNames" in y1["$schema"]:
            assert_equal(
                y1["$schema"]["propertyNames"],
                x1bj["$schema"]["propertyNames"],
                msg=msg,
            )

        with open("y1.json", "w") as f:
            f.write(json.dumps(y1, indent=2))
        with open("x1bj.json", "w") as f:
            f.write(json.dumps(x1bj, indent=2))

        raise AssertionError(msg)

    # once again, without schema
    ieso_false = IESO(with_schema=False)
    if works_without_schema:
        z1 = ipce_from_object(x1, globals_=use_globals, ieso=ieso_false)
        z2 = cbor2.loads(cbor2.dumps(z1))
        u1 = object_from_ipce_(z2, type(x1), ieds=ieds, iedo=iedo)
        check_equality(x1, u1, expect_equality)

    return locals()


import numpy as np


def check_equality(x1: object, x1b: object, expect_equality: bool) -> None:
    if isinstance(x1b, type) and isinstance(x1, type):
        # logger.warning("Skipping type equality check for %s and %s" % (x1b, x1))
        pass
    else:
        if isinstance(x1, np.ndarray):
            pass
        else:

            eq1 = x1b == x1
            eq2 = x1 == x1b

            if expect_equality:  # pragma: no cover

                if not eq1:
                    m = "Object equality (next == orig) not preserved"
                    msg = pretty_dict(
                        m,
                        dict(
                            x1b=x1b,
                            x1b_=type(x1b),
                            x1=x1,
                            x1_=type(x1),
                            x1b_eq=x1b.__eq__,
                        ),
                    )
                    raise AssertionError(msg)
                if not eq2:
                    m = "Object equality (orig == next) not preserved"
                    msg = pretty_dict(
                        m,
                        dict(
                            x1b=x1b,
                            x1b_=type(x1b),
                            x1=x1,
                            x1_=type(x1),
                            x1_eq=x1.__eq__,
                        ),
                    )
                    raise AssertionError(msg)
            else:
                if eq1 and eq2:  # pragma: no cover
                    msg = "You did not expect equality but they actually are"
                    logger.info(msg)
                    # raise Exception(msg)


def test_testing1():
    def get1():
        @dataclass
        class C1:
            a: int

        return C1

    def get2():
        @dataclass
        class C1:
            a: int
            b: float

        return C1

    try:
        assert_equivalent_types(get1(), get2(), set())
    except NotEquivalentException:
        pass
    else:
        raise Exception()


def test_testing2():
    def get1():
        @dataclass
        class C1:
            A: int

        return C1

    def get2():
        @dataclass
        class C2:
            A: float

        return C2

    try:
        assert_equivalent_types(get1(), get2(), set())
    except NotEquivalentException:
        pass
    else:
        raise Exception()


@dataclass
class Patch:
    __print_order = ["prefix_str", "value1", "value2"]
    prefix: Tuple[Union[str, int], ...]
    value1: object
    value2: Optional[object]
    prefix_str: Optional[str] = None

    def __post_init__(self):
        self.prefix_str = "/".join(map(str, self.prefix))


def patch(o1, o2, prefix: Tuple[Union[str, int], ...]) -> Iterator[Patch]:
    if o1 == o2:
        return
    if isinstance(o1, dict) and isinstance(o2, dict):
        for k, v in o1.items():
            if not k in o2:
                yield Patch(prefix + (k,), v, None)
            else:
                yield from patch(v, o2[k], prefix + (k,))
    elif isinstance(o1, list) and isinstance(o2, list):
        for i, v in enumerate(o1):
            if i >= len(o2) - 1:
                yield Patch(prefix + (i,), v, None)
            else:
                yield from patch(o1[i], o2[i], prefix + (i,))
    else:
        if o1 != o2:
            yield Patch(prefix, o1, o2)
