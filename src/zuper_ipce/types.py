from datetime import datetime
from typing import Dict, List, Union

from zuper_typing.annotations_tricks import is_Any

IPCE = Union[
    int, str, float, bytes, datetime, List["IPCE"], Dict[str, "IPCE"], type(None)
]

__all__ = ["IPCE", "TypeLike"]

from zuper_typing.aliases import TypeLike

_ = TypeLike


def is_unconstrained(t: TypeLike):
    assert t is not None
    return is_Any(t) or (t is object)
