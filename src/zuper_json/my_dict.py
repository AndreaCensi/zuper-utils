from typing import ClassVar, Tuple


class CustomDict(dict):
    __dict_type__: ClassVar[Tuple[type, type]]

    def __setitem__(self, key, val):
        K, V = self.__dict_type__
        if not isinstance(key, K):
            msg = f'Invalid key; expected {K}, got {type(key)}'
            raise ValueError(msg)
        if not isinstance(val, V):
            msg = f'Invalid value; expected {V}, got {type(val)}'
            raise ValueError(msg)
        dict.__setitem__(self, key, val)


def make_dict(K, V) -> type:
    attrs = {'__dict_type__': (K, V)}

    from .annotations_tricks import name_for_type_like
    KN = name_for_type_like(K)
    VN = name_for_type_like(V)
    name = f'Dict[{KN},{VN}]'

    res = type(name, (CustomDict,), attrs)
    return res
