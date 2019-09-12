from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import cast, Dict, NewType, Tuple

from zuper_typing.my_dict import make_dict

JSONSchema = NewType("JSONSchema", dict)
GlobalsDict = Dict[str, object]
ProcessingDict = Dict[str, str]
EncounteredDict = Dict[str, object]
# _SpecialForm = Any

SCHEMA_ID = "http://json-schema.org/draft-07/schema#"
SCHEMA_ATT = "$schema"
HINTS_ATT = "$hints"
ANY_OF = "anyOf"
ALL_OF = "allOf"
ID_ATT = "$id"
REF_ATT = "$ref"

X_CLASSVARS = "classvars"
X_CLASSATTS = "classatts"
X_ORDER = "order"
JSC_FORMAT = "format"
JSC_REQUIRED = "required"
JSC_TYPE = "type"
JSC_ITEMS = "items"
JSC_DEFAULT = "default"
JSC_TITLE = "title"
JSC_NUMBER = "number"
JSC_INTEGER = "integer"
JSC_ARRAY = "array"
JSC_OBJECT = "object"
JSC_ADDITIONAL_PROPERTIES = "additionalProperties"
JSC_PROPERTY_NAMES = "propertyNames"
JSC_DESCRIPTION = "description"
JSC_STRING = "string"
JSC_NULL = "null"
JSC_BOOL = "boolean"
JSC_PROPERTIES = "properties"
JSC_DEFINITIONS = "definitions"
JSC_ALLOF = "allOf"
JSC_ANYOF = "anyOf"

Z_ATT_LSIZE = "lsize"
Z_ATT_TSIZE = "tsize"

X_PYTHON_MODULE_ATT = "__module__"
ATT_PYTHON_NAME = "__qualname__"

JSC_TITLE_NUMPY = "numpy"
JSC_TITLE_SLICE = "slice"
JSC_TITLE_BYTES = "bytes"
JSC_TITLE_DECIMAL = "decimal"
JSC_TITLE_FLOAT = "float"
JSC_TITLE_DATETIME = "datetime"
JSC_TITLE_CALLABLE = "Callable"
JSC_TITLE_TYPE = "type"
JSC_TITLE_CID = "cid"
# JSC_TITLE_TUPLE = 'Tuple'
# JSC_TITLE_LIST = 'List'
JSC_FORMAT_CID = "cid"

SCHEMA_BYTES = cast(
    JSONSchema,
    {JSC_TYPE: JSC_STRING, JSC_TITLE: JSC_TITLE_BYTES, SCHEMA_ATT: SCHEMA_ID},
)
SCHEMA_CID = cast(
    JSONSchema,
    {
        JSC_TYPE: JSC_STRING,
        JSC_TITLE: JSC_TITLE_CID,
        JSC_FORMAT: JSC_FORMAT_CID,
        SCHEMA_ATT: SCHEMA_ID,
    },
)

IPCE_SCALARS = (int, str, float, bytes, datetime, bool, Decimal, type(None))


# check_types = False

CALLABLE_ORDERING = "ordering"
CALLABLE_RETURN = "return"


@dataclass
class IEDO:
    use_remembered_classes: bool
    remember_deserialized_classes: bool


ModuleName = QualName = str
n = 0


@dataclass
class IEDS:
    global_symbols: Dict[str, type]
    encountered: Dict
    klasses: Dict[Tuple[ModuleName, QualName], type] = None

    def __post_init__(self):
        pass
        if self.klasses is None:
            self.klasses = make_dict(str, type)()
        #     from .logging import logger
        #     logger.info('IEDS new')
        #     global n
        #     n += 1
        #     if n == 5:
        #         raise NotImplementedError()


@dataclass
class IESO:
    use_ipce_from_typelike_cache: bool = True
    with_schema: bool = True


IPCE_PASS_THROUGH = (NotImplementedError, KeyboardInterrupt, MemoryError)
