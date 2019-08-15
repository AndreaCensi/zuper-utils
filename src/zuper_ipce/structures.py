from typing import Generic, TypeVar

from zuper_typing.monkey_patching_typing import my_dataclass


class CannotFindSchemaReference(Exception):
    pass


class CannotResolveTypeVar(Exception):
    pass


KK = TypeVar("KK")
VV = TypeVar("VV")


@my_dataclass
class FakeValues(Generic[KK, VV]):
    real_key: KK
    value: VV
