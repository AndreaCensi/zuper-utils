from functools import wraps
from unittest import SkipTest

from nose.plugins.attrib import attr


def fail(message):  # pragma: no cover
    raise AssertionError(message)


def known_failure(f):  # pragma: no cover
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest("Known failure test failed: " + str(e))
        fail("test passed but marked as work in progress")

    return attr('known_failure')(run_test)


def relies_on_missing_features(f):
    msg = "Test relying on not implemented feature."

    @wraps(f)
    def run_test(*args, **kwargs):  # pragma: no cover
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest(msg) from e
        fail("test passed but marked as work in progress")

    return attr('relies_on_missing_features')(run_test)
