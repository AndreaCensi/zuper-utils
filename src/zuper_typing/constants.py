import sys

PYTHON_36 = sys.version_info[1] == 6
PYTHON_37 = sys.version_info[1] == 7
NAME_ARG = "__name_arg__"  # XXX: repeated
ANNOTATIONS_ATT = "__annotations__"
DEPENDS_ATT = "__depends__"
INTERSECTION_ATT = "__intersection__"
GENERIC_ATT2 = "__generic2__"
BINDINGS_ATT = "__binding__"

enable_type_checking = True
cache_enabled = True
monkey_patch_Generic = False
monkey_patch_dataclass = False


class MakeTypeCache:
    cache = {}


from .logging import logger
import os

#
# vname = "ZUPER_TYPING_PATCH"
# if vname in os.environ: # pragma: no cover
#     logger.info(f"Enabling monkey_patch_Generic because of {vname}")
#     monkey_patch_Generic = True
# else:  # pragma: no cover
#     logger.info(f"Disabling monkey_patch_Generic because of {vname}")
#     monkey_patch_Generic = False

circle_job = os.environ.get("CIRCLE_JOB", None)
# logger.info(f"Circle JOB: {circle_job!r}")


if circle_job == "test-3.7-no-cache":  # pragma: no cover
    cache_enabled = False
    logger.warning("Disabling cache (zuper_typing:cache_enabled) due to circle_job.")
