__version__ = '3.0.3'
from .logging import logger

logger.info(f'zj {__version__}')

from .monkey_patching_typing import my_dataclass as dataclass

from .json2cbor import *
from .ipce import *
from .types import *
from .zeneric2 import StructuralTyping
