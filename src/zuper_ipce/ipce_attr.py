import warnings
from typing import Any

# IPCE_REPR_ATTR = '__ipce_repr__'

__all__ = ['has_ipce_repr_attr', 'get_ipce_repr_attr', 'set_ipce_repr_attr']


class SchemaCache:
    key2schema = {}


def make_key(x):
    return (str(x), getattr(x, '__qualname__', 'no qual'), getattr(x, '__name__', 'no name'), id(x))


def has_ipce_repr_attr(x: Any):
    k = make_key(x)
    return k in SchemaCache.key2schema
    #
    # if not can_have_ipce_repr_attr(x):
    #     return False
    #
    # if isinstance(x, type):
    #     return hasattr(x, IPCE_REPR_ATTR)
    #
    # if not is_dataclass(x):
    #     return False
    #
    # return IPCE_REPR_ATTR in x.__dict__


def get_ipce_repr_attr(x: Any):
    k = make_key(x)
    res = SchemaCache.key2schema[k]
    # logger.debug(f'Found schema cache for {k}')
    return res
    #
    # if isinstance(x, type):
    #     res = getattr(x, IPCE_REPR_ATTR)
    #     logger.debug(f'Using IPCE for {x} found\n{yaml.dump(res)} ')
    #     return res
    # if not is_dataclass(x):
    #     raise ValueError(type(x))
    #
    # res = x.__dict__[IPCE_REPR_ATTR]
    # return res


def can_have_ipce_repr_attr(x):
    # if x in (int, bool, str, float, bytes):
    #     return False
    return True
    # return False
    # if isinstance(x, type) and is_dataclass(x):
    #     from zuper_ipce.ipce import is_generic
    #     if is_generic(x):
    #         return False
    #
    #     if 'Intersection' in x.__name__:
    #         return False
    #
    #     return True
    # # from zuper_typing.my_dict import is_CustomDict, is_CustomList, is_CustomSet
    # # if is_CustomDict(x) or is_CustomSet(x) or is_CustomList(x):
    # #     return True
    # return False


def set_ipce_repr_attr(x: object, a):
    k = make_key(x)
    if has_ipce_repr_attr(x):
        warnings.warn(f'Double setting of  schema cache for {k}')

    SchemaCache.key2schema[k] = a
    # logger.debug(f'Setting schema cache for {k}')
    return
    #
    # if not can_have_ipce_repr_attr(x):
    #     logger.debug(f'Cannot set attr to {x} = {a}')
    #     # return
    # logger.debug(f'Setting IPCE for {x} to\n{yaml.dump(a)} ')
    #
    # if has_ipce_repr_attr(x):
    #     e = get_ipce_repr_attr(x)
    #     if a != e:
    #         d = {'x': x, 'current': e, 'updated': a}
    #         msg = f'Trying to set different hashes:' +
    #         logger.warning(msg)
    #         raise AssertionError(msg)
    # setattr(x, IPCE_REPR_ATTR, a)
    #
    # assert get_ipce_repr_attr(x) == a
