from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Dict, ClassVar

from mypy_extensions import NamedArg

from zuper_typing.annotations_tricks import name_for_type_like
from zuper_typing.monkey_patching_typing import original_dict_getitem


def test_pretty1():
    @dataclass
    class Animal:
        a: int
        b: bool
        c: float
        d: datetime
        e: str
        f: bytes
        g: str
        h: str
        i: str
        j: str

    g = 'Traceback'
    h = '-----BEGIN ciao'
    i = 'zd...'
    j = 'Qm...'
    print(Animal)
    a = Animal(1, True, 0.1, datetime.now(), 'a', b'a', g, h, i, j)
    print(a.__repr__())
    print(a.__str__())


def test_pretty2():
    X = TypeVar('X', bound=Dict[str, str])
    print(X)
    Y = TypeVar('Y', contravariant=True)
    print(Y)
    Z = TypeVar('Z', covariant=True)
    print(Z)

