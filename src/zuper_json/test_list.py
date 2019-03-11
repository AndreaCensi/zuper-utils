from dataclasses import dataclass
from typing import List

from .test_utils import assert_object_roundtrip, \
    with_private_register


@with_private_register
def test_list_1():
    @dataclass
    class MyClass:
        f: List[int]

    e = MyClass([1, 2, 3])
    assert_object_roundtrip(e, {})
