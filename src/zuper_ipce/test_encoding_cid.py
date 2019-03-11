import hashlib

import multihash
from nose.tools import assert_equal

from zuper_ipce.register import get_cbor_dag_hash
from zuper_json.test_utils import known_failure


def test_encoding1():
    import multihash
    ob = {}
    # as reported
    ob_h = 'zdpuAyTBnYSugBZhqJuLsNpzjmAjSmxDqBbtAqXMtsvxiN2v3'
    from cid import from_string
    cid = from_string(ob_h)
    print(cid)
    assert cid.codec == 'dag-cbor'
    assert cid.multihash == b'\x12 \xc1\x9ay\x7f\xa1\xfdY\x0c\xd2\xe5\xb4-\x1c\xf5\xf2F\xe2\x9b\x91hN/\x87@K\x81\xdc4\\zV\xa0'

    mh = multihash.decode(cid.multihash)
    print(mh)
    assert mh.digest == b'\xc1\x9ay\x7f\xa1\xfdY\x0c\xd2\xe5\xb4-\x1c\xf5\xf2F\xe2\x9b\x91hN/\x87@K\x81\xdc4\\zV\xa0'
    from cbor2 import CBOREncoder
    encoder = CBOREncoder(fp=None, canonical=True)
    ob_cbor = encoder.encode_to_bytes(ob)
    print(ob_cbor)
    ob_cbor_hash = hashlib.sha256(ob_cbor)
    print(ob_cbor_hash.digest())

    ob_h2 = get_cbor_dag_hash(ob)
    print(ob_h2)
    assert ob_h == ob_h2


def inspect_hash(h: str):
    from cid import from_string
    print(f'INSPECTING {h}')
    cid = from_string(h)
    mh = multihash.decode(cid.multihash)
    print(f' cid: {cid}')
    print(f' cid.codec: {cid.codec}')
    print(f' cid.version: {cid.version}')
    print(f' cid.multihash: {cid.multihash}')
    print(f' mh: {mh}')
    print(f' mh.code: {mh.code}')
    print(f' mh.length: {mh.length}')
    print(f' mh.digest: {mh.digest}')


def test_another01():
    ob = {}
    expect = 'zdpuAyTBnYSugBZhqJuLsNpzjmAjSmxDqBbtAqXMtsvxiN2v3'
    check(ob, expect)


@known_failure
def test_another04b():
    ob = 0
    expect = 'zdpuB39X55PgAai6zTPtTGtSrArCZh5ow1zE1d8ZGM6wwhPrZ'
    check(ob, expect)


@known_failure
def test_another02():
    ob = {'a': 1}
    expect = 'zdpuAxTWBh3d49ZCgPP44BT8AAa9qiqxB167yZCFdxHxVg6gN'
    check(ob, expect)


@known_failure
def test_another03():
    ob = 42
    expect = 'zdpuAvVUB18y6k8jZTZUHSq4FctExZm4Mxkt3xEyYW8ptQqru'
    check(ob, expect)


def test_another04():
    ob = {"a": "b"}
    expect = 'zdpuAw6c3ViCx5A7K4nukvmxh3ZtTHnyknmxCLQmGa6JDmDMn'
    check(ob, expect)


def test_another05():
    ob = "banana"
    expect = 'zdpuAxqDrc4Hnkr9PtqYpcuybpnJBwStaks6uwETeYq9gi9kB'
    check(ob, expect)


def test_another06():
    ob = None
    expect = 'zdpuAxKCBsAKQpEw456S49oVDkWJ9PZa44KGRfVBWHiXN3UH8'
    check(ob, expect)


def check(ob, expect):
    inspect_hash(expect)
    found = get_cbor_dag_hash(ob)
    inspect_hash(found)
    assert_equal(expect, found)


def test_another07():
    ob = ["a", "b"]
    expect = "zdpuAnPcrJDq4zxgHbrT1QZxjastWCs3U8bewnfPboBVwxEE8"
    check(ob, expect)


def test_another04c():
    ob = 0.0
    expect = 'zdpuB39X55PgAai6zTPtTGtSrArCZh5ow1zE1d8ZGM6wwhPrZ'
    check(ob, expect)
