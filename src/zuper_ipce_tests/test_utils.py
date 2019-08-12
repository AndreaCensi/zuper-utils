import json
import traceback
import typing
# noinspection PyUnresolvedReferences
from contextlib import contextmanager
from dataclasses import dataclass, fields, is_dataclass

import cbor2

from zuper_commons.fs import write_bytes_to_file, write_ustring_to_utf8_file
from zuper_typing_tests.test_utils import known_failure

try:
    # noinspection PyUnresolvedReferences
    from typing import ForwardRef
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences
    from typing import _ForwardRef as ForwardRef

import cbor2 as cbor
import yaml
from nose.tools import assert_equal

from zuper_ipce import logger
from zuper_typing.annotations_tricks import is_Dict, is_Optional, get_Optional_arg

from zuper_ipce.conv_ipce_from_object import ipce_from_object
from zuper_ipce.conv_object_from_ipce import object_from_ipce
from zuper_ipce.conv_typelike_from_ipce import typelike_from_ipce
from zuper_ipce.conv_ipce_from_typelike import ipce_from_typelike
from zuper_ipce.json_utils import encode_bytes_before_json_serialization, decode_bytes_before_json_deserialization
from zuper_ipce.pretty import pretty_dict


def assert_type_roundtrip(T, use_globals: dict, expect_type_equal: bool = True):
    # assert T is not None
    # rl = RecLogger()
    # resolve_types(T)
    schema0 = ipce_from_typelike(T, use_globals)

    # why 2?
    schema = ipce_from_typelike(T, use_globals)
    save_object(T, ipce=schema)

    T2 = typelike_from_ipce(schema, {}, {})

    # TODO: in 3.6 does not hold for Dict, Union, etc.
    # if hasattr(T, '__qualname__'):
    #     assert hasattr(T, '__qualname__')
    #     assert T2.__qualname__ == T.__qualname__, (T2.__qualname__, T.__qualname__)

    # if False:
    #     rl.pp('\n\nschema', schema=json.dumps(schema, indent=2))
    #     rl.pp(f"\n\nT ({T})  the original one", **getattr(T, '__dict__', {}))
    #     rl.pp(f"\n\nT2 ({T2}) - reconstructed from schema ", **getattr(T2, '__dict__', {}))

    # pprint("schema", schema=json.dumps(schema, indent=2))

    assert_equal(schema, schema0)
    if expect_type_equal:
        # assert_same_types(T, T)
        # assert_same_types(T2, T)
        assert_equivalent_types(T, T2, assume_yes=set())

    schema2 = ipce_from_typelike(T2, use_globals)
    if schema != schema2:
        msg = 'Different schemas'
        d = {
              'T':  T, 'T.qual': T.__qualname__, 'TAnn': T.__annotations__, 'Td': T.__dict__, 'schema': schema0,
              'T2': T2, 'T2.qual': T2.__qualname__, 'TAnn2': T2.__annotations__, 'Td2': T2.__dict__, 'schema2': schema2
              }
        msg = pretty_dict(msg, d)
        # print(msg)
        with open('tmp1.json', 'w') as f:
            f.write(json.dumps(schema, indent=2))
        with open('tmp2.json', 'w') as f:
            f.write(json.dumps(schema2, indent=2))

        # assert_equal(schema, schema2)
        raise AssertionError(msg)
    return T2


from zuper_typing.constants import PYTHON_36


def debug(s, **kwargs):
    ss = pretty_dict(s, kwargs)
    logger.debug(ss)


def assert_equivalent_types(T1: type, T2: type, assume_yes: set):
    key = (id(T1), id(T2))
    if key in assume_yes:
        return
    assume_yes = set(assume_yes)
    assume_yes.add(key)
    try:
        # print(f'assert_equivalent_types({T1},{T2})')
        if T1 is T2:
            logger.debug('same by equality')
            return
        if hasattr(T1, '__dict__'):
            debug('comparing',
                  T1=f'{T1!r}',
                  T2=f'{T2!r}',
                  T1_dict=T1.__dict__, T2_dict=T2.__dict__)

        # for these builtin we cannot set/get the attrs
        # if not isinstance(T1, typing.TypeVar) and (not isinstance(T1, ForwardRef)) and not is_Dict(T1):


        if is_Optional(T1) and is_Optional(T2):
            t1 = get_Optional_arg(T1)
            t2 = get_Optional_arg(T2)
            assert_equivalent_types(t1, t2, assume_yes)
        if is_dataclass(T1):
            assert is_dataclass(T2)

            for k in ['__name__', '__module__', '__doc__']:
                msg = f'Difference for {k} of {T1} ({type(T1)}) and {T2} ({type(T2)}'
                assert_equal(getattr(T1, k, ()), getattr(T2, k, ()), msg=msg)

            # noinspection PyDataclass
            fields1 = fields(T1)
            # noinspection PyDataclass
            fields2 = fields(T2)

            fields1 = {_.name: _ for _ in fields1}
            fields2 = {_.name: _ for _ in fields2}

            if sorted(fields1) != sorted(fields2):
                msg = f'Different fields: {sorted(fields1)} != {sorted(fields2)}'
                raise Exception(msg)

            for k in fields1:
                t1 = fields1[k].type
                t2 = fields2[k].type
                debug(f'checking the fields {k}',
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
                    msg += f'\n t1_attribute = {getattr(T1, k, "no attribute")!r}'
                    msg += f'\n t2_attribute = {getattr(T2, k, "no attribute")!r}'
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
                    assert_equivalent_types(m1, m2, assume_yes=set())

        if PYTHON_36:  # pragma: no cover
            pass  # XX
        else:
            if isinstance(T1, typing._GenericAlias):
                # noinspection PyUnresolvedReferences
                if not is_Dict(T1) and not is_Optional(T1):
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


def save_object(x: object, ipce: object):
    # noinspection PyBroadException
    try:
        import zuper_ipcl
    except:
        return
    print(f'saving {x}')
    x2 = object_from_ipce(ipce, {}, {})
    ipce_bytes = cbor2.dumps(ipce, canonical=True, value_sharing=True)
    from zuper_ipcl.cid2mh import get_cbor_dag_hash_bytes
    from zuper_ipcl.debug_print_ import debug_print
    digest = get_cbor_dag_hash_bytes(ipce_bytes)
    dn = 'test_objects'
    # if not os.path.exists(dn):
    #     os.makedirs(dn)
    fn = os.path.join(dn, digest + '.ipce.cbor.gz')
    if os.path.exists(fn):
        pass
    else:
        fn = os.path.join(dn, digest + '.ipce.cbor')
        write_bytes_to_file(ipce_bytes, fn)
        # fn = os.path.join(dn, digest + '.ipce.yaml')
        # write_ustring_to_utf8_file(yaml.dump(y1), fn)
        fn = os.path.join(dn, digest + '.object.ansi')
        s = debug_print(x)  # '\n\n as ipce: \n\n' + debug_print(ipce) \
        s += '\n\n as YAML: \n\n' + yaml.dump(ipce)
        write_ustring_to_utf8_file(s, fn)


import os


def assert_object_roundtrip(x1, use_globals, expect_equality=True, works_without_schema=True):
    """

        expect_equality: if __eq__ is preserved

        Will not be preserved if use_globals = {}
        because a new Dataclass will be created
        and different Dataclasses with the same fields do not compare equal.

    """

    y1 = ipce_from_object(x1, use_globals)
    y1_cbor: bytes = cbor.dumps(y1)

    save_object(x1, ipce=y1)

    y1 = cbor.loads(y1_cbor)

    y1e = encode_bytes_before_json_serialization(y1)
    y1es = json.dumps(y1e, indent=2)
    # logger.info(f'y1es: {y1es}')
    y1esl = decode_bytes_before_json_deserialization(json.loads(y1es))
    y1eslo = object_from_ipce(y1esl, use_globals)

    x1b = object_from_ipce(y1, use_globals)

    x1bj = ipce_from_object(x1b, use_globals)

    # if False:
    #     from zuper_ipce import store_json, recall_json
    #     h1 = store_json(y1)
    #     y1b = recall_json(h1)
    #     assert y1b == y1
    #     h2 = store_json(x1bj)
    #     assert h1 == h2

    check_equality(x1, x1b, expect_equality)

    if y1 != x1bj:  # pragma: no cover
        msg = pretty_dict('Round trip not obtained', dict(x1bj_json=yaml.dump(x1bj),
                                                          y1_json=yaml.dump(y1)))
        # assert_equal(y1, x1bj, msg=msg)
        if 'propertyNames' in y1['$schema']:
            assert_equal(y1['$schema']['propertyNames'], x1bj['$schema']['propertyNames'], msg=msg)

        with open('y1.json', 'w') as f:
            f.write(json.dumps(y1, indent=2))
        with open('x1bj.json', 'w') as f:
            f.write(json.dumps(x1bj, indent=2))

        raise AssertionError(msg)

    # once again, without schema
    if works_without_schema:
        z1 = ipce_from_object(x1, use_globals, with_schema=False)
        z2 = cbor.loads(cbor.dumps(z1))
        u1 = object_from_ipce(z2, use_globals, expect_type=type(x1))
        check_equality(x1, u1, expect_equality)

    # s = {x1b}
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
                logger.info(msg)
                # raise Exception(msg)


@known_failure
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
    except:
        print(traceback.format_exc())
        raise


@known_failure
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
    except:
        print(traceback.format_exc())
        raise


def assert_equal_ipce(msg, a, b):
    patches = list(patch(a, b, ()))
    if patches:
        with open('ipce1.json', 'w') as f:
            json.dump(a, f, indent=2)

        with open('ipce2.json', 'w') as f:
            json.dump(b, f, indent=2)
        msg += '\nSee differences in ipce1.json, ipce2.json'
        # msg += '\n' + side_by_side([yaml.dump(a), ' ', yaml.dump(b)])
        # msg += '\n\n' + '\n'.join(str(_) for _ in patches)
        msg += '\n\n' + '\n'.join("/".join(map(str, _.prefix)) for _ in patches)
        raise AssertionError(msg)


from typing import Any, Optional, Iterator, Tuple, Union


@dataclass
class Patch:
    prefix: Tuple[Union[str, int], ...]
    value1: Any
    value2: Optional[Any]


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
