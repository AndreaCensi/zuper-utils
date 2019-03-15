from dataclasses import is_dataclass
from typing import *

from contracts import indent
from zuper_json.annotations_tricks import is_Any, is_Dict
from zuper_json.my_dict import is_Dict_or_CustomDict, get_Dict_or_CustomDict_Key_Value


def can_be_used_as(T1, T2) -> Tuple[bool, str]:
    # logger.debug(f'T1: {T1} T2: {T2}')
    # cop out for the easy cases
    if T1 == T2:
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

    if is_Any(T2):
        return True, ''
    if is_dataclass(T2):
        if not is_dataclass(T1):
            msg = f'Expecting dataclass to match to {T2}, got {T1}'
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
    else:
        if not issubclass(T1, T2):
            msg = f'Type {T1}\n is not a subclass of {T2}'
            return False, msg
        return True, ''
