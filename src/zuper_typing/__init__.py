from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from dataclasses import dataclass
    from typing import Generic
else:
    from .monkey_patching_typing import my_dataclass as dataclass, Generic as Generic
