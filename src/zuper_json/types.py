from typing import Dict, List, Union, NewType

JSONObject = Dict[str, Dict]
JSONList = List['MemoryJSON']
MemoryJSON = Union[int, str, float, JSONList, JSONObject, type(None)]

CanonicalJSONString = NewType('CanonicalJSONString', str)

Hash = NewType('Hash', str)
