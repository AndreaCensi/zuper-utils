from dataclasses import dataclass, is_dataclass

INTERSECTION_ATT = '__intersection__'


class Intersection:
    @classmethod
    def __class_getitem__(cls, params):
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


def is_Intersection(T):
    return hasattr(T, INTERSECTION_ATT)


def get_Intersection_args(T):
    assert is_Intersection(T)
    return getattr(T, INTERSECTION_ATT)
