from functools import wraps
from typing import Tuple
from unittest import SkipTest

from nose.plugins.attrib import attr


def known_failure(f, forbid: Tuple[type, ...] = ()):  # pragma: no cover
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except BaseException as e:

            if forbid:
                if isinstance(e, forbid):
                    msg = f"Known failure test is not supposed to raise {type(e).__name__}"
                    raise AssertionError(msg) from e

            raise SkipTest("Known failure test failed: " + str(e))
        raise AssertionError("test passed but marked as work in progress")

    return attr("known_failure")(run_test)


def relies_on_missing_features(f):
    msg = "Test relying on not implemented feature."

    @wraps(f)
    def run_test(*args, **kwargs):  # pragma: no cover
        try:
            f(*args, **kwargs)
        except BaseException as e:
            raise SkipTest(msg) from e
        raise AssertionError("test passed but marked as work in progress")

    return attr("relies_on_missing_features")(run_test)
