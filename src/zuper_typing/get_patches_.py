from dataclasses import is_dataclass, dataclass
from typing import List, Tuple, Union, Optional, cast

from zuper_ipce.conv_ipce_from_object import get_fields_values
from zuper_typing.aliases import TypeLike
from zuper_typing.annotations_tricks import is_TypeLike

from zuper_typing.exceptions import ZValueError


@dataclass
class Patch:
    __print_order = ["prefix_str", "value1", "value2"]
    prefix: Tuple[Union[str, int], ...]
    value1: object
    value2: Optional[object]
    prefix_str: Optional[str] = None

    def __post_init__(self):
        self.prefix_str = "/".join(map(str, self.prefix))


def assert_equivalent_objects(ob1: object, ob2: object):
    if is_TypeLike(ob1):
        from zuper_ipce_tests.test_utils import assert_equivalent_types

        ob1 = cast(TypeLike, ob1)
        ob2 = cast(TypeLike, ob2)
        assert_equivalent_types(ob1, ob2)
    else:
        patches = get_patches(ob1, ob2)
        if patches:
            msg = "The objects are not equivalent"
            raise ZValueError(msg, ob1=ob1, ob2=ob2, patches=patches)


def get_patches(a: object, b: object) -> List[Patch]:
    patches = list(patch(a, b, ()))
    return patches


def is_dataclass_instance(x: object) -> bool:
    return not isinstance(x, type) and is_dataclass(x)


def patch(o1, o2, prefix: Tuple[Union[str, int], ...]):
    if o1 == o2:
        return
    if is_dataclass_instance(o1) and is_dataclass_instance(o2):

        fields1 = get_fields_values(o1)
        fields2 = get_fields_values(o2)
        if list(fields1) != list(fields2):
            yield Patch(prefix, o1, o2)
        for k in fields1:
            v1 = fields1[k]
            v2 = fields2[k]
            yield from patch(v1, v2, prefix + (k,))
    elif isinstance(o1, dict) and isinstance(o2, dict):
        for k, v in o1.items():
            if not k in o2:
                yield Patch(prefix + (k,), v, None)
            else:
                yield from patch(v, o2[k], prefix + (k,))
    elif isinstance(o1, list) and isinstance(o2, list):
        for i, v in enumerate(o1):
            if i >= len(o2) - 1:
                yield Patch(prefix + (i,), v, None)
            else:
                yield from patch(o1[i], o2[i], prefix + (i,))
    else:
        if o1 != o2:
            yield Patch(prefix, o1, o2)


#
#
# def patch(o1, o2, prefix: Tuple[Union[str, int], ...]) -> Iterator[Patch]:
#     if o1 == o2:
#         return
#     if isinstance(o1, dict) and isinstance(o2, dict):
#         for k, v in o1.items():
#             if not k in o2:
#                 yield Patch(prefix + (k,), v, None)
#             else:
#                 yield from patch(v, o2[k], prefix + (k,))
#     elif isinstance(o1, list) and isinstance(o2, list):
#         for i, v in enumerate(o1):
#             if i >= len(o2) - 1:
#                 yield Patch(prefix + (i,), v, None)
#             else:
#                 yield from patch(o1[i], o2[i], prefix + (i,))
#     else:
#         if o1 != o2:
#             yield Patch(prefix, o1, o2)
