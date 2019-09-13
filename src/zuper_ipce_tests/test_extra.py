from typing import Any, Optional, TypeVar

from nose.tools import assert_equal

from zuper_ipce.pretty import pprint
from zuper_ipce_tests.test_utils import assert_type_roundtrip
from zuper_typing import dataclass, Generic


def test_type():
    X = TypeVar("X")
    Y = TypeVar("Y")

    class A:
        pass

    @dataclass
    class Another(Generic[Y]):
        data0: Y

    assert_equal("Another[Y]", Another.__name__)

    @dataclass
    class MyClass(Generic[X]):
        another: Another[X]

    # print(MyClass.__annotations__['another'].__annotations__['data0'])
    assert_equal(MyClass.__annotations__["another"].__annotations__["data0"], X)

    C = MyClass[A]
    # print(C.__annotations__["another"])
    # print(C.__annotations__["another"].__annotations__["data0"])
    assert_equal(C.__annotations__["another"].__annotations__["data0"], A)
    # print(C.__annotations__["another"])
    assert_equal(C.__annotations__["another"].__name__, "Another[A]")

    # cannot serialize because A is not a dataclass
    #
    # assert_type_roundtrip(Another, {})
    # assert_type_roundtrip(MyClass, {})
    # assert_type_roundtrip(C, {})


def test_type02():
    X = TypeVar("X")
    V = TypeVar("V")

    @dataclass
    class MyClass(Generic[X]):
        data0: X

    C0 = MyClass
    C1 = MyClass[V]

    # print(C0.__annotations__)
    # print(C1.__annotations__)

    assert C0.__annotations__["data0"] == X
    assert C1.__annotations__["data0"] == V

    assert_type_roundtrip(C0)
    assert_type_roundtrip(C1)


def test_type05():
    @dataclass
    class A:
        pass

    X = TypeVar("X")

    @dataclass
    class MyEntity(Generic[X]):
        guid: str

        forked1: "MyEntity[X]"
        forked2: Optional["MyEntity[X]"]
        forked3: "Optional[MyEntity[X]]"

    # print("%s" % MyEntity)
    # print("name: %s" % MyEntity.__name__)
    # resolve_types(MyEntity, locals())

    forked1_X = MyEntity.__annotations__["forked1"]
    # print(f"forked1_X: {forked1_X!r}")
    forked2_X = MyEntity.__annotations__["forked2"]
    # print(f"forked2_X: {forked2_X!r}")
    forked3_X = MyEntity.__annotations__["forked3"]
    # print(f"forked3_X: {forked3_X!r}")
    E = MyEntity[A]

    forked1_A = E.__annotations__["forked1"]
    # print(f"forked1_A: {forked1_A!r}")
    forked2_A = E.__annotations__["forked2"]
    # print(f"forked2_A: {forked2_A!r}")
    forked3_A = E.__annotations__["forked3"]
    # print(f"forked3_A: {forked3_A!r}")

    assert_equal(E.__name__, "MyEntity[A]")
    # assert_equal(E.__annotations__['parent'].__args__[0].__name__, Entity[Any].__name__)
    # print(E.__annotations__["forked1"])
    assert_equal(E.__annotations__["forked1"].__name__, MyEntity[A].__name__)
    # print(E.__annotations__["forked2"])
    assert_equal(
        E.__annotations__["forked2"].__args__[0].__name__, MyEntity[A].__name__
    )

    assert_type_roundtrip(MyEntity)


def test_type06():
    @dataclass
    class Values:
        a: int

    Z = TypeVar("Z")
    U = TypeVar("U")
    M = TypeVar("M")

    @dataclass
    class EntityUpdateProposal(Generic[M]):
        proposal: M

    A = EntityUpdateProposal[Z]
    assert_equal(A.__name__, "EntityUpdateProposal[Z]")
    assert_equal(A.__annotations__["proposal"], Z)

    @dataclass
    class Signed(Generic[U]):
        value: U

    B = Signed[EntityUpdateProposal[Z]]
    assert_equal(B.__name__, "Signed[EntityUpdateProposal[Z]]")
    assert_equal(B.__annotations__["value"].__name__, "EntityUpdateProposal[Z]")

    @dataclass
    class VersionChainWithAuthors(Generic[Z]):
        # signed_proposals: List[Signed[EntityUpdateProposal[Z]]]
        signed_proposal: Signed[EntityUpdateProposal[Z]]
        # previous: 'Optional[VersionChainWithAuthors[Z]]' = None

    # print("**********\n\n\n")
    C = VersionChainWithAuthors[Values]
    pprint("C annotations", C=C, **C.__annotations__)
    assert_equal(C.__name__, "VersionChainWithAuthors[Values]")

    assert_equal(
        C.__annotations__["signed_proposal"].__name__,
        "Signed[EntityUpdateProposal[Values]]",
    )
    # print(oyaml_dump(ipce_from_typelike(C)))
    #
    # assert_equal(E.__name__, 'Entity[A]')
    # assert_equal(E.__annotations__['parent'].__args__[0].__name__, Entity[Any].__name__)
    # pprint('Annotations of E', **E.__annotations__)
    # assert_equal(E.__annotations__['forked'].__args__[0].__name__, Entity[A].__name__)

    assert_type_roundtrip(A)
    assert_type_roundtrip(B)


def test_another():
    X = TypeVar("X")

    @dataclass
    class Entity4(Generic[X]):
        guid: str

        forked: "Optional[Entity4[X]]" = None

        parent: "Optional[Entity4[Any]]" = None

    assert_type_roundtrip(Entity4)


if __name__ == "__main__":
    test_another()
