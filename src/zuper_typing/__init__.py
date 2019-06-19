from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from dataclasses import dataclass
else:
    from .monkey_patching_typing import my_dataclass as dataclass
