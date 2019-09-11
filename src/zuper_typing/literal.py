from typing import Tuple, Type

from typing_extensions import Literal

from zuper_typing.aliases import TypeLike


def make_Literal(*values: object) -> TypeLike:
    return Literal[values]


def is_Literal(x: TypeLike) -> bool:
    return "Literal[" in str(x)


def get_Literal_args(x: TypeLike) -> Tuple[object, ...]:
    assert is_Literal(x)

    return getattr(x, "__args__")
