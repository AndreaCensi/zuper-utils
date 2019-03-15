from dataclasses import dataclass

from zuper_json.test_utils import assert_object_roundtrip, assert_type_roundtrip


def test_bool1():
    @dataclass
    class M:
        a: bool

    a = M(True)

    assert_object_roundtrip(a, {})
    assert_type_roundtrip(M, {})





def test_none1():
    assert_type_roundtrip(type(None), {})

    @dataclass
    class M:
        a: type(None)

    a = M(None)

    assert_object_roundtrip(a, {})
    assert_type_roundtrip(M, {})
