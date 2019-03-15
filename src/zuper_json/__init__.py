__version__ = '0.2.1'
from . import monkey_patching_typing
from .logging import logger

logger.info(f'zuper-utils {__version__}')

from .json2cbor import *
