import sys

PYTHON_36 = sys.version_info[1] == 6
PYTHON_37 = sys.version_info[1] == 7
NAME_ARG = '__name_arg__'  # XXX: repeated
ANNOTATIONS_ATT = '__annotations__'
DEPENDS_ATT = '__depends__'
INTERSECTION_ATT = '__intersection__'
GENERIC_ATT2 = '__generic2__'
BINDINGS_ATT = '__binding__'
enable_type_checking = False
cache_enabled = True # XXX


class MakeTypeCache:
    cache = {}
