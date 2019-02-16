from dataclasses import dataclass

from zuper_json.test_utils import assert_object_roundtrip, assert_type_roundtrip, with_private_register


@with_private_register
def test_bool1():
    @dataclass
    class M:
        a: bool

    a = M(True)

    assert_object_roundtrip(a, {})
    assert_type_roundtrip(M, {})

# @with_private_register
# def test_tuples1():
#
#     @dataclass
#     class M:
#         a: Tuple[int, str]
#
#     a = M((1,'32'))
#
#     assert_object_roundtrip(a, {})
#     assert_type_roundtrip(M, {})
