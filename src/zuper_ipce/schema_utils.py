from typing import cast

from .constants import JSONSchema, REF_ATT


# def schema_hash(k):
#     ob_cbor = cbor2.dumps(k)
#     ob_cbor_hash = hashlib.sha256(ob_cbor).digest()
#     return ob_cbor_hash


#
# def get_all_refs(schema):
#     if isinstance(schema, dict):
#         if '$ref' in schema:
#             yield schema['$ref']
#         for _, v in schema.items():
#             yield from get_all_refs(v)
#     if isinstance(schema, list):
#         for v in schema:
#             yield from get_all_refs(v)


def make_url(x: str):
    assert isinstance(x, str), x
    return f"http://invalid.json-schema.org/{x}#"


def make_ref(x: str) -> JSONSchema:
    assert len(x) > 1, x
    assert isinstance(x, str), x
    return cast(JSONSchema, {REF_ATT: x})
