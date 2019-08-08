from dataclasses import dataclass, is_dataclass
from typing import *

from zuper_commons.text import indent
from .annotations_tricks import (get_Optional_arg, get_tuple_types, get_Union_args, is_Any,
                                 is_List, is_Tuple, is_TypeVar, is_Optional, is_Union, is_Sequence, get_Sequence_arg)
from .constants import ANNOTATIONS_ATT, BINDINGS_ATT
from .my_dict import (get_DictLike_args, get_ListLike_arg,
                      get_SetLike_arg, is_DictLike, is_ListLike,
                      is_SetLike)


@dataclass
class CanBeUsed:
    result: bool
    why: str
    matches: Dict[str, type]

    def __bool__(self):
        return self.result


def can_be_used_as2(T1, T2, matches: Dict[str, type],
                    assumptions0: Tuple[Tuple[Any, Any], ...] = ()) -> CanBeUsed:
    if (T1, T2) in assumptions0:
        return CanBeUsed(True, 'By assumption', matches)

    # cop out for the easy cases

    assumptions = assumptions0 + ((T1, T2),)

    if T1 is T2 or (T1 == T2):
        return CanBeUsed(True, 'equal', matches)

    # logger.info(f'can_be_used_as\n {T1} {T2}\n {assumptions0}')

    if is_TypeVar(T2):
        if T2.__name__ not in matches:
            matches = dict(matches)
            matches[T2.__name__] = T1
            return CanBeUsed(True, '', matches)
        # TODO: not implemented

    if is_Any(T2):
        return CanBeUsed(True, 'Any', matches)

    if is_Union(T1):
        if is_Union(T2):
            if get_Union_args(T1) == get_Union_args(T2):
                return CanBeUsed(True, 'same', matches)
        # can_be_used(Union[A,B], C)
        # == can_be_used(A,C) and can_be_used(B,C)

        for t in get_Union_args(T1):
            can = can_be_used_as2(t, T2, matches, assumptions)
            # logger.info(f'can_be_used_as t = {t} {T2}')
            if not can.result:
                msg = f'Cannot match {t}'
                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, '', matches)

    if is_Union(T2):
        reasons = []
        for t in get_Union_args(T2):
            can = can_be_used_as2(T1, t, matches, assumptions)
            if can.result:
                return CanBeUsed(True, f'union match with {t} ', can.matches)
            reasons.append(f'- {t}: {can.why}')

        msg = f'Cannot use {T1} as any of {T2}:\n' + "\n".join(reasons)
        return CanBeUsed(False, msg, matches)

    if is_Optional(T2):
        t2 = get_Optional_arg(T2)
        if is_Optional(T1):
            t1 = get_Optional_arg(T1)
            return can_be_used_as2(t1, t2, matches, assumptions)

        return can_be_used_as2(T1, t2, matches, assumptions)

    if is_DictLike(T2):

        if not is_DictLike(T1):
            msg = f'Expecting a dictionary, got {T1}'
            return CanBeUsed(False, msg, matches)
        else:
            K1, V1 = get_DictLike_args(T1)
            K2, V2 = get_DictLike_args(T2)

            rk = can_be_used_as2(K1, K2, matches, assumptions)
            if not rk:
                return CanBeUsed(False, f'keys {K1} {K2}: {rk}', matches)

            rv = can_be_used_as2(V1, V2, rk.matches, assumptions)
            if not rv:
                return CanBeUsed(False, f'values {V1} {V2}: {rv}', matches)

            return CanBeUsed(True, f'ok: {rk} {rv}', rv.matches)
    else:
        if is_DictLike(T1):
            msg = 'A Dict needs a dictionary'
            return CanBeUsed(False, msg, matches)

    assert not is_Union(T2)

    if is_dataclass(T2):
        # try:
        #     if issubclass(T1, T2):
        #         return True, ''
        # except:
        #     pass
        if hasattr(T1, '__name__') and T1.__name__.startswith('Loadable') and hasattr(T1,
                                                                                      BINDINGS_ATT):
            T1 = list(getattr(T1, BINDINGS_ATT).values())[0]

        if not is_dataclass(T1):
            msg = f'Expecting dataclass to match to {T2}, got something that is not a ' \
                  f'dataclass: {T1}'
            msg += f'  union: {is_Union(T1)}'
            return CanBeUsed(False, msg, matches)
        # h1 = get_type_hints(T1)
        # h2 = get_type_hints(T2)

        h1 = getattr(T1, ANNOTATIONS_ATT, {})
        h2 = getattr(T2, ANNOTATIONS_ATT, {})

        for k, v2 in h2.items():
            if not k in h1:
                # msg = f'Type {T2}\n  requires field "{k}" \n  of type {v2} \n  but {T1} does ' \
                #     f'' \
                #     f'not have it. '
                msg = k
                return CanBeUsed(False, msg, matches)
            v1 = h1[k]
            can = can_be_used_as2(v1, v2, matches, assumptions)
            if not can.result:
                msg = f'Type {T2}\n  requires field "{k}"\n  of type\n       {v2} \n  but' + \
                      f' {T1}\n  has annotated it as\n       {v1}\n  which cannot be used. '
                msg += '\n\n' + f'assumption: {assumptions}'
                msg += '\n\n' + indent(can.why, '> ')

                return CanBeUsed(False, msg, matches)

        return CanBeUsed(True, 'dataclass', matches)

    if T1 is int:
        if T2 is int:

            return CanBeUsed(True, '', matches)
        else:
            msg = 'Need int'
            return CanBeUsed(False, msg, matches)

    if T1 is str:
        assert T2 is not str
        msg = 'A string can only be used a string'
        return CanBeUsed(False, msg, matches)

    if is_Tuple(T1):
        assert not is_Union(T2)
        if not is_Tuple(T2):
            msg = 'A tuple can only be used as a tuple'
            return CanBeUsed(False, msg, matches)
        else:

            for t1, t2 in zip(get_tuple_types(T1), get_tuple_types(T2)):
                can = can_be_used_as2(t1, t2, matches, assumptions)
                if not can.result:
                    return CanBeUsed(False, f'{t1} {T2}', matches)
                matches = can.matches
            return CanBeUsed(True, '', matches)

    if is_Tuple(T2):
        assert not is_Tuple(T1)
        return CanBeUsed(False, '', matches)
    #
    # if is_Iterable(T1):
    #     t1 = get_Iterable_arg(T1)
    #
    #     if is_Tuple(T2):
    #         for t2 in get_tuple_types(T2):
    #             can = can_be_used_as2(t1, t2, matches, assumptions)
    #             if not can.result:
    #                 return CanBeUsed(False, f'{t1} {T2}', matches)
    #             matches = can.matches
    #         return CanBeUsed(True, '', matches)
    #     else:
    #
    #         return CanBeUsed(False, 'not implemented', matches)

    if is_Any(T1):
        assert not is_Union(T2)
        if not is_Any(T2):
            msg = 'Any is the top'
            return CanBeUsed(False, msg, matches)

    if is_ListLike(T2):
        if not is_ListLike(T1):
            msg = 'A List can only be used as a List'
            return CanBeUsed(False, msg, matches)

        t1 = get_ListLike_arg(T1)
        t2 = get_ListLike_arg(T2)
        # print(f'matching List with {t1} {t2}')
        can = can_be_used_as2(t1, t2, matches, assumptions)

        if not can.result:
            return CanBeUsed(False, f'{t1} {T2}', matches)

        return CanBeUsed(True, '', can.matches)

    if is_SetLike(T2):
        if not is_SetLike(T1):
            msg = 'A Set can only be used as a Set'
            return CanBeUsed(False, msg, matches)

        t1 = get_SetLike_arg(T1)
        t2 = get_SetLike_arg(T2)
        # print(f'matching List with {t1} {t2}')
        can = can_be_used_as2(t1, t2, matches, assumptions)

        if not can.result:
            return CanBeUsed(False, f'{t1} {T2}', matches)

        return CanBeUsed(True, '', can.matches)


    if is_Sequence(T1):
        t1 = get_Sequence_arg(T1)

        if is_ListLike(T2):
            t2 = get_ListLike_arg(T2)
            can = can_be_used_as2(t1, t2, matches, assumptions)

            if not can.result:
                return CanBeUsed(False, f'{t1} {T2}', matches)

            return CanBeUsed(True, '', can.matches)

        msg = f'Needs a Sequence[{t1}], got {T2}'
        return CanBeUsed(False, msg, matches)


    if isinstance(T1, type) and isinstance(T2, type):
        # NOTE: issubclass(A, B) == type(T2).__subclasscheck__(T2, T1)
        if type.__subclasscheck__(T2, T1):
            return CanBeUsed(True, f'type.__subclasscheck__ {T1} {T2}', matches)
        else:
            msg = f'Type {T1}\n is not a subclass of {T2}'
            return CanBeUsed(False, msg, matches)

    if is_List(T1):
        msg = f'Needs a List, got {T2}'
        return CanBeUsed(False, msg, matches)

    if T1 is type(None):
        if T2 is type(None):
            return CanBeUsed(True, '', matches)
        else:
            msg = f'Needs type(None), got {T2}'
            return CanBeUsed(False, msg, matches)
    if T2 is type(None):
        msg = f'Needs type(None), got {T1}'
        return CanBeUsed(False, msg, matches)
    msg = f'{T1} ? {T2}'  # pragma: no cover
    raise NotImplementedError(msg)
