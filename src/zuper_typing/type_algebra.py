from dataclasses import dataclass, field, is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from zuper_typing.annotations_tricks import (
    get_FixedTuple_args,
    get_TypeVar_name,
    get_VarTuple_arg,
    is_FixedTuple,
    is_Optional,
    is_TypeVar,
    is_VarTuple,
    make_Tuple,
    make_Union,
    make_VarTuple,
)
from zuper_typing.my_dict import (
    get_DictLike_args,
    get_ListLike_arg,
    get_SetLike_arg,
    is_DictLike,
    is_ListLike,
    is_SetLike,
    make_dict,
    make_list,
    make_set,
)
from zuper_typing.my_intersection import make_Intersection
from zuper_typing.uninhabited import is_Uninhabited, make_Uninhabited


def type_sup(a, b):
    assert a is not None
    assert b is not None

    if a is b or (a == b):
        return a

    if a is object or b is object:
        return object

    if is_Uninhabited(a):
        return b
    if is_Uninhabited(b):
        return a

    if a is type(None):
        if is_Optional(b):
            return b
        else:
            return Optional[b]
    if b is type(None):
        if is_Optional(a):
            return a
        else:
            return Optional[a]

    if (a, b) in [(bool, int), (int, bool)]:
        return int

    if is_ListLike(a) and is_ListLike(b):
        A = get_ListLike_arg(a)
        B = get_ListLike_arg(b)
        u = type_sup(A, B)
        return make_list(u)

    if is_SetLike(a) and is_SetLike(b):
        A = get_SetLike_arg(a)
        B = get_SetLike_arg(b)
        u = type_sup(A, B)
        return make_set(u)

    if is_DictLike(a) and is_DictLike(b):
        KA, VA = get_DictLike_args(a)
        KB, VB = get_DictLike_args(b)
        K = type_sup(KA, KB)
        V = type_sup(VA, VB)
        return make_dict(K, V)

    if is_VarTuple(a) and is_VarTuple(b):
        VA = get_VarTuple_arg(a)
        VB = get_VarTuple_arg(b)
        V = type_sup(VA, VB)
        return make_VarTuple(V)

    if is_FixedTuple(a) and is_FixedTuple(b):
        tas = get_FixedTuple_args(a)
        tbs = get_FixedTuple_args(b)
        ts = tuple(type_sup(ta, tb) for ta, tb in zip(tas, tbs))
        return make_Tuple(*ts)

    if is_dataclass(a) and is_dataclass(b):
        return type_sup_dataclass(a, b)

    return make_Union(a, b)

    # raise NotImplementedError(a, b)


def type_inf_dataclass(a, b):
    from zuper_typing.monkey_patching_typing import my_dataclass

    ann_a = a.__annotations__
    ann_b = b.__annotations__

    all_keys = set(ann_a) | set(ann_b)

    res = {}
    for k in all_keys:
        if k in ann_a and k not in ann_b:
            R = ann_a[k]
        elif k not in ann_a and k in ann_b:
            R = ann_b[k]
        else:
            VA = ann_a[k]
            VB = ann_b[k]
            R = type_inf(VA, VB)

        if is_Uninhabited(R):
            return R
        res[k] = R
    name = f"Int_{a.__name__}_{b.__name__}"
    T2 = my_dataclass(
        type(name, (), {"__annotations__": res, "__module__": "zuper_typing"})
    )
    return T2


def type_sup_dataclass(a, b):
    from zuper_typing.monkey_patching_typing import my_dataclass

    ann_a = a.__annotations__
    ann_b = b.__annotations__

    common_keys = set(ann_a) & set(ann_b)

    res = {}
    for k in common_keys:
        if k in ann_a and k not in ann_b:
            R = ann_a[k]
        elif k not in ann_a and k in ann_b:
            R = ann_b[k]
        else:
            VA = ann_a[k]
            VB = ann_b[k]
            R = type_sup(VA, VB)
        res[k] = R

    name = f"Join_{a.__name__}_{b.__name__}"
    T2 = my_dataclass(
        type(name, (), {"__annotations__": res, "__module__": "zuper_typing"})
    )
    return T2


def type_inf(a, b):
    assert a is not None
    assert b is not None

    if a is object:
        return b
    if b is object:
        return a
    if is_Uninhabited(a):
        return a
    if is_Uninhabited(b):
        return b
    if a is b or (a == b):
        return a

    if (a, b) in [(bool, int), (int, bool)]:
        return bool

    if is_TypeVar(a) and is_TypeVar(b):
        if get_TypeVar_name(a) == get_TypeVar_name(b):
            return a
    if is_TypeVar(a) or is_TypeVar(b):
        return make_Intersection((a, b))

    primitive = (bool, int, str, Decimal, datetime, float, bytes, type(None))
    if a in primitive or b in primitive:
        return make_Uninhabited()

    if is_ListLike(a) ^ is_ListLike(b):
        return make_Uninhabited()
    if is_ListLike(a) & is_ListLike(b):
        A = get_ListLike_arg(a)
        B = get_ListLike_arg(b)
        u = type_inf(A, B)
        return make_list(u)
    if is_SetLike(a) ^ is_SetLike(b):
        return make_Uninhabited()
    if is_SetLike(a) and is_SetLike(b):
        A = get_SetLike_arg(a)
        B = get_SetLike_arg(b)
        u = type_inf(A, B)
        return make_set(u)

    if is_DictLike(a) ^ is_DictLike(b):
        return make_Uninhabited()
    if is_DictLike(a) and is_DictLike(b):
        KA, VA = get_DictLike_args(a)
        KB, VB = get_DictLike_args(b)
        K = type_inf(KA, KB)
        V = type_inf(VA, VB)
        return make_dict(K, V)

    if is_dataclass(a) ^ is_dataclass(b):
        return make_Uninhabited()

    if is_dataclass(a) and is_dataclass(b):
        return type_inf_dataclass(a, b)

    if is_VarTuple(a) and is_VarTuple(b):
        VA = get_VarTuple_arg(a)
        VB = get_VarTuple_arg(b)
        V = type_inf(VA, VB)
        return make_VarTuple(V)

    if is_FixedTuple(a) and is_FixedTuple(b):
        tas = get_FixedTuple_args(a)
        tbs = get_FixedTuple_args(b)
        ts = tuple(type_inf(ta, tb) for ta, tb in zip(tas, tbs))
        return make_Tuple(*ts)

    return make_Intersection((a, b))


@dataclass
class MatchConstraint:
    ub: type = None
    lb: type = None

    def impose_subtype(self, ub) -> "MatchConstraint":
        ub = type_sup(self.ub, ub) if self.ub is not None else ub
        return MatchConstraint(ub=ub, lb=self.lb)

    def impose_supertype(self, lb) -> "MatchConstraint":
        lb = type_inf(self.lb, lb) if self.lb is not None else lb
        return MatchConstraint(lb=lb, ub=self.ub)


@dataclass
class Matches:
    m: Dict[str, MatchConstraint] = field(default_factory=dict)

    def get_matches(self):
        res = {}
        for k, v in self.m.items():
            if v.ub is not None:
                res[k] = v.ub
        return res

    def get_ub(self, k: str):
        if k not in self.m:
            return None
        return self.m[k].ub

    def get_lb(self, k: str):
        if k not in self.m:
            return None
        return self.m[k].lb

    def must_be_subtype_of(self, k: str, ub) -> "Matches":
        m2 = dict(self.m)
        if k not in m2:
            m2[k] = MatchConstraint()
        m2[k] = m2[k].impose_subtype(ub=ub)
        return Matches(m2)

    def must_be_supertype_of(self, k: str, lb) -> "Matches":
        m2 = dict(self.m)
        if k not in m2:
            m2[k] = MatchConstraint()
        m2[k] = m2[k].impose_supertype(lb=lb)
        return Matches(m2)
