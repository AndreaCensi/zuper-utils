class SchemaCache:
    key2schema = {}


def make_key(x: object) -> tuple:
    k0 = id(type(x))
    k1 = getattr(x, "__qualname__", None)
    k2 = getattr(x, "__name__", None)
    k2b = getattr(x, "__dict_type__", None)
    k2c = getattr(x, "__set_type__", None)
    k2d = getattr(x, "__list_type__", None)
    k3 = id(x)
    k = (k3, k0, k1, k2, k2b, k2c, k2d)
    return k
