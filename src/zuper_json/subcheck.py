from dataclasses import is_dataclass
from typing import *

from zuper_commons.text import indent
from zuper_json.constants import BINDINGS_ATT
from .annotations_tricks import is_Any, is_union, get_union_types, is_optional, get_optional_type, is_Tuple
from .my_dict import is_Dict_or_CustomDict, get_Dict_or_CustomDict_Key_Value

from .logging import logger

def can_be_used_as(T1, T2) -> Tuple[bool, str]:
    # cop out for the easy cases

    if T1 is T2 or (T1 == T2):
        return True, ''

    if is_Any(T2):
        return True, ''

    if is_Dict_or_CustomDict(T2):
        K2, V2 = get_Dict_or_CustomDict_Key_Value(T2)
        if not is_Dict_or_CustomDict(T1):
            msg = f'Expecting a dictionary, got {T1}'
            return False, msg
        else:
            K1, V1 = get_Dict_or_CustomDict_Key_Value(T1)
            # TODO: to finish
            return True, ''

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
            return False, msg
        h1 = get_type_hints(T1)
        h2 = get_type_hints(T2)
        for k, v2 in h2.items():
            if not k in h1:  # and not optional...
                msg = f'Type {T2}\n  requires field "{k}" \n  of type {v2} \n  but {T1} does not have it. '
                return False, msg
            v1 = h1[k]
            ok, why = can_be_used_as(v1, v2)
            if not ok:
                msg = f'Type {T2}\n  requires field "{k}"\n  of type {v2} \n  but {T1}\n  has annotated it as {v1}\n  which cannot be used. '
                msg += '\n\n' + indent(why, '> ')
                return False, msg

        return True, ''

    if is_union(T2):
        reasons = []
        for t in get_union_types(T2):
            ok, why = can_be_used_as(T1, t)
            if ok:
                return True, ''
            reasons.append(f'- {t}: {why}')


        msg = f'Cannot use {T1} as any of {T2}:\n' + "\n".join(reasons)
        return False, msg

    if is_optional(T2):
        t = get_optional_type(T2)
        ok, _ = can_be_used_as(T1, t)
        return ok, _

        # if isinstance(T2, type):
    #     if issubclass(T1, T2):
    #         return True, ''
    #
    #     msg = f'Type {T1}\n is not a subclass of {T2}'
    #     return False, msg
    # return True, ''

    assert not is_union(T2)

    if isinstance(T1, type) and isinstance(T2, type):
        if issubclass(T1, T2):
            return True, ''
        else:
            msg = f'Type {T1}\n is not a subclass of {T2}'
            return False, msg

    if T1 is str:
        assert T2 is not str
        return False, 'A string can only be used a string'

    if is_Tuple(T1):
        assert not is_union(T2)
        if not is_Tuple(T2):
            return False, 'A tuple can only be used as a tuple'

    if is_Any(T1):
        assert not is_union(T2)
        if not is_Any(T2):
            return False, 'Any is the top'

    msg = f'{T1} ? {T2}' # pragma: no cover
    raise NotImplementedError(msg)
