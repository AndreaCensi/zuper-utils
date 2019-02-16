from dataclasses import dataclass, field
from typing import *

try:
    from typing import ForwardRef
except ImportError:
    from typing import _ForwardRef as ForwardRef

from .annotations_tricks import is_Any
from .as_json import to_canonical_json, assert_regular_memory_json, assert_good_canonical
from .constants import LINKS, SCHEMA_ATT, SCHEMA_ID
from .ipce import make_dict, ipce_to_object, object_to_ipce, type_to_schema, schema_to_type, \
    CannotFindSchemaReference, JSONSchema, CannotResolveTypeVar, eval_field
from .test_utils import assert_object_roundtrip, with_private_register


# from zuper_json.zeneric2 import zataclass, Zeneric


@dataclass
class Empty:
    ...


@dataclass
class Contents:
    data: bytes


@dataclass
class Address:
    """ An address with street and number """
    street: str
    number: int


@dataclass
class Person:
    """ Describes a Person """
    first: str
    last: str
    address: Address


@dataclass
class Office:
    """ An Office contains people. """
    people: Dict[str, Person] = field(default_factory=make_dict(str, Person))


@with_private_register
def test_ser1():
    x1 = Office()
    x1.people['andrea'] = Person('Andrea', 'Censi', Address('Sonnegstrasse', 3))

    assert_object_roundtrip(x1, symbols)


@with_private_register
def test_ser2():
    x1 = Office()
    x1.people['andrea'] = Person('Andrea', 'Censi', Address('Sonnegstrasse', 3))

    assert_object_roundtrip(x1, {}, expect_equality=True)


@dataclass
class Name:
    """ Describes a Name with optional middle name"""
    first: str
    last: str

    middle: Optional[str] = None


@dataclass
class Chain:
    """ Describes a Name with optional middle name"""
    value: str

    down: Optional['Chain'] = None


@dataclass
class FA:
    """ Describes a Name with optional middle name"""
    value: str

    down: 'FB'


@dataclass
class FB:
    mine: int


symbols = {'Office': Office,
           'Person': Person,
           'Address': Address,
           'Name': Name,
           'Contents': Contents,
           'Empty': Empty,
           'FA': FA,
           'FB': FB,
           'Chain': Chain}


@with_private_register
def test_optional_1():
    n1 = Name(first='H', middle='J', last='Wells')
    assert_object_roundtrip(n1, symbols)


@with_private_register
def test_optional_2():
    n1 = Name(first='H', last='Wells')
    assert_object_roundtrip(n1, symbols)


@with_private_register
def test_optional_3():
    n1 = Name(first='H', last='Wells')
    assert_object_roundtrip(n1, {}, expect_equality=True)


@with_private_register
def test_recursive():
    n1 = Chain(value='12')
    assert_object_roundtrip(n1, {'Chain': Chain})


@with_private_register
def test_ser_forward1():
    n1 = FA(value='a', down=FB(12))
    # with private_register('test_forward'):
    assert_object_roundtrip(n1, symbols)


@with_private_register
def test_ser_forward2():
    n1 = Empty()
    assert_object_roundtrip(n1, symbols)


from nose.tools import raises, assert_equal


@with_private_register
def test_bytes1():
    n1 = Contents(b'1234')
    assert_object_roundtrip(n1, symbols)


@raises(ValueError)
def test_abnormal_no_schema():
    ipce_to_object({}, {})


# @raises(TypeError)
def test_abnormal_no_lists():
    ipce_to_object([], {})


@raises(TypeError)
def test_abnormal_no_nulls():
    object_to_ipce(None, {})


# @raises(TypeError)
def test_abnormal_no_lists_2():
    object_to_ipce([1], {})


@raises(ValueError)
def test_abnormal_json1():
    # noinspection PyTypeChecker
    to_canonical_json(x=None)


@raises(ValueError)
def test_the_tester0():
    assert_regular_memory_json({LINKS: {}})


@raises(ValueError)
def test_the_tester1():
    assert_regular_memory_json({"one": {"/": "this should not be here"}})


@raises(ValueError)
def test_the_tester1_1():
    assert_regular_memory_json({LINKS: {}})


@raises(ValueError)
def test_the_tester_nonones():
    to_canonical_json({"one": None})


@raises(ValueError)
def test_the_tester_no_links():
    h = 'myhash'
    x = {"one": {"/": h}}
    assert_good_canonical(x)


@raises(ValueError)
def test_the_tester_no_links2():
    h = 'myhash'
    x = {LINKS: {}, "one": {"/": h}}
    assert_good_canonical(x)


def test_the_tester_no_links2_in_snd():
    h = 'myhash'
    x = {LINKS: {h: {}}, "one": {"/": h}}
    assert_good_canonical(x)


# @raises(ValueError)
# def test_the_tester_no_links2_in_snd_not():
#     h = 'myhash'
#     x = {LINKS: {h: {}}, "a": {"one": {"/": h}}}
#     assert_good_canonical(x)


@raises(ValueError)
def test_the_tester_no_links2_in_snd_not():
    h = 'myhash'
    x = {"a": {LINKS: {h: {}}}, "b": {"one": {"/": h}}}
    assert_good_canonical(x)


@raises(ValueError)
@with_private_register
def test_the_tester_no_links2_in_snd_not2_0():
    x = {"a": None}
    to_canonical_json(x)


@raises(ValueError)
@with_private_register
def test_the_tester_no_links2_in_snd_not2():
    class NotDataClass:
        ...

    T = NotDataClass
    type_to_schema(T, symbols)


@raises(AssertionError)
def test_not_optional():
    T = Optional[int]
    type_to_schema(T, symbols)


def test_not_union0():
    T = Union[int, str]
    type_to_schema(T, symbols)


@raises(ValueError)
def test_not_str1():
    # noinspection PyTypeChecker
    type_to_schema('T', symbols)


@raises(ValueError)
def test_not_fref2():
    # noinspection PyTypeChecker
    type_to_schema(ForwardRef('one'), {})


def test_any():
    # noinspection PyTypeChecker
    s = type_to_schema(Any, {})
    assert_equal(s, {SCHEMA_ATT: SCHEMA_ID})


# @raises(NotImplementedError)
def test_any_instantiate():
    # noinspection PyTypeChecker
    schema = type_to_schema(Name, {})
    ipce_to_object(schema, {})


@raises(TypeError)
def test_not_dict_naked():
    class A(dict):
        ...

    type_to_schema(A, {})


def test_any1b():
    schema: JSONSchema = {}
    t = schema_to_type(schema, {}, encountered={})
    assert is_Any(t), t


@with_private_register
def test_any2():
    @dataclass
    class C:
        a: Any

    e = C(12)
    assert_object_roundtrip(e, {})


@raises(CannotFindSchemaReference)
def test_invalid_schema():
    schema: JSONSchema = {"$ref": "not-existing"}
    schema_to_type(schema, {}, {})


# @raises(CannotFindSchemaReference)
def test_dict_only():
    T = Dict[str, str]
    _ = type_to_schema(T, {})


@raises(ValueError)
def test_str1():
    type_to_schema('string-arg', {})


@raises(ValueError)
def test_forward_ref1():
    type_to_schema(ForwardRef('AA'), {})


@raises(ValueError)
def test_forward_ref2():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: ForwardRef('unknown')

    type_to_schema(MyClass, {})


@raises(ValueError)
def test_forward_ref3():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: Optional['unknown']

    # do not put MyClass
    type_to_schema(MyClass, {})


@raises(ValueError)
def test_forward_ref4():
    class Other:
        pass

    @dataclass
    class MyClass:
        f: Optional['Other']

    # do not put MyClass
    type_to_schema(MyClass, {'Other': Other})


@raises(NotImplementedError)
def test_error1():
    def f():
        raise NotImplementedError()

    @dataclass
    class MyClass:
        f: Optional['f()']

    # do not put MyClass
    type_to_schema(MyClass, {'f': f})


def test_error2():
    X = TypeVar('X')

    @dataclass
    class M(Generic[X]):
        x: X
        # raise Exception()

    @dataclass
    class MyClass:
        f: "Optional[M[int]]"

    # do not put MyClass
    type_to_schema(MyClass, {'M': M})


@raises(ValueError)
@with_private_register
def test_to_canonical_no_none_values():
    x = {'x': None}
    to_canonical_json(x)


# for completeness
@raises(CannotResolveTypeVar)
def test_cannot_resolve():
    X = TypeVar('X')
    eval_field(X, {}, {})
