from nose.tools import assert_equal

from zuper_ipce import ipce_from_typelike
from zuper_ipce.utils_text import oyaml_load
from zuper_typing import dataclass


def test_u_of_one():
    @dataclass
    class A:
        v: int = 2

    ipce = ipce_from_typelike(A)
    # print(oyaml_dump(ipce))

    expect = """\
$id: http://invalid.json-schema.org/test_u_of_one.<locals>.A#
$schema: http://json-schema.org/draft-07/schema#
__module__: zuper_ipce_tests.test_union_of_one
__qualname__: test_u_of_one.<locals>.A
order: [v]
properties:
  v:
    $schema: http://json-schema.org/draft-07/schema#
    anyOf:
    - {$schema: 'http://json-schema.org/draft-07/schema#', type: integer}
    default: 2
title: A
type: object
"""
    expect_ipce = oyaml_load(expect)
    assert_equal(expect_ipce, ipce)
