import dataclasses
import typing

from numbers import Number
from typing import Generic

import yaml
from nose.tools import raises, assert_equal

from zuper_json import logger
from zuper_json.constants import enable_type_checking
from zuper_json.monkey_patching_typing import my_dataclass
from zuper_json.zeneric2 import resolve_types, dataclass
from .annotations_tricks import is_ClassVar, get_ClassVar_arg, is_Type, get_Type_arg, is_forward_ref
from .ipce import type_to_schema, schema_to_type
from .pretty import pprint
from .test_utils import assert_object_roundtrip, assert_type_roundtrip, known_failure


@raises(TypeError)
def test_dataclass_can_preserve_init():
    X = typing.TypeVar('X')

    @dataclass
    class M(Generic[X]):
        x: int

    M(x=2)


from dataclasses import fields


def test_serialize_generic_typevar():
    X = typing.TypeVar('X', bound=Number)

    @dataclass
    class M1(Generic[X]):
        """ A generic class """
        x: X

    M2 = assert_type_roundtrip(M1, {})

    f1 = fields(M1)
    assert f1[0].type == X
    # there was a bug with modifying this
    _ = M1[int]
    f1b = fields(M1)
    assert f1b[0].type == X
    assert f1 == f1b

    # M2 = assert_type_roundtrip(M1, {})


def test_serialize_generic():
    X = typing.TypeVar('X', bound=Number)

    @dataclass
    class M1(Generic[X]):
        """ A generic class """
        x: X

    M1int = M1[int]

    assert_type_roundtrip(M1, {})
    assert_type_roundtrip(M1int, {})

    m1a = M1int(x=2)
    m1b = M1int(x=3)
    s = type_to_schema(M1, {})
    # print(json.dumps(s, indent=3))

    M2 = schema_to_type(s, {}, {})
    # noinspection PyUnresolvedReferences
    M2int = M2[int]
    assert_equal(M1.__module__, M2.__module__)

    m2a = M2int(x=2)
    m2b = M2int(x=3)
    # print(m1a)
    # print(m2a)
    # print(type(m1a))
    # print(type(m2a))
    # print(type(m1a).__module__)
    # print(type(m2a).__module__)
    assert m1a == m2a
    assert m2a == m1a
    assert m2b == m1b
    assert m1b == m2b
    assert m1b != m1a
    assert m2b != m2a

    # assert_object_roundtrip(M, {'M': M})


def test_serialize_generic_optional():
    # @dataclass
    # class Animal:
    #     pass

    X = typing.TypeVar('X', bound=Number)

    @dataclass
    class M1(Generic[X]):
        """ A generic class """
        x: X
        xo: typing.Optional[X] = None

    M1int = M1[int]
    assert_type_roundtrip(M1, {})
    assert_type_roundtrip(M1int, {})

    m1a = M1int(x=2)
    m1b = M1int(x=3)
    s = type_to_schema(M1, {})
    # print(json.dumps(s, indent=3))

    M2 = schema_to_type(s, {}, {})
    # noinspection PyUnresolvedReferences
    M2int = M2[int]
    assert_equal(M1.__module__, M2.__module__)

    m2a = M2int(x=2)
    m2b = M2int(x=3)
    # print(m1a)
    # print(m2a)
    # print(type(m1a))
    # print(type(m2a))
    # print(type(m1a).__module__)
    # print(type(m2a).__module__)
    assert m1a == m2a
    assert m2a == m1a
    assert m2b == m1b
    assert m1b == m2b
    assert m1b != m1a
    assert m2b != m2a


from typing import Optional, TypeVar


def test_more():
    X = TypeVar('X')

    @dataclass
    class Entity0(Generic[X]):
        data0: X

        parent: "Optional[Entity0[X]]" = None

    resolve_types(Entity0)

    print(Entity0.__annotations__['parent'].__repr__())
    assert not isinstance(Entity0.__annotations__['parent'], str)
    # raise Exception()
    schema = type_to_schema(Entity0, {}, {})
    print(yaml.dump(schema))
    T = schema_to_type(schema, {}, {})
    print(T.__annotations__)

    assert_type_roundtrip(Entity0, {})

    EI = Entity0[int]

    assert_equal(EI.__annotations__['parent'].__args__[0].__name__, 'Entity0[int]')
    assert_type_roundtrip(EI, {})

    x = EI(data0=3, parent=EI(data0=4))

    assert_object_roundtrip(x, {})  # {'Entity': Entity, 'X': X})


def test_more_direct():
    # language=yaml
    schema = yaml.load("""
$id: http://invalid.json-schema.org/Entity0[X]#
$schema: http://json-schema.org/draft-07/schema#
__module__: zuper_json.zeneric2
__qualname__: test_more.<locals>.Entity0
definitions:
  X: {$id: 'http://invalid.json-schema.org/Entity0[X]/X#', $schema: 'http://json-schema.org/draft-07/schema#'}
description: 'Entity0[X](data0: ~X, parent: ''Optional[Entity0[X]]'' = None)'
properties:
  data0: {$ref: 'http://invalid.json-schema.org/Entity0[X]/X#'}
  parent: {$ref: 'http://invalid.json-schema.org/Entity0[X]#'}
required: [data0]
title: Entity0[X]
type: object    
    
    """)
    T = schema_to_type(schema, {}, {})
    print(T.__annotations__)


@known_failure
def test_more2():
    X = TypeVar('X')
    Y = TypeVar('Y')

    @dataclass
    class Entity11(Generic[X]):
        data0: X

        parent: "Optional[Entity11[X]]" = None

    type_to_schema(Entity11, {})

    EI = Entity11[int]

    assert_type_roundtrip(Entity11, {})
    assert_type_roundtrip(EI, {})

    @dataclass
    class Entity2(Generic[Y]):
        parent: Optional[Entity11[Y]] = None

    type_to_schema(Entity2, {})

    assert_type_roundtrip(Entity2, {})
    #
    E2I = Entity2[int]
    assert_type_roundtrip(E2I, {})

    x = E2I(parent=EI(data0=4))
    # print(json.dumps(type_to_schema(type(x), {}), indent=2))
    assert_object_roundtrip(x, {'Entity11': Entity11, 'Entity2': Entity2},
                            works_without_schema=False)


def test_more2b():
    X = TypeVar('X')
    Y = TypeVar('Y')

    @dataclass
    class Entity12(Generic[X]):
        data0: X

        parent: "Optional[Entity12[X]]" = None

    @dataclass
    class Entity13(Generic[Y]):
        parent: Optional[Entity12[Y]] = None

    EI = Entity12[int]
    # print(EI.__annotations__['parent'])
    E2I = Entity13[int]
    parent2 = E2I.__annotations__['parent']
    print(parent2)
    x = E2I(parent=EI(data0=4))
    # print(json.dumps(type_to_schema(type(x), {}), indent=2))
    # print(type(x).__name__)
    assert_object_roundtrip(x, {'Entity12': Entity12, 'Entity13': Entity13}, works_without_schema=False)


from typing import ClassVar, Type


def test_isClassVar():
    X = TypeVar('X')

    A = ClassVar[Type[X]]
    assert is_ClassVar(A)
    assert get_ClassVar_arg(A) == Type[X]


def test_isType():
    X = TypeVar('X')

    A = Type[X]
    # print(type(A))
    # print(A.__dict__)
    assert is_Type(A)
    assert get_Type_arg(A) == X


def test_more3_simpler():
    X = TypeVar('X')

    @dataclass
    class MyClass(Generic[X]):
        XT: ClassVar[Type[X]]

    assert_type_roundtrip(MyClass, {})
    #
    # # type_to_schema(MyClass, {})

    C = MyClass[int, str]
    assert_type_roundtrip(C, {})


def test_more3():
    # class Base:
    #     pass
    X = TypeVar('X')
    Y = TypeVar('Y')

    @dataclass
    class MyClass(Generic[X, Y]):
        a: X
        XT: ClassVar[Type[X]]
        YT: ClassVar[Type[Y]]

        def method(self, x: X) -> Y:
            return type(self).YT(x)

    assert_type_roundtrip(MyClass, {})

    # type_to_schema(MyClass, {})

    C = MyClass[int, str]
    assert_type_roundtrip(C, {})
    # print(f'Annotations for C: {C.__annotations__}')
    assert_equal(C.__annotations__['XT'], ClassVar[Type[int]])
    assert_equal(C.XT, int)
    assert_equal(C.__annotations__['YT'], ClassVar[Type[str]])
    assert_equal(C.YT, str)

    schema = type_to_schema(C, {})
    # print(json.dumps(schema, indent=2))
    schema_to_type(schema, {}, {})
    # print(f'Annotations for C2: {C2.__annotations__}')
    e = C(2)
    r = e.method(1)
    assert r == "1"

    assert_object_roundtrip(e, {})


def test_entity():
    X = TypeVar('X')

    @my_dataclass
    class SecurityModel2:
        # guid: Any
        owner: str
        arbiter: str

    @my_dataclass
    class Entity2(Generic[X]):
        data0: X
        guid: str

        security_model: SecurityModel2
        parent: "Optional[Entity2[X]]" = None
        forked: "Optional[Entity2[X]]" = None



    T = type_to_schema(Entity2, {}, {})
    C = schema_to_type(T, {}, {})
    print(yaml.dump(T))
    print(C.__annotations__)

    # resolve_types(Entity2, locals())
    # assert_type_roundtrip(Entity2, locals())
    assert_type_roundtrip(Entity2, {})
    Entity2_int = Entity2[int]
    assert_type_roundtrip(Entity2_int, {})

    # assert_object_roundtrip(x, {})


def test_entity0():
    # language=yaml
    schema = yaml.load("""
$id: http://invalid.json-schema.org/Entity2[X]#
$schema: http://json-schema.org/draft-07/schema#
definitions:
  X: {$id: 'http://invalid.json-schema.org/Entity2[X]/X#', $schema: 'http://json-schema.org/draft-07/schema#'}
description: 
properties:
  parent: {$ref: 'http://invalid.json-schema.org/Entity2[X]#'}
required: [data0, guid, security_model]
title: Entity2[X]
type: object    
    """)
    C = schema_to_type(schema, {}, {})
    print(C.__annotations__)

    assert not is_forward_ref(C.__annotations__['parent'].__args__[0])


def test_classvar1():
    @dataclass
    class C:
        v: ClassVar[int] = 1

    assert_type_roundtrip(C, {})
    # schema = type_to_schema(C, {})
    # C2: C = schema_to_type(schema, {}, {})
    #
    # assert_equal(C.v, C2.v)


def test_classvar2():
    X = TypeVar('X', bound=int)

    @dataclass
    class CG(Generic[X]):
        v: ClassVar[X] = 1

    C = CG[int]
    schema = type_to_schema(C, {})
    C2: C = schema_to_type(schema, {}, {})

    assert_type_roundtrip(C, {})
    assert_type_roundtrip(CG, {})

    assert_equal(C.v, C2.v)


@raises(TypeError)
def test_check_bound():
    @dataclass
    class Animal:
        pass

    X = TypeVar('X', bound=Animal)

    @dataclass
    class CG(Generic[X]):
        a: X

    CG[int](a=2)

    # assert_type_roundtrip(CG, {})
    # assert_type_roundtrip(CG[int], {})
    #


if enable_type_checking:
    @raises(ValueError, TypeError)  # typerror in 3.6
    def test_check_value():
        @dataclass
        class CG(Generic[()]):
            a: int

        CG[int](a="a")


def test_signing():
    X = TypeVar('X')

    @dataclass
    class PublicKey1:
        key: bytes

    @dataclass
    class Signed1(Generic[X]):
        key: PublicKey1
        signature_data: bytes
        data: X

    s = Signed1[str](key=PublicKey1(key=b''), signature_data=b'xxx', data="message")

    assert_type_roundtrip(Signed1[str], {})
    assert_object_roundtrip(s, {})


def test_derived1():
    X = TypeVar('X')

    @dataclass
    class Signed3(Generic[X]):
        data: X

    S = Signed3[int]

    logger.info(dataclasses.fields(S))

    class Y(S):
        """hello"""
        pass

    assert S.__doc__ in ['Signed3[int](data:int)', 'Signed3[int](data: int)']
    assert_equal(Y.__doc__, """hello""")
    assert_type_roundtrip(Y, {})


def test_derived2_no_doc():
    X = TypeVar('X')

    @dataclass
    class Signed3(Generic[X]):
        data: X

    S = Signed3[int]

    class Z(S):
        pass

    assert_type_roundtrip(Z, {})


def test_derived2_subst():
    X = TypeVar('X')

    # print(dir(Generic))
    # print(dir(typing.GenericMeta))
    # print(Generic.__getitem__)
    @dataclass
    class Signed3(Generic[X]):
        data: X
        parent: Optional['Signed3[X]'] = None

    _ = Signed3[int]
    # resolve_types(Signed3, locals())

    S = Signed3[int]

    pprint(**S.__annotations__)
    assert 'X' not in str(S.__annotations__), S.__annotations__

    # assert_type_roundtrip(S, {})
    @dataclass
    class Y(S):
        pass

    pprint(**Y.__annotations__)

    schema = type_to_schema(Y, {}, {})
    print(yaml.dump(schema))
    TY = schema_to_type(schema, {}, {})

    pprint('annotations', **TY.__annotations__)
    P = TY.__annotations__['parent']
    assert not is_forward_ref(P)

    # raise Exception()
    # raise Exception()
    assert_type_roundtrip(Y, {})


def test_derived3_subst():
    X = TypeVar('X')

    @dataclass
    class Signed3(Generic[X]):
        data: Optional[X]

    S = Signed3[int]
    x = S(data=2)
    assert_object_roundtrip(x, {})


if __name__ == '__main__':
    test_entity()
