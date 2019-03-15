from typing import ClassVar, Tuple

from zuper_json.annotations_tricks import is_Dict


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
    from zuper_json.annotations_tricks import get_Dict_name_K_V
    name = get_Dict_name_K_V(K, V)

    res = type(name, (CustomDict,), attrs)
    return res


def is_Dict_or_CustomDict(x):
    from zuper_json.annotations_tricks import is_Dict
    return is_Dict(x) or (isinstance(x, type) and issubclass(x, CustomDict))

def get_Dict_or_CustomDict_Key_Value(x):
    assert is_Dict_or_CustomDict(x)
    if is_Dict(x):
        return x.__args__
    else:
        return x.__dict_type__
