from typing import Any, ClassVar, Tuple

from .annotations_tricks import (get_Dict_args, get_Dict_name_K_V, get_Set_name_V, is_Dict, name_for_type_like, is_List,
                                 get_List_arg, is_Set, get_Set_arg)


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




def is_CustomDict(x):
    return isinstance(x, type) and issubclass(x, CustomDict)


def is_Dict_or_CustomDict(x):
    from zuper_typing.annotations_tricks import is_Dict
    return x is dict or is_Dict(x) or is_CustomDict(x)


def get_CustomDict_args(x):
    assert is_CustomDict(x)
    return x.__dict_type__


def get_CustomSet_arg(x):
    assert is_CustomSet(x)
    return x.__set_type__

def get_CustomList_arg(x):
    assert is_CustomList(x)
    return x.__list_type__


def get_Dict_or_CustomDict_Key_Value(x):
    assert is_Dict_or_CustomDict(x), x
    # if x is typing.Dict:
    #     return Any, Any
    if is_Dict(x):
        k, v = get_Dict_args(x)

        return k, v
    elif is_CustomDict(x):
        return get_CustomDict_args(x)
    elif x is dict:
        return Any, Any
    else:
        assert False, x


def get_Dict_or_CustomDict_name(T):
    assert is_Dict_or_CustomDict(T)
    K, V = get_Dict_or_CustomDict_Key_Value(T)
    return get_Dict_name_K_V(K, V)


class CustomSet(set):
    __set_type__: ClassVar[type]

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(sorted(self)))
            return h


class CustomList(list):
    __list_type__: ClassVar[type]

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(self))
            return h


def make_set(V) -> type:
    from .logging import logger
    class MyType(type):
        def __eq__(self, other):
            V = getattr(self, '__set_type__')
            if is_Set(other):
                return V == get_Set_arg(other)
            res = isinstance(other, type) and issubclass(other, CustomSet) and other.__set_type__ == V
            return res

        def __hash__(cls):
            return 1  # XXX

            # logger.debug(f'here ___eq__ {self} {other} {issubclass(other, CustomList)} = {res}')
    attrs = {'__set_type__': V}
    name = get_Set_name_V(V)
    res = MyType(name, (CustomSet,), attrs)
    return res


def make_list(V) -> type:
    from .logging import logger
    class MyType(type):
        def __eq__(self, other):
            V = getattr(self, '__list_type__')
            if is_List(other):
                return V == get_List_arg(other)
            res = isinstance(other, type) and issubclass(other, CustomList) and other.__list_type__ == V
            return res

        def __hash__(cls):
            return 1  # XXX
            # logger.debug(f'here ___eq__ {self} {other} {issubclass(other, CustomList)} = {res}')
    attrs = {'__list_type__': V}

    # name = get_List_name(V)
    name = 'List[%s]' % name_for_type_like(V)

    res = MyType(name, (CustomList,), attrs)
    return res

# from . import logger
def make_dict(K, V) -> type:
    class MyType(type):
        def __eq__(self, other):
            K, V = getattr(self, '__dict_type__')
            if is_Dict(other):
                K1, V1 = get_Dict_args(other)
                return K == K1 and V == V1
            res = isinstance(other, type) and issubclass(other, CustomDict) and other.__dict_type__ == (K, V)
            return res
        def __hash__(cls):
            return 1 # XXX

    if isinstance(V, str):
        msg = f'Trying to make dict with K = {K!r} and V = {V!r}; I need types, not strings.'
        raise ValueError(msg)
    # warnings.warn('Creating dict', stacklevel=2)
    attrs = {'__dict_type__': (K, V)}
    from zuper_typing.annotations_tricks import get_Dict_name_K_V
    name = get_Dict_name_K_V(K, V)

    res = MyType(name, (CustomDict,), attrs)
    return res

def is_list_or_List(x):
    from zuper_typing.annotations_tricks import is_List
    return is_List(x) or (isinstance(x, type) and issubclass(x, list))


def is_list_or_List_or_CustomList(x):
    from zuper_typing.annotations_tricks import is_List
    return (x is list) or is_List(x) or is_CustomList(x)


def get_list_or_List_or_CustomList_arg(x):
    from zuper_typing.annotations_tricks import is_List, get_List_arg
    if x is list:
        return Any
    if is_List(x):
        return get_List_arg(x)

    if isinstance(x, type) and issubclass(x, CustomList):
        return x.__list_type__

    assert False, x


def get_list_List_Value(x):
    from zuper_typing.annotations_tricks import is_List, get_List_arg
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


def is_CustomList(x):
    return isinstance(x, type) and issubclass(x, CustomList)


def is_set_or_CustomSet(x):
    from zuper_typing.annotations_tricks import is_Set
    return (x is set) or is_Set(x) or is_CustomSet(x)


def get_set_Set_or_CustomSet_Value(x):
    from zuper_typing.annotations_tricks import is_Set, get_Set_arg
    if x is set:
        return Any

    if is_Set(x):
        return get_Set_arg(x)

    if isinstance(x, type) and issubclass(x, CustomSet):
        return x.__set_type__

    assert False, x
