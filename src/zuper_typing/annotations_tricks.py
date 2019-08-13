import typing
from typing import Any, Dict, Tuple, Union

from .constants import NAME_ARG, PYTHON_36


# noinspection PyProtectedMember
def is_Optional(x):
    if PYTHON_36:  # pragma: no cover
        return isinstance(x, typing._Union) and len(x.__args__) >= 2 and x.__args__[-1] is type(None)
    else:
        return isinstance(x, typing._GenericAlias) and (x.__origin__ is Union) and len(
              x.__args__) >= 2 and x.__args__[-1] is type(None)


def get_Optional_arg(x):
    assert is_Optional(x)
    args = x.__args__
    if len(args) == 2:
        return args[0]
    else:
        return make_Union(args[:-1])
    # return x.__args__[0]


def is_Union(x):
    """ Union[X, None] is not considered a Union"""
    if PYTHON_36:  # pragma: no cover
        return not is_Optional(x) and isinstance(x, typing._Union)
    else:
        return not is_Optional(x) and isinstance(x, typing._GenericAlias) and (
              x.__origin__ is Union)


def get_Union_args(x):
    assert is_Union(x)
    return tuple(x.__args__)


def make_Union(*a):
    if a: # and a[-1] is type(None):
        T0 = type(None)
        if T0 in a:
            others = tuple(_ for _ in a if _ is not T0)
            if len(others) == 1:
                return typing.Optional[others[0]]
            else:
                return typing.Optional[make_Union(*others)]

    if len(a) == 0:
        raise ValueError('empty')
    if len(a) == 1:
        x = Union[a[0]]
    elif len(a) == 2:
        x = Union[a[0], a[1]]
    elif len(a) == 3:
        x = Union[a[0], a[1], a[2]]
    elif len(a) == 4:
        x = Union[a[0], a[1], a[2], a[3]]
    elif len(a) == 5:
        x = Union[a[0], a[1], a[2], a[3], a[4]]
    else:
        x = Union.__getitem__(tuple(a))
    return x


TUPLE_EMPTY_ATTR = '__empty__'


class Caches:
    tuple_caches = {}


def make_VarTuple(a: type):
    args = (a, ...)
    return make_Tuple(*args)


def make_Tuple(*a):
    if a in Caches.tuple_caches:
        return Caches.tuple_caches[a]
    if len(a) == 0:
        x = Tuple[bool]
        # from .logging import logger
        # logger.info(f'x : {x.__args__!r}')
        #
        x.__args__ = ()
        setattr(x, TUPLE_EMPTY_ATTR, True)
    elif len(a) == 1:
        x = Tuple[a[0]]
    elif len(a) == 2:
        x = Tuple[a[0], a[1]]
    elif len(a) == 3:
        x = Tuple[a[0], a[1], a[2]]
    elif len(a) == 4:
        x = Tuple[a[0], a[1], a[2], a[3]]
    elif len(a) == 5:
        x = Tuple[a[0], a[1], a[2], a[3], a[4]]
    else:
        if PYTHON_36:  # pragma: no cover
            x = Tuple[a]
        else:
            # NOTE: actually correct
            # noinspection PyArgumentList
            x = Tuple.__getitem__(tuple(a))

    Caches.tuple_caches[a] = x
    return x


def _check_valid_arg(x):
    if isinstance(x, str):  # pragma: no cover
        msg = f'The annotations must be resolved: {x!r}'
        raise ValueError(msg)


def is_ForwardRef(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        return isinstance(x, typing._ForwardRef)
    else:
        return isinstance(x, typing.ForwardRef)

def make_ForwardRef(n):

    if PYTHON_36:  # pragma: no cover
        return  typing._ForwardRef(n)
    else:
        return  typing.ForwardRef(n)


def get_ForwardRef_arg(x) -> str:
    assert is_ForwardRef(x)
    return x.__forward_arg__


def is_Any(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        return str(x) == 'typing.Any'
    else:
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing._SpecialForm) and x._name == 'Any'


def is_TypeVar(x):
    return isinstance(x, typing.TypeVar)


def get_TypeVar_name(x):
    assert is_TypeVar(x), x
    return x.__name__


def is_ClassVar(x):
    _check_valid_arg(x)
    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing._ClassVar)
    else:
        return isinstance(x, typing._GenericAlias) and (x.__origin__ is typing.ClassVar)


def get_ClassVar_arg(x):
    assert is_ClassVar(x), x
    if PYTHON_36:  # pragma: no cover
        return x.__type__
    else:

        return x.__args__[0]


def get_ClassVar_name(x) -> str:
    assert is_ClassVar(x), x
    s = name_for_type_like(get_ClassVar_arg(x))
    return f'ClassVar[{s}]'


def is_Type(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return (x is typing.Type) or (
              isinstance(x, typing.GenericMeta) and (x.__origin__ is typing.Type))
    else:
        return (x is typing.Type) or (
              isinstance(x, typing._GenericAlias) and (x.__origin__ is type))


def is_NewType(x):
    _check_valid_arg(x)

    # if PYTHON_36:  # pragma: no cover
    #     # noinspection PyUnresolvedReferences
    #     return (x is typing.Type) or (isinstance(x, typing.GenericMeta) and (x.__origin__
    #     is typing.Type))
    # else:
    # return (x is typing.Type) or (isinstance(x, typing._GenericAlias) and (x.__origin__ is
    # type))

    return hasattr(x, '__supertype__')


def get_NewType_arg(x):
    return x.__supertype__


def get_NewType_name(x):
    return x.__name__


def get_NewType_repr(x):
    n = get_NewType_name(x)
    p = get_NewType_arg(x)
    if is_Any(p):
        return f'NewType({n!r})'
    else:
        sp = name_for_type_like(p)
        return f'NewType({n!r}, {sp})'


def is_TupleLike(x):
    return is_Tuple(x) or x is tuple


def is_Tuple(x) -> bool:
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.TupleMeta)
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'Tuple')


def is_FixedTuple(x) -> bool:
    if not is_Tuple(x):
        return False
    ts = get_tuple_types(x)
    # if len(ts) == 0:
    #     return False
    if len(ts) == 2 and ts[-1] is ...:
        return False
    else:
        return True


def is_VarTuple(x) -> bool:
    if x is tuple:
        return True
    if not is_Tuple(x):
        return False
    ts = get_tuple_types(x)
    if len(ts) == 2 and ts[-1] is ...:
        return True
    else:
        return False


def get_FixedTuple_args(x) -> Tuple[type, ...]:
    assert is_FixedTuple(x)
    return get_tuple_types(x)


def get_VarTuple_arg(x):
    if x is tuple:
        return Any
    assert is_VarTuple(x), x
    ts = get_tuple_types(x)
    if len(ts) == 0: # pragma: no cover
        return Any
    return ts[0]


def is_List(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return x is typing.List or isinstance(x,
                                              typing.GenericMeta) and x.__origin__ is \
               typing.List
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'List')


def is_Iterator(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return x is typing.Iterator or isinstance(x,
                                                  typing.GenericMeta) and x.__origin__ is \
               typing.Iterator
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'Iterator')


def is_Iterable(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return x is typing.Iterable or isinstance(x,
                                                  typing.GenericMeta) and x.__origin__ is \
               typing.Iterable
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'Iterable')


def is_Sequence(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return x is typing.Sequence or isinstance(x,
                                                  typing.GenericMeta) and x.__origin__ is \
               typing.Sequence
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'Sequence')


def is_placeholder_typevar(x):
    return is_TypeVar(x) and get_TypeVar_name(x) in ['T', 'T_co']


def get_Set_arg(x):
    assert is_Set(x)
    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        if x is typing.Set:
            return Any
    t = x.__args__[0]
    if is_placeholder_typevar(t):
        return Any

    return t


def get_List_arg(x):
    assert is_List(x), x
    if x.__args__ is None:
        return Any

    t = x.__args__[0]
    if is_placeholder_typevar(t):
        return Any
    return t


def get_Dict_args(T):
    assert is_Dict(T), T

    if T is Dict:
        return Any, Any
    # if PYTHON_36:  # pragma: no cover
    #     # noinspection PyUnresolvedReferences
    #     return x is Dict or isinstance(x, typing.GenericMeta) and x.__origin__ is typing.Dict
    #
    K, V = T.__args__

    if PYTHON_36: # pragma: no cover
        if is_placeholder_typevar(K):
            K = Any
        if is_placeholder_typevar(V):
            V = Any

    return K, V


def get_Iterator_arg(x):
    assert is_Iterator(x), x
    if x.__args__ is None:
        return Any
    t = x.__args__[0]
    if is_placeholder_typevar(t):
        return Any
    return t


def get_Iterable_arg(x):
    assert is_Iterable(x), x
    if x.__args__ is None:
        return Any
    t = x.__args__[0]
    if is_placeholder_typevar(t):
        return Any
    return t


def get_Sequence_arg(x):
    assert is_Sequence(x), x
    if x.__args__ is None:
        return Any
    t = x.__args__[0]
    if is_placeholder_typevar(t):
        return Any
    return t


def get_Type_arg(x):
    assert is_Type(x)
    if x.__args__ is None:
        return type
    return x.__args__[0]


def is_Callable(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.CallableMeta)
    else:
        return getattr(x, '_name', None) == 'Callable'
    # return hasattr(x, '__origin__') and x.__origin__ is typing.Callable

    # return isinstance(x, typing._GenericAlias) and x.__origin__.__name__ == "Callable"


def is_MyNamedArg(x):
    return hasattr(x, NAME_ARG)


def get_MyNamedArg_name(x):
    assert is_MyNamedArg(x), x
    return getattr(x, NAME_ARG)


def is_Dict(x: Any):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return x is Dict or isinstance(x, typing.GenericMeta) and x.__origin__ is typing.Dict
    else:
        return isinstance(x, typing._GenericAlias) and x._name == 'Dict'


def is_Set(x: Any):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        if x is typing.Set:
            return True
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.GenericMeta) and x.__origin__ is typing.Set
    else:
        return isinstance(x, typing._GenericAlias) and x._name == 'Set'


def get_Dict_name(T):
    assert is_Dict(T), T
    K, V = get_Dict_args(T)
    return get_Dict_name_K_V(K, V)


def get_Dict_name_K_V(K, V):
    return 'Dict[%s,%s]' % (name_for_type_like(K), name_for_type_like(V))


def get_Set_name_V(V):
    return 'Set[%s]' % (name_for_type_like(V))


def get_Union_name(V):
    return 'Union[%s]' % ",".join(name_for_type_like(_) for _ in get_Union_args(V))


def get_List_name(V):
    v = get_List_arg(V)
    return 'List[%s]' % name_for_type_like(v)


def get_Type_name(V):
    v = get_Type_arg(V)
    return 'Type[%s]' % name_for_type_like(v)


def get_Iterator_name(V):
    v = get_Iterator_arg(V)
    return 'Iterator[%s]' % name_for_type_like(v)


def get_Iterable_name(V):
    v = get_Iterable_arg(V)
    return 'Iterable[%s]' % name_for_type_like(v)


def get_Sequence_name(V):
    v = get_Sequence_arg(V)
    return 'Sequence[%s]' % name_for_type_like(v)


def get_Optional_name(V):
    v = get_Optional_arg(V)
    return 'Optional[%s]' % name_for_type_like(v)


def get_Set_name(V):
    v = get_Set_arg(V)
    return 'Set[%s]' % name_for_type_like(v)


# def get_Set_or_CustomSet_name(V):
#     from zuper_typing.my_dict import get_SetLike_arg
#     v = get_SetLike_arg(V)
#     return 'Set[%s]' % name_for_type_like(v)


def get_Tuple_name(V):
    return 'Tuple[%s]' % ",".join(name_for_type_like(_) for _ in get_tuple_types(V))


def get_tuple_types(V):
    if V is tuple:
        return Any, ...
    if PYTHON_36: # pragma: no cover
        if V.__args__ is None:
            return Any, ...
    args = V.__args__  # XXX
    if args == ():
        if hasattr(V, TUPLE_EMPTY_ATTR):
            return ()
        else:
            return Any, ...
    else:
        return args


def name_for_type_like(x):
    from .my_dict import is_DictLike, get_SetLike_name
    from .my_dict import is_SetLike
    from .my_dict import get_DictLike_name
    if is_Any(x):
        return 'Any'
    elif isinstance(x, typing.TypeVar):
        return x.__name__
    elif x is type(None):
        return 'NoneType'
    elif is_Union(x):
        return get_Union_name(x)
    elif is_List(x):
        return get_List_name(x)
    elif is_Iterator(x):
        return get_Iterator_name(x)
    elif is_Iterable(x):
        return get_Iterable_name(x)
    elif is_Tuple(x):
        return get_Tuple_name(x)
    elif is_Set(x):
        return get_Set_name(x)
    elif is_SetLike(x):
        return get_SetLike_name(x)
    elif is_Dict(x):
        return get_Dict_name(x)
    elif is_DictLike(x):
        return get_DictLike_name(x)
    elif is_Type(x):
        return get_Type_name(x)
    elif is_ClassVar(x):
        return get_ClassVar_name(x)
    elif is_Sequence(x):
        return get_Sequence_name(x)
    elif is_Optional(x):
        return get_Optional_name(x)
    elif is_NewType(x):
        return get_NewType_repr(x)
    elif is_ForwardRef(x):
        a = get_ForwardRef_arg(x)
        return f'ForwardRef({a!r})'
    elif is_Callable(x):
        info = get_Callable_info(x)

        # params = ','.join(name_for_type_like(p) for p in info.parameters_by_position)
        def ps(k, v):
            if k.startswith('__'):
                return name_for_type_like(v)
            else:
                return f'NamedArg({name_for_type_like(v)},{k!r})'

        params = ','.join(ps(k, v) for k, v in info.parameters_by_name.items())
        ret = name_for_type_like(info.returns)
        return f'Callable[[{params}],{ret}]'
    elif x is typing.IO:
        return str(x) # TODO: should get the attribute
    elif hasattr(x, '__name__'):
        # logger.info(f'not matching __name__ {type(x)} {x!r}')
        return x.__name__

    else:

        # logger.info(f'not matching {type(x)} {x!r}')
        return str(x)


# do not make a dataclass
class CallableInfo:
    parameters_by_name: Dict[str, Any]
    parameters_by_position: Tuple[type, ...]
    ordering: Tuple[str, ...]
    returns: Any

    def __init__(self, parameters_by_name, parameters_by_position, ordering, returns):
        for k, v in parameters_by_name.items():
            assert not is_MyNamedArg(v), v
        for v in parameters_by_position:
            assert not is_MyNamedArg(v), v

        self.parameters_by_name = parameters_by_name
        self.parameters_by_position = parameters_by_position
        self.ordering = ordering
        self.returns = returns

    def __repr__(self):
        return f'CallableInfo({self.parameters_by_name!r}, {self.parameters_by_position!r}, ' \
               f'{self.ordering}, {self.returns})'

    def replace(self, f: typing.Callable[[Any], Any]) -> 'CallableInfo':
        parameters_by_name = {k: f(v) for k, v in self.parameters_by_name.items()}
        parameters_by_position = tuple(f(v) for v in self.parameters_by_position)
        ordering = self.ordering
        returns = f(self.returns)
        return CallableInfo(parameters_by_name, parameters_by_position, ordering, returns)

    def as_callable(self) -> typing.Callable:
        args = []
        for k, v in self.parameters_by_name.items():
            if is_MyNamedArg(v):
                # try:
                v = v.original
            args.append(v)
        # noinspection PyTypeHints
        return typing.Callable[args, self.returns]


def get_Callable_info(x) -> CallableInfo:
    assert is_Callable(x), x
    parameters_by_name = {}
    parameters_by_position = []
    ordering = []

    args = x.__args__
    if args:
        returns = args[-1]
        rest = args[:-1]
    else:
        returns = Any
        rest = ()

    for i, a in enumerate(rest):

        if is_MyNamedArg(a):
            name = get_MyNamedArg_name(a)
            t = a.original
            # t = a
        else:
            name = f'__{i}'
            t = a

        parameters_by_name[name] = t
        ordering.append(name)

        parameters_by_position.append(t)

    return CallableInfo(parameters_by_name=parameters_by_name,
                        parameters_by_position=tuple(parameters_by_position),
                        ordering=tuple(ordering),
                        returns=returns)
