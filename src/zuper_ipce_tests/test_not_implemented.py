from dataclasses import dataclass, field
from typing import List

from zuper_ipce_tests.test_utils import assert_type_roundtrip
from zuper_typing_tests.test_utils import known_failure


@known_failure
def test_default_arguments():
    @dataclass
    class A1b:
        a: List[int] = field(default_factory=list)

    F = assert_type_roundtrip(A1b, {}, expect_type_equal=False)
    F(a=[])
    F()
