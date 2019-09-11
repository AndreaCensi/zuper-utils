__version__ = "3.0.3"
from .logging import logger

logger.info(f"zj {__version__}")

# noinspection PyUnresolvedReferences
# from typing import Generic

# from .json2cbor import *
# from .utils_text import *

from .types import IPCE, TypeLike
from .constants import IEDO, IESO
from .conv_ipce_from_object import ipce_from_object
from .conv_ipce_from_typelike import ipce_from_typelike
from .conv_object_from_ipce import object_from_ipce
from .conv_typelike_from_ipce import typelike_from_ipce

_ = (
    ipce_from_object,
    object_from_ipce,
    typelike_from_ipce,
    ipce_from_typelike,
    TypeLike,
    IPCE,
    IEDO,
    IESO,
)

# __all__ = ['IPCE', 'ipce_from_typelike' ,'ipce_from_object', 'object_from_ipce', 'typelike_from_ipce']
