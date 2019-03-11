import json
import traceback
from json import JSONDecodeError

import cbor2

from . import logger

__all__ = [
    'read_cbor_or_json_objects',
    'json2cbor_main',
    'cbor2json_main',
]


def json2cbor_main():
    fo = open('/dev/stdout', 'wb')
    fi = open('/dev/stdin', 'rb')
    for j in read_cbor_or_json_objects(fi):
        c = cbor2.dumps(j)
        fo.write(c)
        fo.flush()


def cbor2json_main():
    fo = open('/dev/stdout', 'wb')
    fi = open('/dev/stdin', 'rb')
    for j in read_cbor_or_json_objects(fi):
        ob = json.dumps(j)
        ob = ob.encode('utf-8')
        fo.write(ob)
        fo.write(b'\n')
        fo.flush()


def read_cbor_or_json_objects(f):
    """ Reads cbor or line-separated json objects from the binary file f."""
    while True:
        first = f.peek(1)[:1]
        if len(first) == 0:
            break
        # logger.debug(f'first char is {first}')
        if first in [b' ', b'\n', b'{']:
            line = f.readline()
            line = line.strip()
            if not line: continue
            # logger.debug(f'line is {line!r}')
            try:
                j = json.loads(line)
            except JSONDecodeError:
                msg = f'Could not decode line {line!r}: {traceback.format_exc()}'
                logger.error(msg)
                continue
            yield j
        else:
            j = cbor2.load(f)
            yield j
