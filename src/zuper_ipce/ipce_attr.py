from typing import Any

# IPCE_REPR_ATTR = '__ipce_repr__'
from zuper_commons.text.text_sidebyside import side_by_side
from zuper_typing.annotations_tricks import is_Union

__all__ = ['has_ipce_repr_attr', 'get_ipce_repr_attr', 'set_ipce_repr_attr']


class SchemaCache:
    key2schema = {}


def make_key(x):
    return (id(type(x)), getattr(x, '__qualname__', 'no qual'), getattr(x, '__name__', 'no name'), id(x))


def has_ipce_repr_attr(x: Any):
    k = make_key(x)
    return k in SchemaCache.key2schema


def get_ipce_repr_attr(x: Any):
    k = make_key(x)
    res = SchemaCache.key2schema[k]
    # logger.debug(f'Found schema cache for {k}')
    return res
    #


def can_have_ipce_repr_attr(x):
    return not is_Union(x)
    return True


import yaml


def set_ipce_repr_attr(x: object, a):
    k = make_key(x)
    if has_ipce_repr_attr(x):
        prev = SchemaCache.key2schema[k]
        if prev != a:
            msg = f'Double setting of schema cache for {x}:\n'
            msg += side_by_side([yaml.dump(prev), ' ', yaml.dump(a)])
            raise ValueError(msg)

    SchemaCache.key2schema[k] = a
    # logger.debug(f'Setting schema cache for {k}')
    return
