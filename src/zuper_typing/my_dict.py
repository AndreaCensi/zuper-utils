from dataclasses import is_dataclass
from typing import Any, cast, ClassVar, Dict, List, Set, Tuple, Type, TypeVar

from zuper_typing.aliases import TypeLike
from .annotations_tricks import (
    get_Dict_args,
    get_Dict_name_K_V,
    get_List_arg,
    get_Set_arg,
    get_Set_name_V,
    is_Dict,
    is_List,
    is_Set,
    name_for_type_like,
)

_V = TypeVar("_V")
_K = TypeVar("_K")

_X = TypeVar("_X")
_Y = TypeVar("_Y")
_Z = TypeVar("_Z")


class CustomSet(set):
    __set_type__: ClassVar[type]

    def __hash__(self) -> Any:
        try:
            return self._cached_hash
        except AttributeError:
            try:
                h = self._cached_hash = hash(tuple(sorted(self)))
            except TypeError:  # pragma: no cover
                h = self._cached_hash = hash(tuple(self))
            return h


class CustomList(list):
    __list_type__: ClassVar[type]

    def __hash__(self) -> Any:  # pragma: no cover
        try:
            return self._cached_hash
        except AttributeError:  # pragma: no cover
            h = self._cached_hash = hash(tuple(self))
            return h


class CustomDict(dict):
    __dict_type__: ClassVar[Tuple[type, type]]

    def __hash__(self) -> Any:
        try:
            return self._cached_hash
        except AttributeError:
            try:
                h = self._cached_hash = hash(tuple(sorted(self.items())))
            except TypeError:  # pragma: no cover
                h = self._cached_hash = hash(tuple(self.items()))
            return h

    def copy(self: _X) -> _X:
        return type(self)(self)


def get_CustomSet_arg(x: Type[CustomSet]) -> TypeLike:
    assert is_CustomSet(x)
    return x.__set_type__


def get_CustomList_arg(x: Type[CustomList]) -> TypeLike:
    assert is_CustomList(x)
    return x.__list_type__


def get_CustomDict_args(x: Type[CustomDict]) -> Tuple[TypeLike, TypeLike]:
    assert is_CustomDict(x), x
    return x.__dict_type__


def is_CustomSet(x: TypeLike) -> bool:
    return isinstance(x, type) and issubclass(x, CustomSet)


def is_CustomList(x: TypeLike) -> bool:
    return isinstance(x, type) and issubclass(x, CustomList)


def is_CustomDict(x: TypeLike) -> bool:
    return isinstance(x, type) and issubclass(x, CustomDict)


def is_SetLike(x: TypeLike) -> bool:
    return (x is set) or is_Set(x) or is_CustomSet(x)


def is_ListLike(x: TypeLike) -> bool:
    return (x is list) or is_List(x) or is_CustomList(x)


def is_DictLike(x: TypeLike) -> bool:
    return (x is dict) or is_Dict(x) or is_CustomDict(x)


def is_ListLike_canonical(x: Type[List]) -> bool:
    return is_CustomList(x)


def is_DictLike_canonical(x: Type[Dict]) -> bool:
    return is_CustomDict(x)


def is_SetLike_canonical(x: Type[Set]) -> bool:
    return is_CustomSet(x)


def get_SetLike_arg(x: Type[Set[_V]]) -> Type[_V]:
    if x is set:
        return Any

    if is_Set(x):
        return get_Set_arg(x)

    if is_CustomSet(x):
        x = cast(Type[CustomSet], x)
        return get_CustomSet_arg(x)

    assert False, x


def get_ListLike_arg(x: Type[List[_V]]) -> Type[_V]:
    if x is list:
        return Any

    if is_List(x):
        return get_List_arg(x)

    if is_CustomList(x):
        # noinspection PyTypeChecker
        return get_CustomList_arg(x)

    assert False, x


def get_DictLike_args(x: Type[Dict[_K, _V]]) -> Tuple[Type[_K], Type[_V]]:
    assert is_DictLike(x), x
    if is_Dict(x):
        return get_Dict_args(x)
    elif is_CustomDict(x):
        x = cast(Type[CustomDict], x)
        return get_CustomDict_args(x)
    elif x is dict:
        return Any, Any
    else:
        assert False, x


def get_DictLike_name(T: Type[Dict]) -> str:
    assert is_DictLike(T)
    K, V = get_DictLike_args(T)
    return get_Dict_name_K_V(K, V)


def get_ListLike_name(x: Type[List]) -> str:
    V = get_ListLike_arg(x)
    return "List[%s]" % name_for_type_like(V)


def get_SetLike_name(x: Type[Set]) -> str:
    v = get_SetLike_arg(x)
    return "Set[%s]" % name_for_type_like(v)


class Caches:
    use_cache = True
    make_set_cache = {}
    make_list_cache = {}
    make_dict_cache = {}


def assert_good_typelike(x: TypeLike) -> None:
    if isinstance(x, type):
        return
    if is_dataclass(type(x)):
        n = type(x).__name__
        if n in ["Constant"]:
            raise AssertionError(x)


def make_list(V_: Type[_X]) -> Type[List[Type[_X]]]:
    if Caches.use_cache:
        if V_ in Caches.make_list_cache:
            return Caches.make_list_cache[V_]

    assert_good_typelike(V_)

    class MyType(type):
        def __eq__(self, other) -> bool:
            V2 = getattr(self, "__list_type__")
            if is_List(other):
                return V2 == get_List_arg(other)
            res2 = (
                isinstance(other, type)
                and issubclass(other, CustomList)
                and other.__list_type__ == V2
            )
            return res2

        def __hash__(cls) -> Any:  # pragma: no cover
            return 1  # XXX
            # logger.debug(f'here ___eq__ {self} {other} {issubclass(other, CustomList)} = {res}')

    def copy(self: _X) -> _X:
        return type(self)(self)

    attrs = {"__list_type__": V_, "copy": copy}

    # name = get_List_name(V)
    name = "List[%s]" % name_for_type_like(V_)

    res = MyType(name, (CustomList,), attrs)

    setattr(res, "EMPTY", res([]))
    Caches.make_list_cache[V_] = res
    # noinspection PyTypeChecker
    return res


def make_set(V: TypeLike) -> Type[CustomSet]:
    if Caches.use_cache:
        if V in Caches.make_set_cache:
            return Caches.make_set_cache[V]

    assert_good_typelike(V)

    class MyType(type):
        def __eq__(self, other) -> bool:
            V2 = getattr(self, "__set_type__")
            if is_Set(other):
                return V2 == get_Set_arg(other)
            res2 = (
                isinstance(other, type)
                and issubclass(other, CustomSet)
                and other.__set_type__ == V2
            )
            return res2

        def __hash__(cls) -> Any:  # pragma: no cover
            return 1  # XXX

    def copy(self: _X) -> _X:
        return type(self)(self)

    attrs = {"__set_type__": V, "copy": copy}
    name = get_Set_name_V(V)
    res = MyType(name, (CustomSet,), attrs)
    setattr(res, "EMPTY", res([]))
    Caches.make_set_cache[V] = res
    # noinspection PyTypeChecker
    return res


# from . import logger
# def make_dict(K: Type[X], V: Type[Y]) -> Type[Dict[Type[X], Type[Y]]]:
def make_dict(K: TypeLike, V: TypeLike) -> type:  # Type[CustomDict]:
    key = (K, V)
    if Caches.use_cache:

        if key in Caches.make_dict_cache:
            return Caches.make_dict_cache[key]

    assert_good_typelike(K)
    assert_good_typelike(V)

    class MyType(type):
        def __eq__(self, other) -> bool:
            K2, V2 = getattr(self, "__dict_type__")
            if is_Dict(other):
                K1, V1 = get_Dict_args(other)
                return K2 == K1 and V2 == V1
            res2 = (
                isinstance(other, type)
                and issubclass(other, CustomDict)
                and other.__dict_type__ == (K2, V2)
            )
            return res2

        def __hash__(cls) -> Any:
            return 1  # XXX

    if isinstance(V, str):
        msg = f"Trying to make dict with K = {K!r} and V = {V!r}; I need types, not strings."
        raise ValueError(msg)
    # warnings.warn('Creating dict', stacklevel=2)

    attrs = {"__dict_type__": (K, V)}
    name = get_Dict_name_K_V(K, V)

    res = MyType(name, (CustomDict,), attrs)

    setattr(res, "EMPTY", res({}))
    Caches.make_dict_cache[key] = res

    # noinspection PyUnresolvedReferences
    import zuper_typing.my_dict

    zuper_typing.my_dict.__dict__[res.__name__] = res
    # noinspection PyTypeChecker
    return res
