from datetime import datetime
from typing import Dict, List, Union

IPCE = Union[
    int, str, float, bytes, datetime, List["IPCE"], Dict[str, "IPCE"], type(None)
]

__all__ = ["IPCE", "TypeLike"]

from zuper_typing.aliases import TypeLike

_ = TypeLike
