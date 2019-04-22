from dataclasses import dataclass
from typing import Optional

from zuper_json.test_utils import assert_type_roundtrip


def test_recursive01():
    @dataclass
    class Rec1:
        a: int
        parent: 'Rec1'

    assert_type_roundtrip(Rec1, {})


def test_recursive02():
    @dataclass
    class Rec2:
        a: int
        parent: 'Optional[Rec2]'

    assert_type_roundtrip(Rec2, {})


def test_recursive03():
    @dataclass
    class Rec3:
        a: int
        parent: Optional['Rec3']

    assert_type_roundtrip(Rec3, {})

