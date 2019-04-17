__version__ = '2.0.2'
from . import monkey_patching_typing
from .logging import logger

logger.info(f'zj {__version__}')

from .json2cbor import *
