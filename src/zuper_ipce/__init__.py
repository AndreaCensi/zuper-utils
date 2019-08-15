__version__ = "3.0.3"
from .logging import logger

logger.info(f"zj {__version__}")


# noinspection PyUnresolvedReferences
from typing import Generic

from .json2cbor import *
from .utils_text import *
from .types import *
