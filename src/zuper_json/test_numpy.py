import json
from dataclasses import dataclass, field

import numpy as np
from numpy.testing import assert_allclose

from .json_utils import encode_bytes_before_json_serialization
from .numpy_encoding import dict_from_numpy, numpy_from_dict
from .test_utils import assert_type_roundtrip, assert_object_roundtrip


def array_eq(arr1, arr2):
    return (isinstance(arr1, np.ndarray) and
            isinstance(arr2, np.ndarray) and
            arr1.shape == arr2.shape and
            (arr1 == arr2).all())


def test_numpy_01():
    @dataclass
    class C:
        data: np.ndarray = field(metadata=dict(contract='array[HxWx3](uint8)'))

    assert_type_roundtrip(C, {})


def test_numpy_02():
    @dataclass
    class C:
        data: np.ndarray = field(metadata=dict(contract='array[HxWx3](uint8)'))
        #
        # def __eq__(self, other):
        #     if not isinstance(other, C):
        #         return NotImplemented
        #     return array_eq(self.data, other.data)

    x = np.random.rand(1)
    c = C(x)
    assert_object_roundtrip(c, {})


#
# def test_numpy_03():
#     x = np.random.rand(2, 3)
#     b = bytes_from_numpy(x)
#     y = numpy_from_bytes(b)
#     assert_allclose(x, y)


def test_numpy_04():
    x = np.random.rand(2, 3)

    d = dict_from_numpy(x)
    d1 = encode_bytes_before_json_serialization(d)
    print(json.dumps(d1, indent=3))
    y = numpy_from_dict(d)
    assert_allclose(x, y)
