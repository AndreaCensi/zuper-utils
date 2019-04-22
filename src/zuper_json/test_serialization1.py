from dataclasses import dataclass, field
from typing import *

from zuper_json.monkey_patching_typing import my_dataclass

try:
    from typing import ForwardRef
except ImportError: # pragma: no cover
    from typing import _ForwardRef as ForwardRef

from .annotations_tricks import is_Any
from .constants import SCHEMA_ATT, SCHEMA_ID
from .ipce import make_dict, ipce_to_object, object_to_ipce, type_to_schema, schema_to_type, \
    CannotFindSchemaReference, JSONSchema, CannotResolveTypeVar, eval_field
from .test_utils import assert_object_roundtrip


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


def test_ser1():
    x1 = Office()
    x1.people['andrea'] = Person('Andrea', 'Censi', Address('Sonnegstrasse', 3))

    assert_object_roundtrip(x1, get_symbols())


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


def get_symbols():
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
    return symbols


def test_optional_1():
    n1 = Name(first='H', middle='J', last='Wells')
    assert_object_roundtrip(n1, get_symbols())


def test_optional_2():
    n1 = Name(first='H', last='Wells')
    assert_object_roundtrip(n1, get_symbols())


def test_optional_3():
    n1 = Name(first='H', last='Wells')
    assert_object_roundtrip(n1, {}, expect_equality=True)


def test_recursive():
    n1 = Chain(value='12')
    assert_object_roundtrip(n1, {'Chain': Chain})


def test_ser_forward1():
    symbols = get_symbols()
    FA = symbols['FA']
    FB = symbols['FB']

    n1 = FA(value='a', down=FB(12))
    # with private_register('test_forward'):
    assert_object_roundtrip(n1, get_symbols())


def test_ser_forward2():
    n1 = Empty()
    assert_object_roundtrip(n1, get_symbols())


def test_ser_dict_object():
    @dataclass
    class M:
        x: int
        y: int

    @dataclass()
    class P:
        x: int
        y: int

    @dataclass(unsafe_hash=True)
    class N:
        x: int
        y: int

    @dataclass(frozen=True)
    class O:
        x: int
        y: int

    @dataclass(frozen=True, unsafe_hash=True)
    class L:
        x: int
        y: int

    @dataclass
    class M:
        a: Dict[L, str]

    d = {L(0, 0): 'one',
         L(1, 1): 'two'}
    m = M(d)
    symbols2 = {L.__qualname__: L}
    assert_object_roundtrip(m, symbols2)


from nose.tools import raises, assert_equal


def test_bytes1():
    n1 = Contents(b'1234')
    assert_object_roundtrip(n1, get_symbols())


@raises(ValueError)
def test_abnormal_no_schema():
    ipce_to_object({}, {})


def test_lists():
    ipce_to_object([], {})


def test_nulls():
    object_to_ipce(None, {})


def test_lists_2():
    object_to_ipce([1], {})


# @raises(ValueError)
# def test_the_tester_no_links2_in_snd_not():
#     h = 'myhash'
#     x = {LINKS: {h: {}}, "a": {"one": {"/": h}}}
#     assert_good_canonical(x)


@raises(ValueError)
def test_the_tester_no_links2_in_snd_not2():
    class NotDataClass:
        ...

    T = NotDataClass
    type_to_schema(T, get_symbols())


@raises(AssertionError)
def test_not_optional():
    T = Optional[int]
    type_to_schema(T, get_symbols())


def test_not_union0():
    T = Union[int, str]
    type_to_schema(T, {})


@raises(ValueError)
def test_not_str1():
    # noinspection PyTypeChecker
    type_to_schema('T', {})


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
    res = cast(JSONSchema, {})
    t = schema_to_type(res, {}, encountered={})
    assert is_Any(t), t


def test_any2():
    @dataclass
    class C:
        a: Any

    e = C(12)
    assert_object_roundtrip(e, {})


@raises(CannotFindSchemaReference)
def test_invalid_schema():
    schema = cast(JSONSchema, {"$ref": "not-existing"})
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


@raises(TypeError)
def test_forward_ref2():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: ForwardRef('unknown')

    type_to_schema(MyClass, {})


@raises(TypeError)
def test_forward_ref3():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: Optional['unknown']

    # do not put MyClass
    type_to_schema(MyClass, {})


@raises(TypeError)
def test_forward_ref4():
    class Other:
        pass

    @dataclass
    class MyClass:
        f: Optional['Other']

    # do not put MyClass
    type_to_schema(MyClass, {'Other': Other})


# @raises(NotImplementedError)
def test_error1():
    try:
        def f():
            raise NotImplementedError()

        @dataclass
        class MyClass:
            f: Optional['f()']

        # do not put MyClass
        type_to_schema(MyClass, {'f': f})
    except (TypeError, NotImplementedError, NameError):
        pass
    else:
        raise AssertionError()


def test_2_ok():
    X = TypeVar('X')

    @my_dataclass
    class M(Generic[X]):
        x: X

    @my_dataclass
    class MyClass:
        f: "Optional[M[int]]"

    # do not put M
    type_to_schema(MyClass, {'M': M})  # <---- note


@raises(TypeError)
def test_2_error():
    X = TypeVar('X')

    @my_dataclass
    class M(Generic[X]):
        x: X

    @my_dataclass
    class MyClass:
        f: "Optional[M[int]]"

    # do not put M
    type_to_schema(MyClass, {})  # <---- note


# for completeness
@raises(CannotResolveTypeVar)
def test_cannot_resolve():
    X = TypeVar('X')
    eval_field(X, {}, {})


@raises(AssertionError)
def test_random_json():
    """ Invalid because of $schema """
    data = {"$schema": {"title": "LogEntry"}, "topic": "next_episode", "data": None}
    ipce_to_object(data, {})


if __name__ == '__main__':
    test_error2()
