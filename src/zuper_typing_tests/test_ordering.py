from typing import Optional

from zuper_typing import dataclass


def test_ordering():
    @dataclass
    class C:
        root: Optional[int]
        links: int

    # print(C.__annotations__)

    a = C(1, 2)
    assert a.root == 1
    assert a.links == 2
    assert C(1, 2) == C(root=1, links=2)
