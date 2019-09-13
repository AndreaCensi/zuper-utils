from typing import Optional

from jsonschema import validate

from zuper_ipce import ipce_from_object
from zuper_typing import dataclass


@dataclass
class AName:
    """ Describes a Name with optional middle name"""

    first: str
    last: str

    middle: Optional[str] = None


symbols = {"AName": AName}


def test_schema1():
    n1 = AName("one", "two")
    y1 = ipce_from_object(n1, globals_=symbols)
    # print(json.dumps(y1, indent=2))

    validate(y1, y1["$schema"])
