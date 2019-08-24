from nose.tools import assert_equal

from zuper_typing.my_intersection import (
    Intersection,
    get_Intersection_args,
    is_Intersection,
    make_Intersection,
)


def test_intersection1():
    args = (int, bool)
    T = make_Intersection(args)
    assert is_Intersection(T)
    assert_equal(get_Intersection_args(T), args)


def test_intersection2():
    T = Intersection[int, bool]
    assert is_Intersection(T)

    assert_equal(get_Intersection_args(T), (int, bool))
