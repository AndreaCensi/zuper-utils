__version__ = '3.0.3'
from .logging import logger

logger.info(f'zj {__version__}')

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from dataclasses import dataclass
else:
    from .monkey_patching_typing import my_dataclass as dataclass

# noinspection PyUnresolvedReferences
from typing import Generic

from .json2cbor import *
from .ipce import *
from .types import *
from .zeneric2 import StructuralTyping
