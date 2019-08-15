from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from dataclasses import dataclass

    # noinspection PyUnresolvedReferences
    from typing import Generic
else:
    # noinspection PyUnresolvedReferences
    from .monkey_patching_typing import my_dataclass as dataclass

    # noinspection PyUnresolvedReferences
    from typing import Generic
