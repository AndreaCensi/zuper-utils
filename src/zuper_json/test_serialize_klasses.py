# @relies_on_missing_features
from dataclasses import dataclass
from typing import Dict

from zuper_json.ipce import object_to_ipce
from zuper_json.pretty import pprint
from zuper_json.test_utils import assert_type_roundtrip, assert_object_roundtrip


def test_serialize_klasses0():
    assert_type_roundtrip(type, {})

    @dataclass
    class A:
        a: int

    Aj = object_to_ipce(A, {})
    pprint(Aj=Aj)

    assert_object_roundtrip(A, {}, expect_equality=False)  # because of classes


def test_serialize_klasses1():
    @dataclass
    class MyLanguage:
        my_types: Dict[str, type]

    @dataclass
    class A:
        a: int
        pass

    a = MyLanguage({'a': A})
    assert_type_roundtrip(MyLanguage, {})

    assert_object_roundtrip(a, {}, expect_equality=False)  # because of classes


def test_serialize_klasses2():
    @dataclass
    class MyLanguage:
        my_type: type

    @dataclass
    class A:
        a: int

    a = MyLanguage(A)
    assert_type_roundtrip(MyLanguage, {})

    assert_object_roundtrip(a, {}, expect_equality=False)  # because of classes
