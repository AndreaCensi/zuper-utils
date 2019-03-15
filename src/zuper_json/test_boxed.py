from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, is_dataclass
from typing import *

try:
    from typing import ForwardRef
except ImportError:
    from typing import _ForwardRef as ForwardRef

from nose.tools import raises, assert_equal

from .constants import BINDINGS_ATT
from .test_utils import assert_object_roundtrip
from .zeneric2 import NoConstructorImplemented

X = TypeVar('X')


@raises(TypeError)
def test_boxed1():
    @dataclass
    class Boxed(Generic[X]):
        inside: X

    # cannot instance yet
    Boxed(inside=13)
    # assert_object_roundtrip(n1, {'Boxed': Boxed})


def test_boxed2():
    @dataclass
    class BoxedZ(Generic[X]):
        inside: X

    # print(BoxedZ.__eq__)

    C = BoxedZ[int]
    # print(pretty_dict('BoxedZ[int]', C.__dict__))

    assert_equal(C.__annotations__, {'inside': int})

    n1 = C(inside=13)

    assert_object_roundtrip(n1, {'BoxedZ': BoxedZ})


@raises(TypeError)
def test_boxed_cannot():
    # without @dataclass
    class CannotInstantiateYet(Generic[X]):
        inside: X

    # print(CannotInstantiateYet.__init__)
    # noinspection PyArgumentList
    CannotInstantiateYet(inside=13)


@raises(TypeError)
def test_boxed_cannot2():
    class CannotInstantiateYet(Generic[X]):
        inside: X

    # print(CannotInstantiateYet.__init__)
    # assert_equal(CannotInstantiateYet.__init__.__name__, 'cannot_instantiate')
    CI = dataclass(CannotInstantiateYet)
    # print(CannotInstantiateYet.__init__)
    # assert_equal(CannotInstantiateYet.__init__.__name__, 'new_init')
    # print(CI.__init__)
    CI(inside=13)


def test_boxed_can_dataclass():
    @dataclass
    class CannotInstantiateYet(Generic[X]):
        inside: X

    print('name: %s %s' % (CannotInstantiateYet.__name__, CannotInstantiateYet))
    assert 'CannotInstantiateYet' in CannotInstantiateYet.__name__, CannotInstantiateYet.__name__

    assert is_dataclass(CannotInstantiateYet)
    print('calling')
    CanBeInstantiated = CannotInstantiateYet[str]

    assert 'CannotInstantiateYet[str]' in CanBeInstantiated.__name__, CanBeInstantiated.__name__
    print('CanBeInstantiated: %s %s' % (CanBeInstantiated.__name__, CanBeInstantiated))

    print(CanBeInstantiated.__init__)

    CanBeInstantiated(inside="13")


def test_boxed_can_with_dataclass():
    @dataclass
    class CannotInstantiateYet(Generic[X]):
        inside: X

    CanBeInstantiated = CannotInstantiateYet[str]

    CanBeInstantiated(inside="12")


def _do_parametric(decorator=lambda _: _):
    class Animal(metaclass=ABCMeta):
        @abstractmethod
        def verse(self):
            """verse"""

    A = TypeVar('A', bound=Animal)

    @decorator
    class Parametric(Generic[A]):
        inside: A
        AT: ClassVar[Type[A]]

        def check_knows_type(self, Specific):
            T = type(self)
            a: A = type(self).AT()
            a.verse()

            assert (self.AT is getattr(T, BINDINGS_ATT)[A])
            assert (self.AT is Specific)

    class Dog(Animal):
        def verse(self):
            return 'wof'

    fido = Dog()
    PDog = Parametric[Dog]
    assert 'inside' not in PDog.__dict__, PDog.__dict__
    assert 'AT' in PDog.__dict__, PDog.__dict__
    p = PDog(inside=fido)
    p.check_knows_type(Dog)


@raises(NoConstructorImplemented)
def test_parametric_zeneric():
    _do_parametric(lambda _: _)


def test_parametric_zeneric_dataclass():
    _do_parametric(dataclass)
