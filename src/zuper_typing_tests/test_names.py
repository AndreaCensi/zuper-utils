from typing import ClassVar, Dict, Iterable, Type, IO

from mypy_extensions import NamedArg

from zuper_typing.annotations_tricks import (
    name_for_type_like,
    make_ForwardRef,
    get_Type_arg,
)
from zuper_typing.monkey_patching_typing import original_dict_getitem
from zuper_typing.my_dict import make_set


def test_names():
    from typing import Iterator, List, Tuple, Set, Type, Callable

    xs = (
        ClassVar[int],
        Iterator[int],
        List,
        List[int],
        Tuple,
        Tuple[int],
        Set,
        Set[int],
        Type[int],
        Dict[int, int],
        make_set(int),
        original_dict_getitem((int, int)),
        Callable[[int], int],
        Callable[[], int],
        Callable[[NamedArg(int, "a")], int],
        Callable,
        IO,
        Iterable[int],
        make_ForwardRef("varname"),
        type(None),
    )
    for x in xs:
        print(name_for_type_like(x))


if __name__ == "__main__":
    test_names()
