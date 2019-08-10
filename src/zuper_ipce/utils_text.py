import hashlib

import base58


def get_sha256_base58(contents):
    m = hashlib.sha256()
    m.update(contents)
    s = m.digest()
    return base58.b58encode(s)
