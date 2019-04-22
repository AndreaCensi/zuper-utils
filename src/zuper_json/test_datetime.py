from datetime import datetime

from nose.tools import raises

from zuper_json.test_utils import assert_type_roundtrip, assert_object_roundtrip


def test_datetime01():
    assert_type_roundtrip(datetime, {})


@raises(ValueError)
def test_datetime02():
    d = datetime.now()
    assert_object_roundtrip(d, {})


import pytz


def test_datetime03():
    d = datetime.now()
    timezone = pytz.timezone("America/Los_Angeles")
    d_aware = timezone.localize(d)
    assert_object_roundtrip(d_aware, {})
