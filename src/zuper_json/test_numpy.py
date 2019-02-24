from dataclasses import dataclass, field

import numpy as np

from .test_utils import assert_type_roundtrip, known_failure

@known_failure
def test_numpy_01():
    @dataclass
    class C:
        data: np.ndarray = field(metadata=dict(contract='array[HxWx3](uint8)'))

    assert_type_roundtrip(C, {})

    serialized_type = {
        "type": "object",
        "numpy": True,
        "contract": 'array[HxWx3](uint8)',
    }

    serialized_object = {
        "shape": [10, 10, 3],
        "dtype": 'uint8',
        "byteorder": "l",
        "bytes_": ...
    }
