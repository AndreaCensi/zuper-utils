import functools
import json
import os
import sys
import typing
from contextlib import contextmanager
# noinspection PyUnresolvedReferences
from typing import _eval_type
from unittest import SkipTest

from nose.tools import assert_equal

from . import logger
from .ipce import object_to_ipce, ipce_to_object, type_to_schema, schema_to_type
from .pretty import pretty_dict, pprint
from .register import ConcreteRegister, use_register, store_json, recall_json, IPFSDagRegister
PYTHON_36 = sys.version_info[1] == 6

def assert_type_roundtrip(T, use_globals, expect_type_equal=True):
    # resolve_types(T)
    schema0 = type_to_schema(T, use_globals)
    schema = type_to_schema(T, use_globals)
    print(json.dumps(schema, indent=2))
    T2 = schema_to_type(schema, {}, {})
    pprint("T", **getattr(T, '__dict__', {}))
    pprint("T2", **getattr(T2, '__dict__', {}))
    # pprint("schema", schema=json.dumps(schema, indent=2))

    assert_equal(schema, schema0)
    if expect_type_equal:
        # assert_same_types(T, T)
        # assert_same_types(T2, T)
        assert_equivalent_types(T, T2)

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


def assert_equivalent_types(T1: type, T2: type):
    if T1 is T2:
        return
    if hasattr(T1, '__dict__'):
        pprint('compare',
               T1n=str(T1),
               T2n=str(T2),

               T1=T1.__dict__, T2=T2.__dict__)
    assert_equal(T1.__doc__, T2.__doc__)

    for k in ['__name__', '__module__', '__doc__']:
        assert_equal(getattr(T1, k, ()), getattr(T2, k, ()))

    for k in ['__annotations__']:
        assert_equivalent_types(getattr(T1, k, None), getattr(T2, k, None))

    if False:
        if hasattr(T1, 'mro'):
            if len(T1.mro()) != len(T2.mro()):
                msg = pretty_dict('Different mros', dict(T1=T1.mro(), T2=T2.mro()))
                raise AssertionError(msg)

            for m1, m2 in zip(T1.mro(), T2.mro()):
                if m1 is T1 or m2 is T2: continue
                assert_equivalent_types(m1, m2)

    if PYTHON_36:
        pass # XX
    else:
        if isinstance(T1, typing._GenericAlias):
            for z1, z2 in zip(T1.__args__, T2.__args__):
                assert_equivalent_types(z1, z2)

    # assert T1 == T2
    # assert_equal(T1.mro(), T2.mro())


def assert_object_roundtrip(x1, use_globals, expect_equality=True):
    """

        expect_equality: if __eq__ is preserved

        Will not be preserved if use_globals = {}
        because a new Dataclass will be created
        and different Dataclasses with the same fields do not compare equal.

    """

    y1 = object_to_ipce(x1, use_globals)

    h1 = store_json(y1)
    y1b = recall_json(h1)

    # print('---original')

    # print('---recalled')
    # print(json_dump(y1b))

    # print(register.pretty_print())

    assert y1b == y1

    x1b = ipce_to_object(y1, use_globals)
    # print(x1b)
    # assert isinstance(x1b, Office)

    #
    # print(register.string_from_hash(h1))
    # print(register.G)

    x1bj = object_to_ipce(x1b, use_globals)
    h2 = store_json(x1bj)
    if h1 != h2:  # pragma: no cover
        msg = pretty_dict('Round trip not obtained', dict(x1bj=json.dumps(x1bj, indent=2),
                                                          y1=json.dumps(y1, indent=2)))

        raise AssertionError(msg)

    if isinstance(x1b, type) and isinstance(x1, type):
        logger.warning('Skipping type equality check for %s and %s' % (x1b, x1))
    else:

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

    return locals()


def with_private_register(f):
    def f2(*args, **kwargs):
        with private_register(f.__name__):
            return f(*args, **kwargs)

    f2.__name__ = f.__name__
    return f2


r = IPFSDagRegister()


@functools.lru_cache(128)
def get_test_register(fn):
    # print(f'Creating new register {fn}')

    register = ConcreteRegister(fn, parent=r)

    return register


@contextmanager
def private_register(name):
    delete = False
    d = '.registers'
    if not os.path.exists(d):  # pragma: no cover
        os.makedirs(d)

    fn = os.path.join(d, f'{name}.db')

    if delete:  # pragma: no cover
        if os.path.exists(fn):
            os.unlink(fn)
    register = get_test_register(fn)
    with use_register(register):
        yield


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
