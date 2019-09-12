from dataclasses import field
from typing import Any, cast, Dict, NewType, Optional, TypeVar, Union

from zuper_commons.logs import setup_logging
from zuper_ipce import ipce_from_typelike, object_from_ipce, typelike_from_ipce
from zuper_ipce.constants import JSONSchema, SCHEMA_ATT, SCHEMA_ID
from zuper_ipce.structures import CannotFindSchemaReference
from zuper_typing import Generic
from zuper_typing.annotations_tricks import make_ForwardRef
from zuper_typing.monkey_patching_typing import my_dataclass as dataclass
from zuper_typing.my_dict import make_dict
from zuper_typing_tests.test_utils import known_failure
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


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


def test_ser0():
    """ Make sure we can have a constructor with default """

    # class Office0:
    #     """ An Office contains people. """
    #     people: Dict[str, Person] = field(default_factory=make_dict(str, Person))
    #
    # print(Office0.__dict__)

    Office()


def test_ser1():
    # Address_schema = type_to_schema(Address, {})
    # assert Address_schema['description'] == Address.__doc__
    # Address2 = schema_to_type(Address_schema, {}, {})
    # assert Address2.__doc__ == Address.__doc__

    Person_schema = ipce_from_typelike(Person)

    # print(oyaml_dump(Person_schema))

    Address2 = typelike_from_ipce(Person_schema["properties"]["address"])
    assert_equal(Address2.__doc__, Address.__doc__)

    assert Person_schema["description"] == Person.__doc__
    Person2 = typelike_from_ipce(Person_schema)
    assert Person2.__doc__ == Person.__doc__

    assert_equal(Person2.__annotations__["address"].__doc__, Address.__doc__)

    assert_type_roundtrip(Address, expect_type_equal=False)
    assert_type_roundtrip(Person, expect_type_equal=False)
    assert_type_roundtrip(Office, expect_type_equal=False)

    x1 = Office()
    x1.people["andrea"] = Person("Andrea", "Censi", Address("Sonnegstrasse", 3))

    assert_object_roundtrip(x1, use_globals=get_symbols())


def test_ser2():
    x1 = Office()
    x1.people["andrea"] = Person("Andrea", "Censi", Address("Sonnegstrasse", 3))

    assert_object_roundtrip(x1, expect_equality=True)


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

    down: Optional["Chain"] = None


def get_symbols():
    @dataclass
    class FB:
        mine: int

    @dataclass
    class FA:
        """ Describes a Name with optional middle name"""

        value: str

        down: FB

    symbols = {
        "Office": Office,
        "Person": Person,
        "Address": Address,
        "Name": Name,
        "Contents": Contents,
        "Empty": Empty,
        "FA": FA,
        "FB": FB,
        "Chain": Chain,
    }
    return symbols


def test_optional_1():
    n1 = Name(first="H", middle="J", last="Wells")
    assert_object_roundtrip(n1, use_globals=get_symbols())


def test_optional_2():
    n1 = Name(first="H", last="Wells")
    assert_object_roundtrip(n1, use_globals=get_symbols())


def test_optional_3():
    n1 = Name(first="H", last="Wells")
    assert_object_roundtrip(n1, expect_equality=True)


def test_recursive():
    n1 = Chain(value="12")
    assert_object_roundtrip(n1, use_globals={"Chain": Chain})


def test_ser_forward1():
    symbols = get_symbols()
    FA = symbols["FA"]
    FB = symbols["FB"]

    n1 = FA(value="a", down=FB(12))
    # with private_register('test_forward'):
    assert_object_roundtrip(n1, use_globals=get_symbols())


def test_ser_forward2():
    n1 = Empty()
    assert_object_roundtrip(n1, use_globals=get_symbols())


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

    d = {L(0, 0): "one", L(1, 1): "two"}
    m = M(d)
    symbols2 = {L.__qualname__: L}
    assert_object_roundtrip(m, use_globals=symbols2)


from nose.tools import raises, assert_equal


def test_bytes1():
    n1 = Contents(b"1234")
    assert_object_roundtrip(n1, use_globals=get_symbols())


@raises(ValueError)
def test_abnormal_no_schema():
    res = object_from_ipce({})
    # logger.info(f"res = {res!r}")
    # logger.info(f"type = {type(res)}")
    #


def test_lists():
    object_from_ipce([])


def test_nulls():
    assert_object_roundtrip(None)


def test_lists_2():
    assert_object_roundtrip([1])


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
    ipce_from_typelike(T, globals0=get_symbols())


# @raises(AssertionError)
def test_not_optional():
    T = Optional[int]
    ipce_from_typelike(T, globals0=get_symbols())


def test_not_union0():
    T = Union[int, str]
    ipce_from_typelike(T)


@raises(ValueError)
def test_not_str1():
    # noinspection PyTypeChecker
    ipce_from_typelike("T")


@raises(ValueError)
def test_not_fref2():
    # noinspection PyTypeChecker
    ipce_from_typelike(make_ForwardRef("one"))


def test_serialize_any():
    # noinspection PyTypeChecker
    s = ipce_from_typelike(Any)
    assert_equal(s, {SCHEMA_ATT: SCHEMA_ID, "title": "Any"})

    assert assert_type_roundtrip(Any)


def test_serialize_object():
    # noinspection PyTypeChecker
    s = ipce_from_typelike(object)
    assert_equal(s, {SCHEMA_ATT: SCHEMA_ID, "title": "object"})

    assert assert_type_roundtrip(object)


# @raises(NotImplementedError)
def test_any_instantiate():
    # noinspection PyTypeChecker
    schema = ipce_from_typelike(Name)
    object_from_ipce(schema)


@known_failure
def test_not_dict_naked():
    class A(dict):
        ...

    ipce_from_typelike(A)


def test_any1b():
    res = cast(JSONSchema, {})
    t = typelike_from_ipce(res)
    assert t is object, t


def test_any2():
    @dataclass
    class C:
        a: Any

    e = C(12)
    assert_object_roundtrip(e)


@raises(CannotFindSchemaReference)
def test_invalid_schema():
    schema = cast(JSONSchema, {"$ref": "not-existing"})
    typelike_from_ipce(schema)


# @raises(CannotFindSchemaReference)
def test_dict_only():
    T = Dict[str, str]
    _ = ipce_from_typelike(T)


@raises(ValueError)
def test_str1():
    # noinspection PyTypeChecker
    ipce_from_typelike("string-arg")


@raises(ValueError)
def test_forward_ref1():
    ipce_from_typelike(make_ForwardRef("AA"))


@raises(TypeError)
def test_forward_ref2():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: make_ForwardRef("unknown")

    ipce_from_typelike(MyClass)


@raises(TypeError)
def test_forward_ref3():
    @dataclass
    class MyClass:
        # noinspection PyUnresolvedReferences
        f: Optional["unknown"]

    # do not put MyClass
    ipce_from_typelike(MyClass)


@raises(TypeError)
def test_forward_ref4():
    class Other:
        pass

    @dataclass
    class MyClass:
        f: Optional["Other"]

        __depends__ = (Other,)

    # do not put MyClass
    g = {"Other": Other}
    ipce_from_typelike(MyClass, globals0=g)


# @raises(NotImplementedError)
# def test_error1():
#     try:
#         def f():
#             raise NotImplementedError()
#
#         @dataclass
#         class MyClass:
#             f: Optional['f()']
#
#         # do not put MyClass
#         ipce_from_typelike(MyClass, {'f': f})
#     except (TypeError, NotImplementedError, NameError):
#         pass
#     else:
#         raise AssertionError()


def test_2_ok():
    X = TypeVar("X")

    @dataclass
    class M(Generic[X]):
        x: X

    @dataclass
    class MyClass:
        f: "Optional[M[int]]"

        __depends__ = (M,)

    # do not put M
    # ipce_from_typelike(MyClass, {'M': M})  # <---- note
    ipce_from_typelike(MyClass)  # <---- note


@raises(Exception)
def test_2_error():
    X = TypeVar("X")

    @dataclass
    class M(Generic[X]):
        x: X

    @dataclass
    class MyClass:
        f: "Optional[M[int]]"

    # do not put M
    ipce_from_typelike(MyClass)  # <---- note


# # for completeness
# @raises(CannotResolveTypeVar)
# def test_cannot_resolve():
#     X = TypeVar('X')
#     eval_field(X, {}, {})


@raises(TypeError)
def test_random_json():
    """ Invalid because of $schema """
    data = {"$schema": {"title": "LogEntry"}, "topic": "next_episode", "data": None}
    object_from_ipce(data)


def test_newtype_1():
    A = NewType("A", str)

    @dataclass
    class M10:
        a: A

    assert_type_roundtrip(M10)


def test_newtype_2():
    X = TypeVar("X")
    A = NewType("A", str)

    @dataclass
    class M11(Generic[X]):
        a: A

    assert_type_roundtrip(M11)

    #
    # def __init__(self, cid):
    #     self.cid = cid


def test_nonetype0():
    T = type(None)

    assert_type_roundtrip(T)
    assert_object_roundtrip(T)


def test_none2():
    T = None
    assert_object_roundtrip(T)


@raises(ValueError)
def test_none3():
    T = None
    assert_type_roundtrip(T)


def test_nonetype1():
    @dataclass
    class M12:
        a: type(None)

    assert_type_roundtrip(M12)

    assert_object_roundtrip(M12)


def test_optional0():
    T = Optional[int]

    assert_type_roundtrip(T)
    assert_object_roundtrip(T)


if __name__ == "__main__":
    setup_logging()
    test_ser0()
