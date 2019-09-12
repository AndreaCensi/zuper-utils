from zuper_ipce_tests.test_utils import assert_object_roundtrip, assert_type_roundtrip


# TODO:
# if not USE_REMEMBERED_CLASSES:  # pragma: no cover
#
#     def test_default_arguments():
#         @dataclass
#         class A1b:
#             a: List[int] = field(default_factory=list)
#
#         F = assert_type_roundtrip(A1b, expect_type_equal=False)
#         F(a=[])
#         F()


def test_object():
    T = object
    assert_type_roundtrip(T)


def test_slice():
    T = slice
    assert_type_roundtrip(T)


def test_slice1():
    T = slice(1, None, None)
    assert_object_roundtrip(T)


def test_slice2():
    T = slice(1, 2, None)
    assert_object_roundtrip(T)


def test_slice3():
    T = slice(1, 2, 3)
    assert_object_roundtrip(T)
