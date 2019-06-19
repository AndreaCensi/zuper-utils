from dataclasses import is_dataclass, dataclass
from typing import *

from zuper_commons.text import indent
from .annotations_tricks import is_Any, is_union, get_union_types, is_optional, get_optional_type, is_Tuple, is_TypeVar, \
    get_tuple_types
from .constants import BINDINGS_ATT
from .my_dict import is_Dict_or_CustomDict, get_Dict_or_CustomDict_Key_Value


@dataclass
class CanBeUsed:
    result: bool
    why: str
    matches: Dict[str, type]

    def __bool__(self):
        return self.result


def can_be_used_as2(T1, T2, matches: Dict[str, type]) -> CanBeUsed:
    # cop out for the easy cases

    if T1 is T2 or (T1 == T2):
        return CanBeUsed(True, 'equal', matches)

    if is_Any(T2):
        return CanBeUsed(True, 'Any', matches)
    if is_union(T1):
        # can_be_used(Union[A,B], C)
        # == can_be_used(A,C) and can_be_used(B,C)
        for t in get_union_types(T1):
            can = can_be_used_as2(t, T2, matches)
            if not can.result:
                msg = f'Cannot match {t}'
                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, '', matches)

    if is_union(T2):
        reasons = []
        for t in get_union_types(T2):
            can = can_be_used_as2(T1, t, matches)
            if can.result:
                return CanBeUsed(True, f'union match with {t} ', can.matches)
            reasons.append(f'- {t}: {can.why}')

        msg = f'Cannot use {T1} as any of {T2}:\n' + "\n".join(reasons)
        return CanBeUsed(False, msg, matches)

    if is_optional(T2):
        t = get_optional_type(T2)
        return can_be_used_as2(T1, t, matches)

    if is_Dict_or_CustomDict(T2):
        K2, V2 = get_Dict_or_CustomDict_Key_Value(T2)
        if not is_Dict_or_CustomDict(T1):
            msg = f'Expecting a dictionary, got {T1}'
            return CanBeUsed(False, msg, matches)
        else:
            K1, V1 = get_Dict_or_CustomDict_Key_Value(T1)
            # TODO: to finish
            return CanBeUsed(True, 'not implemented', matches)
    else:
        if is_Dict_or_CustomDict(T1):
            msg = 'A Dict needs a dictionary'
            return CanBeUsed(False, msg, matches)

    if is_dataclass(T2):
        # try:
        #     if issubclass(T1, T2):
        #         return True, ''
        # except:
        #     pass
        if hasattr(T1, '__name__') and T1.__name__.startswith('Loadable') and hasattr(T1, BINDINGS_ATT):
            T1 = list(getattr(T1, BINDINGS_ATT).values())[0]

        if not is_dataclass(T1):
            msg = f'Expecting dataclass to match to {T2}, got something that is not a dataclass: {T1}'
            return CanBeUsed(False, msg, matches)
        h1 = get_type_hints(T1)
        h2 = get_type_hints(T2)
        for k, v2 in h2.items():
            if not k in h1:
                msg = f'Type {T2}\n  requires field "{k}" \n  of type {v2} \n  but {T1} does not have it. '
                return CanBeUsed(False, msg, matches)
            v1 = h1[k]
            can = can_be_used_as2(v1, v2, matches)
            if not can.result:
                msg = f'Type {T2}\n  requires field "{k}"\n  of type {v2} \n  but {T1}\n  has annotated it as {v1}\n  which cannot be used. '
                msg += '\n\n' + indent(can.why, '> ')
                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, 'dataclass', matches)

        # if isinstance(T2, type):
    #     if issubclass(T1, T2):
    #         return True, ''
    #
    #     msg = f'Type {T1}\n is not a subclass of {T2}'
    #     return False, msg
    # return True, ''

    assert not is_union(T2)

    if T1 is str:
        assert T2 is not str
        msg = 'A string can only be used a string'
        return CanBeUsed(False, msg, matches)

    if is_Tuple(T1):
        assert not is_union(T2)
        if not is_Tuple(T2):
            msg = 'A tuple can only be used as a tuple'
            return CanBeUsed(False, msg, matches)
        else:

            for t1, t2 in zip(get_tuple_types(T1), get_tuple_types(T2)):
                can = can_be_used_as2(t1, t2, matches)
                if not can.result:
                    return CanBeUsed(False, f'{t1} {T2}', matches)

            return CanBeUsed(True, '', matches)
    if is_Any(T1):
        assert not is_union(T2)
        if not is_Any(T2):
            msg = 'Any is the top'
            return CanBeUsed(False, msg, matches)

    if is_TypeVar(T2):
        if T2.__name__ not in matches:
            return CanBeUsed(True, '', {T2.__name__: T1})

    if isinstance(T1, type) and isinstance(T2, type):
        # NOTE: issubclass(A, B) == type(T2).__subclasscheck__(T2, T1)
        if type.__subclasscheck__(T2, T1):
            return CanBeUsed(True, f'type.__subclasscheck__ {T1} {T2}', matches)
        else:
            msg = f'Type {T1}\n is not a subclass of {T2}'
            return CanBeUsed(False, msg, matches)

    msg = f'{T1} ? {T2}'  # pragma: no cover
    raise NotImplementedError(msg)
#
# def can_be_used_unions(T1, T2, matches) -> CanBeUsed:
#     assert is_union(T1), T1
#     assert is_union(T2), T2
#     for t in get_union_types(T2):
#         can = can_be_used_as2(T1, t, matches)
#         if can.result:
#             return CanBeUsed(True, f'union match with {t} ', can.matches)
#         reasons.append(f'- {t}: {can.why}')
#
