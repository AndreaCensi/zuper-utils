import base64


def encode_bytes_base64(data: bytes, mime=None) -> str:
    encoded = base64.b64encode(data).decode('ascii')
    if mime is None:
        mime = 'binary/octet-stream'
    res = 'data:%s;base64,%s' % (mime, encoded)
    return res


def is_encoded_bytes_base64(s: str):
    return s.startswith('data:') and 'base64,' in s


def decode_bytes_base64(s: str) -> bytes:
    assert is_encoded_bytes_base64(s)
    i = s.index('base64,')
    j = i + len('base64,')
    s2 = s[j:]
    res = base64.b64decode(s2)
    return res
