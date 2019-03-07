from nose.tools import raises

from zuper_ipce.as_json import to_canonical_json
from zuper_json.json_utils import json_dump
from zuper_ipce.register import get_register, get_links_prefix, IPFSDagRegister, ConcreteRegister
from .test_utils import with_private_register
from zuper_json.types import Hash
from zuper_ipce.constants import CanonicalJSONString


@raises(KeyError)
@with_private_register
def test_register_does_not_have_key():
    register = get_register()
    h: Hash = 'not-existing'
    register.string_from_hash(h)


@with_private_register
def test_register_uses_ipfs_for_recovering():
    register = get_register()

    ipfs = IPFSDagRegister()

    rs = get_random_string(32)
    x = {'random': rs}
    # rs_h = to_canonical_json(rs)
    x_c = to_canonical_json(x)
    x_c_json: CanonicalJSONString = json_dump(x_c)
    x_h_r = ipfs.hash_from_string(x_c_json)
    x_h = x_h_r.hash
    register.string_from_hash(x_h)

    # test a couple more things
    register.pretty_print()

    for _ in get_links_prefix(x_h):
        pass


@raises(ValueError)
def test_register_needs_parent():
    ConcreteRegister()


@raises(ValueError)
def test_need_push_before_get_register():
    get_register()


import random, string


def get_random_string(N):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
