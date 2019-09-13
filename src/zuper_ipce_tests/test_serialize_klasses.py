from zuper_ipce import ipce_from_object
from zuper_typing import dataclass
from zuper_typing.my_dict import make_dict
from .test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_serialize_klasses0():
    assert_type_roundtrip(type)

    @dataclass
    class A:
        a: int

    Aj = ipce_from_object(A)
    # pprint(Aj=Aj)

    assert_object_roundtrip(A, expect_equality=False)  # because of classes


def test_serialize_klasses1():
    """ Note: equality does not come because the two As do not compare equal """
    D = make_dict(str, type)

    @dataclass
    class MyLanguage:
        # my_types: Dict[str, type]
        my_types: D

    @dataclass
    class A:
        a: int
        pass

    x = MyLanguage(D({"A": A}))

    assert_type_roundtrip(MyLanguage)
    #
    # x2: MyLanguage = object_from_ipce(ipce_from_object(x), {}, {})
    # print(f' x: {x}')
    # print(f'x2: {x2}')
    # assert_equal(x.my_types['A'], x2.my_types['A'])
    # assert_equal(x.my_types, x2.my_types)
    # assert x == x2

    expect_equality = False
    assert_object_roundtrip(x, expect_equality=expect_equality)  # because of classes


def test_serialize_klasses2():
    @dataclass
    class MyLanguage:
        my_type: type

    @dataclass
    class A:
        a: int

    a = MyLanguage(A)
    assert_type_roundtrip(MyLanguage)

    expect_equality = False
    assert_object_roundtrip(a, expect_equality=expect_equality)  # because of classes
