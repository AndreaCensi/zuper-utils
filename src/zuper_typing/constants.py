import sys

PYTHON_36 = sys.version_info[1] == 6
PYTHON_37 = sys.version_info[1] == 7
NAME_ARG = '__name_arg__'  # XXX: repeated
ANNOTATIONS_ATT = '__annotations__'
DEPENDS_ATT = '__depends__'
INTERSECTION_ATT = '__intersection__'
GENERIC_ATT2 = '__generic2__'
BINDINGS_ATT = '__binding__'
enable_type_checking = True
cache_enabled = True  # XXX


class MakeTypeCache:
    cache = {}


from .logging import logger
import os

circle_job = os.environ.get('CIRCLE_JOB', None)
logger.info(f'Circle JOB: {circle_job!r}')

if circle_job == 'test-3.7-no-cache':
    cache_enabled = False
    logger.warning('Disabling cache (zuper_typing:cache_enabled) due to circle_job.')
