from dataclasses import dataclass, is_dataclass

from .constants import ANNOTATIONS_ATT, INTERSECTION_ATT, PYTHON_36


def Intersection_item(cls, params):
    from .annotations_tricks import name_for_type_like
    from .zeneric2 import as_tuple

    types = as_tuple(params)
    name = f'Intersection[{",".join(name_for_type_like(_) for _ in types)}]'

    annotations = {}
    any_dataclass = any(is_dataclass(_) for _ in types)
    for t in types:
        a = getattr(t, ANNOTATIONS_ATT, {})
        annotations.update(a)

    res = {ANNOTATIONS_ATT: annotations, INTERSECTION_ATT: types}

    for k in annotations:
        for t in types:
            if hasattr(t, k):
                res[k] = getattr(t, k)

    C = type(name, params, res)
    if any_dataclass:
        C = dataclass(C)

    return C


if PYTHON_36:  # pragma: no cover

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
