from typing import ClassVar, Tuple, Any

from .annotations_tricks import is_Dict, get_Set_name_V


class CustomDict(dict):
    __dict_type__: ClassVar[Tuple[type, type]]

    def __setitem__(self, key, val):
        K, V = self.__dict_type__

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


def make_dict(K, V) -> type:
    attrs = {'__dict_type__': (K, V)}
    from .annotations_tricks import get_Dict_name_K_V
    name = get_Dict_name_K_V(K, V)

    res = type(name, (CustomDict,), attrs)
    return res


def is_Dict_or_CustomDict(x):
    from .annotations_tricks import is_Dict
    return is_Dict(x) or (isinstance(x, type) and issubclass(x, CustomDict))


def get_Dict_or_CustomDict_Key_Value(x):
    assert is_Dict_or_CustomDict(x)
    if is_Dict(x):
        return x.__args__
    else:
        return x.__dict_type__


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


def is_set_or_CustomSet(x):
    from .annotations_tricks import is_Set
    return is_Set(x) or (isinstance(x, type) and issubclass(x, CustomSet))


def get_set_Set_or_CustomSet_Value(x):
    from .annotations_tricks import is_Set, get_Set_arg
    if x is set:
        return Any

    if is_Set(x):
        return get_Set_arg(x)

    if isinstance(x, type) and issubclass(x, CustomSet):
        return x.__set_type__

    assert False, x
