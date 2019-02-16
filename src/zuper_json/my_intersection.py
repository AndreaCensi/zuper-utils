from zuper_json.constants import INTERSECTION_ATT
from .constants import PYTHON_36
from dataclasses import dataclass, is_dataclass


def Intersection_item(cls, params):
    from zuper_json.zeneric2 import as_tuple
    types = as_tuple(params)
    name = f'Intersection[{",".join(_.__name__ for _ in types)}]'

    annotations = {}
    any_dataclass = any(is_dataclass(_) for _ in types)
    for t in types:
        a = getattr(t, '__annotations__', {})
        annotations.update(a)

    res = {
        '__annotations__': annotations,
        INTERSECTION_ATT: types
    }

    C = type(name, params, res)
    if any_dataclass:
        C = dataclass(C)

    return C


if PYTHON_36: # pragma: no cover
    class IntersectionMeta(type):

        def __getitem__(self, params):
            return Intersection_item(self, params)

    class Intersection(metaclass=IntersectionMeta):
        pass
else:
    class Intersection:
        @classmethod
        def __class_getitem__(cls, params):
           return Intersection_item(cls, params)


def is_Intersection(T):
    return hasattr(T, INTERSECTION_ATT)


def get_Intersection_args(T):
    assert is_Intersection(T)
    return getattr(T, INTERSECTION_ATT)
