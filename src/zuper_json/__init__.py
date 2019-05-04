__version__ = '3.0.3'
from .logging import logger

logger.info(f'zj {__version__}')
from . import monkey_patching_typing

from .json2cbor import *
