from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Tuple

from zuper_typing.exceptions import ZValueError
from .constants import JSONSchema, REF_ATT, SCHEMA_ATT, SCHEMA_ID
from .ipce_attr import make_key
from .ipce_spec import assert_canonical_ipce


def assert_canonical_schema(x: JSONSchema):
    assert isinstance(x, dict)
    if SCHEMA_ATT in x:
        assert x[SCHEMA_ATT] in [SCHEMA_ID]
    elif REF_ATT in x:
        pass
    else:
        msg = f"No {SCHEMA_ATT} or {REF_ATT}"
        raise ZValueError(msg, x=x)

    assert_canonical_ipce(x)

    # json.dumps(x) # try no bytes


@dataclass
class TRE:
    schema: JSONSchema
    used: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            assert_canonical_schema(self.schema)
        except ValueError as e:  # pragma: no cover
            msg = f"Invalid schema"
            raise ZValueError(msg, schema=self.schema) from e


class IPCETypelikeCache:
    c: Dict[Tuple, Dict[Tuple, JSONSchema]] = defaultdict(dict)


# def get_cached():
#     return {k[1]: [x for x, _ in v.items()] for k, v in IPCETypelikeCache.c.items()}


def get_ipce_from_typelike_cache(T, context: Dict[str, str]) -> TRE:
    k = make_key(T)
    if k not in IPCETypelikeCache.c:
        raise KeyError()
    items = list(IPCETypelikeCache.c[k].items())
    # actually first look for the ones with more context
    items.sort(key=lambda x: len(x[1]), reverse=True)
    for context0, schema in items:
        if compatible(context0, context):
            # if context0:
            # logger.debug(f'Returning cached {T} with context {context0}')
            return TRE(schema, dict(context0))
    raise KeyError()


def compatible(c0: Tuple[Tuple[str, str]], context: Dict[str, str]) -> bool:
    for k, v in c0:
        if k not in context or context[k] != v:
            return False
    return True


def set_ipce_from_typelike_cache(T, context: Dict[str, str], schema: JSONSchema):
    k = make_key(T)
    ci = tuple(sorted(context.items()))
    IPCETypelikeCache.c[k][ci] = schema
