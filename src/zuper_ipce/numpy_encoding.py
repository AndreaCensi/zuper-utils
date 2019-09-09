import numpy as np

from zuper_commons.types import check_isinstance
from .types import IPCE


def ipce_from_numpy_array(x: np.ndarray) -> IPCE:
    res = {"shape": list(x.shape), "dtype": x.dtype.name, "data": x.tobytes()}
    from .ipce_spec import sorted_dict_cbor_ord

    res = sorted_dict_cbor_ord(res)
    return res


def numpy_array_from_ipce(d: IPCE) -> np.ndarray:
    shape = tuple(d["shape"])
    dtype = d["dtype"]
    data: bytes = d["data"]
    check_isinstance(data, bytes)
    a = np.frombuffer(data, dtype=dtype)
    res = a.reshape(shape)
    return res


#
#
# def bytes_from_numpy(a: np.ndarray) -> bytes:
#     import h5py
#     io = BytesIO()
#     with h5py.File(io) as f:
#         # f.setdefault("compression", "lzo")
#         f['value'] = a
#     uncompressed = io.getvalue()
#
#     compressed_data = zlib.compress(uncompressed)
#     return compressed_data
#
#
# def numpy_from_bytes(b: bytes) -> np.ndarray:
#     b = zlib.decompress(b)
#     import h5py
#     io = BytesIO(b)
#     with h5py.File(io) as f:
#         # f.setdefault("compression", "lzw")
#         a = f['value']
#         res = np.array(a)
#         return res
