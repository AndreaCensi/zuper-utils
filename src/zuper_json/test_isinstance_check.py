from zuper_json import dataclass, StructuralTyping


def test1():
    @dataclass
    class C1(metaclass=StructuralTyping):
        a: int
        b: float

    @dataclass
    class C2(metaclass=StructuralTyping):
        a: int
        b: float
        c: str

    c1 = C1(1, 2)
    c2 = C2(1, 2, 'a')

    assert isinstance(c1, C1)
    assert isinstance(c2, C2)
    assert isinstance(c2, C1)

    assert issubclass(C2, C1)
