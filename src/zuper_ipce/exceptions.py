from zuper_typing.exceptions import ZValueError


class ZDeserializationError(ZValueError):
    pass


class ZDeserializationErrorSchema(ZDeserializationError):
    pass


class ZSerializationError(ZValueError):
    pass


class ZInvalidSchema(ZValueError):
    pass


IPCE_PASS_THROUGH = (NotImplementedError, KeyboardInterrupt, MemoryError, TypeError)
