import sys
from dataclasses import dataclass, is_dataclass

INTERSECTION_ATT = '__intersection__'


def Intersection_item(cls, params):
    from zuper_json.zeneric2 import as_tuple
    types = as_tuple(params)
    name = f'Intersection[{",".join(_.__name__ for _ in types)}]'

    annotations = {}
    any_dataclass = any(is_dataclass(_) for _ in types)
    for t in types:
        a = getattr(t, '__annotations__', {})
        annotations.update(a)

    # def my_eq(self, other):
    #     return getattr(self, INTERSECTION_ATT) == getattr(other, INTERSECTION_ATT, ())

    res = {
        '__annotations__': annotations,
        # '__eq__': my_eq,
        INTERSECTION_ATT: types
    }

    C = type(name, params, res)
    if any_dataclass:
        C = dataclass(C)

    return C

PYTHON_36 = sys.version_info[1] == 6

if PYTHON_36:
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
