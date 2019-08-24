from zuper_typing.annotations_tricks import name_for_type_like
from .constants import INTERSECTION_ATT, PYTHON_36

#
# def Intersection_item(cls, params):
#     from .annotations_tricks import name_for_type_like
#     from .zeneric2 import as_tuple
#
#     types = as_tuple(params)
#     name = f'Intersection[{",".join(name_for_type_like(_) for _ in types)}]'
#
#     annotations = {}
#     any_dataclass = any(is_dataclass(_) for _ in types)
#     for t in types:
#         a = getattr(t, ANNOTATIONS_ATT, {})
#         annotations.update(a)
#
#     res = {ANNOTATIONS_ATT: annotations, INTERSECTION_ATT: types}
#
#     for k in annotations:
#         for t in types:
#             if hasattr(t, k):
#                 res[k] = getattr(t, k)
#
#     C = type(name, params, res)
#     if any_dataclass:
#         C = dataclass(C)
#
#     return C


if PYTHON_36:  # pragma: no cover

    class IntersectionMeta(type):
        def __getitem__(self, params):
            return make_Intersection(params)

    class Intersection(metaclass=IntersectionMeta):
        pass


else:

    class Intersection:
        @classmethod
        def __class_getitem__(cls, params):
            # return Intersection_item(cls, params)
            return make_Intersection(params)


class IntersectionCache:
    use_cache = True
    make_intersection_cache = {}


def make_Intersection(ts: tuple) -> type:
    if IntersectionCache.use_cache:
        if ts in IntersectionCache.make_intersection_cache:
            return IntersectionCache.make_intersection_cache[ts]

    class IntersectionBase(type):
        def __eq__(self, other):
            if is_Intersection(other):
                t1 = get_Intersection_args(self)
                t2 = get_Intersection_args(other)
                return set(t1) == set(t2)
            return False

        def __hash__(cls):  # pragma: no cover
            return 1  # XXX
            # logger.debug(f'here ___eq__ {self} {other} {issubclass(other, CustomList)} = {res}')

    attrs = {INTERSECTION_ATT: ts}

    # name = get_List_name(V)
    name = "Intersection[%s]" % ",".join(name_for_type_like(_) for _ in ts)

    res = IntersectionBase(name, (), attrs)

    IntersectionCache.make_intersection_cache[ts] = res
    return res


def is_Intersection(T):
    return hasattr(T, INTERSECTION_ATT)


def get_Intersection_args(T):
    assert is_Intersection(T)
    return getattr(T, INTERSECTION_ATT)
