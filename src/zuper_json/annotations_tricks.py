import typing
from typing import Union, Any, Dict

from zuper_json.constants import NAME_ARG
from .constants import PYTHON_36


# noinspection PyProtectedMember
def is_optional(x):
    if PYTHON_36:  # pragma: no cover
        return isinstance(x, typing._Union) and len(x.__args__) == 2 and x.__args__[-1] is type(None)
    else:
        return isinstance(x, typing._GenericAlias) and (x.__origin__ is Union) and len(x.__args__) == 2 and x.__args__[
            -1] is type(None)


def get_optional_type(x):
    assert is_optional(x)
    return x.__args__[0]


def is_union(x):
    """ Union[X, None] is not considered a Union"""
    if PYTHON_36:  # pragma: no cover
        return not is_optional(x) and isinstance(x, typing._Union)
    else:
        return not is_optional(x) and isinstance(x, typing._GenericAlias) and (x.__origin__ is Union)


def get_union_types(x):
    assert is_union(x)
    return tuple(x.__args__)


def _check_valid_arg(x):
    if isinstance(x, str):  # pragma: no cover
        msg = f'The annotations must be resolved: {x!r}'
        raise ValueError(msg)


def is_forward_ref(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        return isinstance(x, typing._ForwardRef)
    else:
        return isinstance(x, typing.ForwardRef)


def get_forward_ref_arg(x) -> str:
    assert is_forward_ref(x)
    return x.__forward_arg__


def is_Any(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        return str(x) == 'typing.Any'
    else:
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing._SpecialForm) and x._name == 'Any'


def is_ClassVar(x):
    _check_valid_arg(x)
    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing._ClassVar)
    else:
        return isinstance(x, typing._GenericAlias) and (x.__origin__ is typing.ClassVar)


def get_ClassVar_arg(x):
    assert is_ClassVar(x)
    if PYTHON_36:  # pragma: no cover
        return x.__type__
    else:

        return x.__args__[0]


def is_Type(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return (x is typing.Type) or (isinstance(x, typing.GenericMeta) and (x.__origin__ is typing.Type))
    else:
        return (x is typing.Type) or (isinstance(x, typing._GenericAlias) and (x.__origin__ is type))


def is_Tuple(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.TupleMeta)
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'Tuple')


def is_List(x):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.GenericMeta) and x.__origin__ is typing.List
    else:
        return isinstance(x, typing._GenericAlias) and (x._name == 'List')


def get_List_arg(x):
    assert is_List(x)
    return x.__args__[0]


def get_Type_arg(x):
    assert is_Type(x)
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
    assert is_MyNamedArg(x)
    return getattr(x, NAME_ARG)


def is_Dict(x: Any):
    _check_valid_arg(x)

    if PYTHON_36:  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return isinstance(x, typing.GenericMeta) and x.__origin__ is typing.Dict
    else:
        return isinstance(x, typing._GenericAlias) and x._name == 'Dict'


def get_Dict_name(T):
    assert is_Dict(T)
    K, V = T.__args__
    return get_Dict_name_K_V(K, V)


def get_Dict_name_K_V(K, V):
    return 'Dict[%s,%s]' % (name_for_type_like(K), name_for_type_like(V))


def name_for_type_like(x):
    if is_Any(x):
        return 'Any'
    elif isinstance(x, type):
        return x.__name__
    elif isinstance(x, typing.TypeVar):
        return x.__name__
    elif is_Dict(x):
        return get_Dict_name(x)
    elif is_Callable(x):
        info = get_Callable_info(x)
        params = ','.join(name_for_type_like(p) for p in info.parameters_by_position)
        ret = name_for_type_like(info.returns)
        return f'Callable[[{params}],{ret}'
    elif hasattr(x, '__name__'):
        return x.__name__
    else:
        return str(x)


from typing import Tuple


# do not make a dataclass
class CallableInfo:
    parameters_by_name: Dict[str, Any]
    parameters_by_position: Tuple
    ordering: Tuple[str, ...]
    returns: Any

    def __init__(self, parameters_by_name, parameters_by_position, ordering, returns):
        self.parameters_by_name = parameters_by_name
        self.parameters_by_position = parameters_by_position
        self.ordering = ordering
        self.returns = returns


def get_Callable_info(x) -> CallableInfo:
    assert is_Callable(x)
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
        else:
            name = f'#{i}'
            t = a

        parameters_by_name[name] = t
        ordering.append(name)

        parameters_by_position.append(t)

    return CallableInfo(parameters_by_name=parameters_by_name,
                        parameters_by_position=tuple(parameters_by_position),
                        ordering=tuple(ordering),
                        returns=returns)
