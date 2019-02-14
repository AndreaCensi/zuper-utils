from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import *
# noinspection PyUnresolvedReferences
from typing import ForwardRef

from nose.tools import raises, assert_equal

from .constants import BINDINGS_ATT
from .test_utils import assert_object_roundtrip, with_private_register
from .zeneric2 import NoConstructorImplemented

X = TypeVar('X')


@raises(TypeError)
@with_private_register
def test_boxed1():

    @dataclass
    class Boxed(Generic[X]):
        inside: X

    # cannot instance yet
    Boxed(inside=13)
    # assert_object_roundtrip(n1, {'Boxed': Boxed})


@with_private_register
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
    # without @zataclass
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

    CanBeInstantiated = CannotInstantiateYet[str]

    CanBeInstantiated(inside="13")


def test_boxed_can_zataclass():
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

#
# def test_parametric_zeneric_zataclass():
#     _do_parametric(zataclass)
