import logging

logging.basicConfig()

logger = logging.getLogger("zuper-typing")
logger.setLevel(logging.DEBUG)


def ztinfo(msg, **kwargs):
    from .debug_print_ import debug_print

    s = msg + "\n" + debug_print(kwargs)
    logger.info(s)
