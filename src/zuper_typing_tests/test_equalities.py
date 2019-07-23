from nose.tools import assert_equal

from zuper_typing.my_dict import make_list, make_set, make_dict


def test_eq1():
    a = make_list(int)
    b = make_list(int)
    assert a == b
    assert_equal(a, b)

def test_eq_set():
    a = make_set(int)
    b = make_set(int)
    assert a == b
    assert_equal(a, b)

def test_eq_dict():
    a = make_dict(int, str)
    b = make_dict(int, str)

    assert a == b
    assert_equal(a, b)
