from nose.tools import raises

from zuper_ipce.special_strings import Email


@raises(ValueError)
def test_email():
    Email("aaa")


def test_email_ok():
    Email("a@a.com")
