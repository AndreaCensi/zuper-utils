from nose.tools import raises

try:
    from typing import ForwardRef
except ImportError:
    from typing import _ForwardRef as ForwardRef

from zuper_ipce.as_json import to_canonical_json, assert_regular_memory_json, assert_good_canonical
from zuper_ipce.ipce_constants import LINKS
from .test_utils import with_private_register


@raises(ValueError)
def test_the_tester_no_links2_in_snd_not():
    h = 'myhash'
    x = {"a": {LINKS: {h: {}}}, "b": {"one": {"/": h}}}
    assert_good_canonical(x)


@raises(ValueError)
def test_the_tester0():
    assert_regular_memory_json({LINKS: {}})


@raises(ValueError)
def test_the_tester1():
    assert_regular_memory_json({"one": {"/": "this should not be here"}})


@raises(ValueError)
def test_the_tester1_1():
    assert_regular_memory_json({LINKS: {}})


@raises(ValueError)
def test_the_tester_no_links2():
    h = 'myhash'
    x = {LINKS: {}, "one": {"/": h}}
    assert_good_canonical(x)


def test_the_tester_no_links2_in_snd():
    h = 'myhash'
    x = {LINKS: {h: {}}, "one": {"/": h}}
    assert_good_canonical(x)


@raises(ValueError)
def test_abnormal_json1():
    # noinspection PyTypeChecker
    to_canonical_json(x=None)


@raises(ValueError)
def test_the_tester_nonones():
    to_canonical_json({"one": None})


@raises(ValueError)
def test_the_tester_no_links():
    h = 'myhash'
    x = {"one": {"/": h}}
    assert_good_canonical(x)


@raises(ValueError)
@with_private_register
def test_the_tester_no_links2_in_snd_not2_0():
    x = {"a": None}
    to_canonical_json(x)


@raises(ValueError)
@with_private_register
def test_to_canonical_no_none_values():
    x = {'x': None}
    to_canonical_json(x)
