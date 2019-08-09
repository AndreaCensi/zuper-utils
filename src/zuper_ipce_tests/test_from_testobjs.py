import gzip
from dataclasses import dataclass
from typing import Iterator
from unittest import SkipTest

import cbor2

from zuper_commons.fs import locate_files, os, read_bytes_from_file
from zuper_ipce import IPCE, ipce_from_object, object_from_ipce


@dataclass
class Case:
    fn: str
    ipce: IPCE
    digest: str


def find_objects(load: bool = True) -> Iterator[Case]:
    d = 'test_objects'
    filenames = locate_files(d, '*.ipce.cbor.gz', normalize=False)
    for f in filenames:
        if load:
            data = read_bytes_from_file(f)
            ipce = cbor2.loads(data)
        else:
            ipce = None
        digest, _, _ = os.path.basename(f).partition('.')
        yield Case(f, ipce=ipce, digest=digest)


#
# def test_from_test_objects():
#     for case in find_objects():
#         print(case.fn)
#         ob = object_from_ipce(case.ipce, {})
#         ipce2 = ipce_from_object(ob)

def check_case(fn: str):
    if not os.path.exists(fn):
        raise SkipTest(f"File {fn} not found")
    print('check_case ' + fn)
    ipce_gz = read_bytes_from_file(fn)
    ipce_cbor = gzip.decompress(ipce_gz)
    ipce = cbor2.loads(ipce_cbor)
    ob = object_from_ipce(ipce, {})
    print(ob)
    ipce2 = ipce_from_object(ob)
    assert ipce == ipce2


def main():
    print("""
from .test_from_testobjs import check_case
    """)
    for case in find_objects(load=False):
        s = f"""
def test_{case.digest}():
    fn = {case.fn!r}
    check_case(fn)
"""
        print(s)


if __name__ == '__main__':
    main()
