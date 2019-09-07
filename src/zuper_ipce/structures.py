from typing import TypeVar

from zuper_commons.types.exceptions import ZException
from zuper_typing.monkey_patching_typing import my_dataclass
from zuper_typing.zeneric2 import ZenericFix


class CannotFindSchemaReference(ZException):
    pass


class CannotResolveTypeVar(ZException):
    pass


KK = TypeVar("KK")
VV = TypeVar("VV")


@my_dataclass
class FakeValues(ZenericFix[KK, VV]):
    real_key: KK
    value: VV
