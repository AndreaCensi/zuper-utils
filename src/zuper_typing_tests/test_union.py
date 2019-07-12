from nose.tools import raises

from zuper_typing.annotations_tricks import make_Union


def test_making_union():
    make_Union(int)
    make_Union(int, float)
    make_Union(int, float, bool)
    make_Union(int, float, bool, str)
    make_Union(int, float, bool, str, bytes)
    make_Union(int, float, bool, str, bytes, int)



@raises(ValueError)
def test_corner_cases_empty_union():
    make_Union()


# @raises(ValueError)
def test_corner_cases_empty_union1():
    print(make_Union(int))
