from nose.tools import raises

from zuper_ipce.ipce_spec import assert_canonical_ipce


@raises(ValueError)
def test_spec1():
    x = {"/": ""}
    assert_canonical_ipce(x)


@raises(ValueError)
def test_spec2():
    x = {"$links": {}}
    assert_canonical_ipce(x)


@raises(ValueError)
def test_spec3():
    x = {"$self": {}}
    assert_canonical_ipce(x)


@raises(ValueError)
def test_spec4():
    x = (1, 2)
    assert_canonical_ipce(x)


def test_spec4ok():
    x = [1, 2]
    assert_canonical_ipce(x)
