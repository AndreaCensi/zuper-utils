from typing import NewType, Dict, Any

JSONSchema = NewType('JSONSchema', dict)
GlobalsDict = Dict[str, Any]
ProcessingDict = Dict[str, Any]
EncounteredDict = Dict[str, str]
_SpecialForm = Any

SCHEMA_ID = "http://json-schema.org/draft-07/schema#"
SCHEMA_ATT = '$schema'

INTERSECTION_ATT = '__intersection__'

ID_ATT = '$id'
REF_ATT = '$ref'

X_CLASSVARS = 'classvars'
X_CLASSATTS = 'clasatts'

JSC_REQUIRED = 'required'
JSC_TYPE = 'type'
JSC_TITLE = 'title'
JSC_NUMBER = 'number'
JSC_INTEGER = 'integer'
JSC_OBJECT = 'object'
JSC_ADDITIONAL_PROPERTIES = 'additionalProperties'
JSC_DESCRIPTION = 'description'
JSC_STRING = 'string'
JSC_BOOL = 'boolean'
JSC_PROPERTIES = 'properties'
JSC_DEFINITIONS = 'definitions'
Z_ATT_LSIZE = 'lsize'
Z_ATT_TSIZE = 'tsize'

GENERIC_ATT = '__generic__'
BINDINGS_ATT = '__binding__'

X_PYTHON_MODULE_ATT = '__module__'
ATT_PYTHON_NAME = '__qualname__'
SCHEMA_BYTES: JSONSchema = {JSC_TYPE: JSC_OBJECT,
                            SCHEMA_ATT: SCHEMA_ID,
                            JSC_PROPERTIES: {"base64": {JSC_TYPE: JSC_STRING}}}
NAME_ARG = '__name_arg__'  # XXX: repeated

import sys
PYTHON_36 = sys.version_info[1] == 6
PYTHON_37 = sys.version_info[1] == 7
