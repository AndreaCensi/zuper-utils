import json

from zuper_json.base64_utils import encode_bytes_base64, is_encoded_bytes_base64, decode_bytes_base64


def json_dump(x) -> str:
    x = recursive_sort(x)

    if False:
        s = json.dumps(x, ensure_ascii=False, allow_nan=False, check_circular=False,
                       indent=2)
    else:
        s = json.dumps(x, ensure_ascii=False, allow_nan=False, check_circular=False,
                       separators=(',', ':'))
    # (optional): put the links on the same line instead of indenting
    # "$schema": {"/": "sha6:92c65f"},

    # s = re.sub(r'\n\s+\"/\"(.*)\s*\n\s*', r'"/"\1', s)

    return s


def recursive_sort(x):
    if isinstance(x, dict):
        s = sorted(x)
        return {k: recursive_sort(x[k]) for k in s}
    else:
        return x


def transform_leaf(x, transform):
    if isinstance(x, dict):
        return {k: transform_leaf(v, transform) for k, v in x.items()}
    if isinstance(x, list):
        return [transform_leaf(_, transform) for _ in x]
    # if isinstance(x, (str, bool, float, int, type(None))):
    return transform(x)

from decimal import Decimal

DECIMAL_PREFIX = 'decimal:'
def encode_bytes_before_json_serialization(x0):
    def f(x):
        if isinstance(x, bytes):
            return encode_bytes_base64(x)
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
            x = x.replace(DECIMAL_PREFIX, '')
            return Decimal(x)
        else:
            return x
    return transform_leaf(x0, f)
