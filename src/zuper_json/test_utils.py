import json
import typing
# noinspection PyUnresolvedReferences
from contextlib import contextmanager
from dataclasses import is_dataclass, fields
from typing import ForwardRef
from unittest import SkipTest

import cbor2 as cbor
from nose.tools import assert_equal

from zuper_json.zeneric2 import loglevel, RecLogger
from . import logger
from .annotations_tricks import is_Dict
from .constants import PYTHON_36
from .ipce import object_to_ipce, ipce_to_object, type_to_schema, schema_to_type
from .json_utils import encode_bytes_before_json_serialization, decode_bytes_before_json_deserialization
from .pretty import pretty_dict


def assert_type_roundtrip(T, use_globals: dict, expect_type_equal: bool = True):
    assert T is not None
    rl = RecLogger()
    # resolve_types(T)
    schema0 = type_to_schema(T, use_globals)
    schema = type_to_schema(T, use_globals)
    rl.pp('\n\nschema', schema=json.dumps(schema, indent=2))
    T2 = schema_to_type(schema, {}, {})
    rl.pp(f"\n\nT ({T})  the original one", **getattr(T, '__dict__', {}))
    print()
    rl.pp(f"\n\nT2 ({T2}) - reconstructed from schema ", **getattr(T2, '__dict__', {}))
    print()
    # pprint("schema", schema=json.dumps(schema, indent=2))

    assert_equal(schema, schema0)
    if expect_type_equal:
        # assert_same_types(T, T)
        # assert_same_types(T2, T)
        assert_equivalent_types(T, T2,assume_yes=set())

    schema2 = type_to_schema(T2, use_globals)
    if schema != schema2:
        msg = 'Different schemas'
        msg = pretty_dict(msg, dict(T=T, schema=schema0, T2=T2, schema2=schema2))
        # print(msg)
        with open('tmp1.json', 'w') as f:
            f.write(json.dumps(schema, indent=2))
        with open('tmp2.json', 'w') as f:
            f.write(json.dumps(schema2, indent=2))

        assert_equal(schema, schema2)
        raise AssertionError(msg)
    return T2


@loglevel
def assert_equivalent_types(T1: type, T2: type, assume_yes: set, rl=None):
    key = (id(T1), id(T2))
    if key in assume_yes:
        return
    assume_yes = set(assume_yes)
    assume_yes.add(key)
    rl = rl or RecLogger()
    try:
        # print(f'assert_equivalent_types({T1},{T2})')
        if T1 is T2:
            rl.p('same by equality')
            return
        if hasattr(T1, '__dict__'):
            rl.pp('comparing',
                  T1=f'{T1!r}',
                  T2=f'{T2!r}',

                  T1_dict=T1.__dict__, T2_dict=T2.__dict__)

        # for these builtin we cannot set/get the attrs
        if not isinstance(T1, typing.TypeVar) and (not isinstance(T1, ForwardRef)) and not is_Dict(T1):
            for k in ['__name__', '__module__', '__doc__']:
                msg = f'Difference for {k} of {T1} ({type(T1)} and {T2} ({type(T2)}'
                assert_equal(getattr(T1, k, ()), getattr(T2, k, ()), msg=msg)

        if is_dataclass(T1):
            assert is_dataclass(T2)

            fields1 = fields(T1)
            fields2 = fields(T2)

            fields1 = {_.name: _ for _ in fields1}
            fields2 = {_.name: _ for _ in fields2}

            if sorted(fields1) != sorted(fields2):
                msg = f'Different fields: {sorted(fields1)} != {sorted(fields2)}'
                raise Exception(msg)

            for k in fields1:
                t1 = fields1[k].type
                t2 = fields2[k].type
                rl.pp(f'checking the fields {k}',
                      t1=f'{t1!r}',
                      t2=f'{t2!r}',
                      t1_ann=f'{T1.__annotations__[k]!r}',
                      t2_ann=f'{T2.__annotations__[k]!r}')

                try:
                    assert_equivalent_types(t1, t2, assume_yes=assume_yes)
                except BaseException as e:
                    msg = f'Could not establish the field {k!r} to be equivalent'
                    msg += f'\n t1 = {t1!r}'
                    msg += f'\n t2 = {t2!r}'
                    msg += f'\n t1_ann = {T1.__annotations__[k]!r}'
                    msg += f'\n t2_ann = {T2.__annotations__[k]!r}'
                    raise Exception(msg) from e

        # for k in ['__annotations__']:
        #     assert_equivalent_types(getattr(T1, k, None), getattr(T2, k, None))

        if False:
            if hasattr(T1, 'mro'):
                if len(T1.mro()) != len(T2.mro()):
                    msg = pretty_dict('Different mros', dict(T1=T1.mro(), T2=T2.mro()))
                    raise AssertionError(msg)

                for m1, m2 in zip(T1.mro(), T2.mro()):
                    if m1 is T1 or m2 is T2: continue
                    assert_equivalent_types(m1, m2)

        if PYTHON_36:  # pragma: no cover
            pass  # XX
        else:
            if isinstance(T1, typing._GenericAlias):
                # noinspection PyUnresolvedReferences
                if not is_Dict(T1):
                    # noinspection PyUnresolvedReferences
                    for z1, z2 in zip(T1.__args__, T2.__args__):
                        assert_equivalent_types(z1, z2, assume_yes=assume_yes)
    except BaseException as e:
        msg = f'Could not establish the two types to be equivalent.'
        msg += f'\n T1 = {id(T1)} {T1!r}'
        msg += f'\n T2 = {id(T2)} {T2!r}'
        raise Exception(msg) from e
    # assert T1 == T2
    # assert_equal(T1.mro(), T2.mro())


def assert_object_roundtrip(x1, use_globals, expect_equality=True, works_without_schema=True):
    """

        expect_equality: if __eq__ is preserved

        Will not be preserved if use_globals = {}
        because a new Dataclass will be created
        and different Dataclasses with the same fields do not compare equal.

    """

    y1 = object_to_ipce(x1, use_globals)
    y1_cbor = cbor.dumps(y1)
    y1 = cbor.loads(y1_cbor)

    y1e = encode_bytes_before_json_serialization(y1)
    y1es = json.dumps(y1e, indent=2)
    logger.info(f'y1es: {y1es}')
    y1esl = decode_bytes_before_json_deserialization(json.loads(y1es))
    y1eslo = ipce_to_object(y1esl, use_globals)

    x1b = ipce_to_object(y1, use_globals)

    x1bj = object_to_ipce(x1b, use_globals)

    # if False:
    #     from zuper_ipce import store_json, recall_json
    #     h1 = store_json(y1)
    #     y1b = recall_json(h1)
    #     assert y1b == y1
    #     h2 = store_json(x1bj)
    #     assert h1 == h2

    check_equality(x1, x1b, expect_equality)

    if y1 != x1bj:  # pragma: no cover
        msg = pretty_dict('Round trip not obtained', dict(x1bj=str(x1bj),
                                                          y1=str(y1)))

        raise AssertionError(msg)

    # once again, without schema
    if works_without_schema:
        z1 = object_to_ipce(x1, use_globals, with_schema=False)
        z2 = cbor.loads(cbor.dumps(z1))
        u1 = ipce_to_object(z2, use_globals, expect_type=type(x1))
        check_equality(x1, u1, expect_equality)

    return locals()


def check_equality(x1, x1b, expect_equality):
    if isinstance(x1b, type) and isinstance(x1, type):
        logger.warning('Skipping type equality check for %s and %s' % (x1b, x1))
    else:
        #
        # if isinstance(x1, np.ndarray):
        #     assert allclose(x1b, x1)
        # else:
        # print('x1: %s' % x1)
        eq1 = (x1b == x1)
        eq2 = (x1 == x1b)
        # test object equality
        if expect_equality:  # pragma: no cover
            if not eq1:
                m = 'Object equality (next == orig) not preserved'
                msg = pretty_dict(m,
                                  dict(x1b=x1b,
                                       x1b_=type(x1b),
                                       x1=x1,
                                       x1_=type(x1), x1b_eq=x1b.__eq__))
                raise AssertionError(msg)
            if not eq2:
                m = 'Object equality (orig == next) not preserved'
                msg = pretty_dict(m,
                                  dict(x1b=x1b,
                                       x1b_=type(x1b),
                                       x1=x1,
                                       x1_=type(x1),
                                       x1_eq=x1.__eq__))
                raise AssertionError(msg)
        else:
            if eq1 and eq2:  # pragma: no cover
                msg = 'You did not expect equality but they actually are'
                raise Exception(msg)


from functools import wraps
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest


def fail(message):  # pragma: no cover
    raise AssertionError(message)


def known_failure(f):  # pragma: no cover
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest("Known failure test failed: " + str(e))
        fail("test passed but marked as work in progress")

    return attr('known_failure')(run_test)


def relies_on_missing_features(f):
    msg = "Test relying on not implemented feature."

    @wraps(f)
    def run_test(*args, **kwargs):  # pragma: no cover
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest(msg) from e
        fail("test passed but marked as work in progress")

    return attr('relies_on_missing_features')(run_test)

#
# def with_private_register(f):
#     return f
#     from zuper_ipce.test_utils import with_private_register as other
#     return other(f)
