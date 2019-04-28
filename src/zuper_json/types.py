from datetime import datetime
from typing import Dict, List, Union, NewType

# JSONObject = Dict[str, Dict]
# JSONList = List['MemoryJSON']
# MemoryJSON = Union[int, str, float, JSONList, JSONObject, type(None)]
# JSONObject = Dict[str, Dict]
# JSONList = List['MemoryJSON']
IPCE = Union[int, str, float, bytes, datetime, List['IPCE'], Dict[str, 'IPCE'], type(None)]
IPCL = Union[int, str, float, bytes, datetime, List['IPCL'], Dict[str, 'IPCL'], type(None)]

CID = NewType('CID', str)
