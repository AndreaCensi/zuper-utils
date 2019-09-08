import hashlib
from typing import Any

import base58

__all__ = ["get_sha256_base58"]


def get_sha256_base58(contents: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(contents)
    s = m.digest()
    return base58.b58encode(s)


import oyaml


def oyaml_dump(x: object) -> str:
    return oyaml.dump(x)


def oyaml_load(x: str, **kwargs: Any) -> object:
    return oyaml.load(x, **kwargs)
