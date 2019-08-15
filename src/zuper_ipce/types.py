from datetime import datetime
from typing import Dict, List, Union

from .constants import _SpecialForm

IPCE = Union[
    int, str, float, bytes, datetime, List["IPCE"], Dict[str, "IPCE"], type(None)
]

__all__ = ["IPCE"]
TypeLike = Union[type, _SpecialForm]
