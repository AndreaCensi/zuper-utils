import inspect
import os
from typing import Optional

from zuper_commons.text import indent
from zuper_typing.debug_print_ import debug_print
from zuper_typing.logging import logger


def ztinfo(msg: Optional[str] = None, **kwargs):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)

    frame, filename, line, fname, *rest = calframe[1]
    fn = os.path.basename(filename)

    if msg is None:
        msg = ""
    m = str(msg)
    for k, v in kwargs.items():
        m += "\n" + indent(debug_print(v), "│  ", k + ":  ")

    logger.info(f"{fn}:{line}|" + fname + "()|" + "\n" + m)
