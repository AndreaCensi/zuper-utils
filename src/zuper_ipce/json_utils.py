from datetime import datetime

from .base64_utils import (
    decode_bytes_base64,
    encode_bytes_base64,
    is_encoded_bytes_base64,
)


def transform_leaf(x, transform):
    if isinstance(x, dict):
        return {k: transform_leaf(v, transform) for k, v in x.items()}
    if isinstance(x, list):
        return [transform_leaf(_, transform) for _ in x]
    return transform(x)


from decimal import Decimal

DECIMAL_PREFIX = "decimal:"


def encode_bytes_before_json_serialization(x0):
    def f(x):
        if isinstance(x, bytes):
            return encode_bytes_base64(x)
        elif isinstance(x, datetime):
            return x.isoformat()
        elif isinstance(x, Decimal):
            return DECIMAL_PREFIX + str(x)
        else:
            return x

    return transform_leaf(x0, f)


def decode_bytes_before_json_deserialization(x0):
    def f(x):
        if isinstance(x, str) and is_encoded_bytes_base64(x):
            return decode_bytes_base64(x)
        elif isinstance(x, str) and x.startswith(DECIMAL_PREFIX):
            x = x.replace(DECIMAL_PREFIX, "")
            return Decimal(x)
        else:
            return x

    return transform_leaf(x0, f)
