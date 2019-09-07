from zuper_commons.types.exceptions import ZException


class ZTypeError(ZException, TypeError):
    pass


class ZValueError(ZException, ValueError):
    pass


class ZAssertionError(ZException, AssertionError):
    pass


class ZNotImplementedError(ZException, NotImplementedError):
    pass
