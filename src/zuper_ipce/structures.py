from typing import TypeVar, Generic, Optional

from zuper_ipce.constants import JSONSchema
from zuper_typing.monkey_patching_typing import my_dataclass


class CannotFindSchemaReference(Exception):
    pass


class CannotResolveTypeVar(Exception):
    pass


KK = TypeVar('KK')
VV = TypeVar('VV')


@my_dataclass
class FakeValues(Generic[KK, VV]):
    real_key: KK
    value: VV


class Result:
    schema: JSONSchema
    optional: Optional[bool] = False

    def __init__(self, schema: JSONSchema, optional: bool = None):
        self.schema = schema
        self.optional = optional
