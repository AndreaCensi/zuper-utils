from dataclasses import dataclass, field
from typing import List

from zuper_json.test_utils import known_failure, assert_type_roundtrip


@known_failure
def test_default_arguments():
    @dataclass
    class A1b:
        a: List[int] = field(default_factory=list)

    F = assert_type_roundtrip(A1b, {}, expect_type_equal=False)
    F(a=[])
    F()
