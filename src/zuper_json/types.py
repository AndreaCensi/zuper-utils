from typing import Dict, List, Union, NewType, ForwardRef

JSONObject = Dict[str, ForwardRef('MemoryJSON')]
JSONList = List['MemoryJSON']
MemoryJSON = Union[int, str, float, JSONList, JSONObject]

CanonicalJSONString = NewType('CanonicalJSONString', str)

Hash = NewType('Hash', str)
