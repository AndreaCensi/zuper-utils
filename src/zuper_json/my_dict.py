from typing import ClassVar, Tuple, Any, TypeVar

from .annotations_tricks import is_Dict, get_Set_name_V


class CustomDict(dict):
    __dict_type__: ClassVar[Tuple[type, type]]

    def __setitem__(self, key, val):
        K, V = self.__dict_type__

        if False:
            if not isinstance(key, K):
                msg = f'Invalid key; expected {K}, got {type(key)}'
                raise ValueError(msg)
            # XXX: this should be for many more cases
            if isinstance(V, type) and not isinstance(val, V):
                msg = f'Invalid value; expected {V}, got {type(val)}'
                raise ValueError(msg)
        dict.__setitem__(self, key, val)

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(sorted(self.items())))
            return h


# from . import logger
def make_dict(K, V) -> type:
    if isinstance(V, str):
        msg = f'Trying to make dict with K = {K!r} and V = {V!r}; I need types, not strings.'
        raise ValueError(msg)
    # warnings.warn('Creating dict', stacklevel=2)
    attrs = {'__dict_type__': (K, V)}
    from .annotations_tricks import get_Dict_name_K_V
    name = get_Dict_name_K_V(K, V)

    res = type(name, (CustomDict,), attrs)
    return res


def is_CustomDict(x):
    return isinstance(x, type) and issubclass(x, CustomDict)


def is_Dict_or_CustomDict(x):
    from .annotations_tricks import is_Dict
    return x is dict or is_Dict(x) or is_CustomDict(x)


def get_Dict_or_CustomDict_Key_Value(x):
    assert is_Dict_or_CustomDict(x), x
    if is_Dict(x):
        k, v = x.__args__
        if isinstance(k, TypeVar):
            k = Any
        if isinstance(v, TypeVar):
            v = Any
        return k, v

    elif is_CustomDict(x):
        return x.__dict_type__
    elif x is dict:
        return Any, Any
    else:
        assert False, x


class CustomSet(set):
    __set_type__: ClassVar[type]

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(sorted(self)))
            return h


def make_set(V) -> type:
    attrs = {'__set_type__': V}
    name = get_Set_name_V(V)
    res = type(name, (CustomSet,), attrs)
    return res


def is_list_or_List(x):
    from .annotations_tricks import is_List
    return is_List(x) or (isinstance(x, type) and issubclass(x, list))


def get_list_List_Value(x):
    from .annotations_tricks import is_List, get_List_arg
    if x is list:
        return Any

    if is_List(x):
        return get_List_arg(x)
    #
    # if isinstance(x, type) and issubclass(x, CustomSet):
    #     return x.__set_type__

    assert False, x


def is_CustomSet(x):
    return isinstance(x, type) and issubclass(x, CustomSet)


def is_set_or_CustomSet(x):
    from .annotations_tricks import is_Set
    return (x is set) or is_Set(x) or is_CustomSet(x)


def get_set_Set_or_CustomSet_Value(x):
    from .annotations_tricks import is_Set, get_Set_arg
    if x is set:
        return Any

    if is_Set(x):
        return get_Set_arg(x)

    if isinstance(x, type) and issubclass(x, CustomSet):
        return x.__set_type__

    assert False, x
