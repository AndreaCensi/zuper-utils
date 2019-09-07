from typing import Union

import typing

from zuper_typing.constants import PYTHON_36

if PYTHON_36:  # pragma: no cover
    TypeLike = type
else:
    TypeLike = Union[type, typing._SpecialForm]
