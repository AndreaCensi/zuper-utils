import json
from zuper_typing import dataclass
from typing import Optional

from jsonschema import validate

from zuper_ipce.conv_ipce_from_object import ipce_from_object


@dataclass
class AName:
    """ Describes a Name with optional middle name"""
    first: str
    last: str

    middle: Optional[str] = None


symbols = {'AName': AName}


def test_schema1():
    n1 = AName('one', 'two')
    y1 = ipce_from_object(n1, symbols)
    print(json.dumps(y1, indent=2))

    validate(y1, y1['$schema'])
