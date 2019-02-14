import argparse
import json
import sys
from typing import *

from .ipce import ipce_to_object, object_to_ipce
from .register import ConcreteRegister
from .types import Hash


def read_arguments(args: Sequence[str]) -> Iterator[str]:
    if len(args) == 0:
        sys.stderr.write('Reading hashes from stdin...\n')
        for h in sys.stdin:
            yield h.strip()
    else:
        for _ in args:
            yield _


def zj_main():
    MODE_STRINGS = 'string'
    MODE_JSON = 'json'
    MODE_OBJECT = 'object'
    MODE_OBJECT2J = 'object2j'
    MODE_OBJECT2J2H = 'object2j2h'
    choices = [MODE_STRINGS, MODE_JSON, MODE_OBJECT, MODE_OBJECT2J, MODE_OBJECT2J2H]

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', choices=choices, required=True)

    parsed, args = parser.parse_known_args()

    register = ConcreteRegister('zj.sqlite.db')
    for h in read_arguments(args):
        h: Hash = h
        if parsed.w == MODE_STRINGS:
            s = register.string_from_hash(h)
            print(s)
        if parsed.w == MODE_JSON:
            j = register.recall_json(h)
            print(json.dumps(j, indent=4))
        if parsed.w == MODE_OBJECT:
            j = register.recall_json(h)
            ob = ipce_to_object(j, globals())
            print(f'{ob!r}')
        if parsed.w == MODE_OBJECT2J:
            j = register.recall_json(h)
            ob = ipce_to_object(j, globals())
            obj = object_to_ipce(ob, globals())
            print(json.dumps(obj, indent=4))
        if parsed.w == MODE_OBJECT2J2H:
            j = register.recall_json(h)
            ob = ipce_to_object(j, globals())
            obj = object_to_ipce(ob, globals())
            h1 = register.store_json(obj)
            print(h1)

            # h1 = register.store_json(y1)


if __name__ == '__main__':
    zj_main()
