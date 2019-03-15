import numpy as np

from contracts import check_isinstance


def dict_from_numpy(x: np.ndarray) -> dict:
    res = {}
    res['shape'] = list(x.shape)
    res['dtype'] = x.dtype.name
    res['data'] = x.tobytes()
    return res


def numpy_from_dict(d: dict) -> np.ndarray:
    shape = tuple(d['shape'])
    dtype = d['dtype']
    data: bytes = d['data']
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
