__version__ = '0.2.1'
from . import monkey_patching_typing
from .logging import logger

logger.info('Using zuper-utils version %s' % __version__)

from .json2cbor import  *

