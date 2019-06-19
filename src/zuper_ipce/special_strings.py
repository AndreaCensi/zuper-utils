from collections import UserString
from typing import NewType, Dict, Callable


def valid_email(s):
    import validate_email

    is_valid = validate_email.validate_email(s)

    if not is_valid:
        msg = f'Invalid email address {s!r}'
        raise ValueError(msg)


json_formats: Dict[str, Callable[[str], None]] = {
    "date-time": None,
    "email": valid_email,
    "ipv4": None,
    "ipv6": None,
    "uri": None,
    "uri-reference": None,
    "json-pointer": None,
    "uri-template": None,

    # others:
    "domain": None,
    "multihash": None,
}


def make_special(name, sformat):
    validator = json_formats[sformat]

    class Special(UserString):
        data: str

        def __init__(self, seq):
            UserString.__init__(self, seq)
            if validator is not None:
                validator(self.data)

    return type(name, (Special,), {})


__all__ = [
    'URL',
    'DateTimeString',
    'Email',
    'IP4',
    'IP6',
    'URI',
    'URIReference',
    'JSONPointer',
    'URITemplate',
    'Domain',
    'Multihash',
    # 'IPDELink',
]

URL = make_special('URL', 'uri')
DateTimeString = make_special('DateTimeString', 'date-time')
Email = make_special('Email', 'email')
IP4 = make_special('IP4', 'ipv4')
IP6 = make_special('IP6', 'ipv6')
URI = make_special('URI', 'uri')
URIReference = make_special('URIReference', 'uri')
JSONPointer = make_special('JSONPointer', 'json-pointer')
URITemplate = make_special('URITemplate', 'uri-template')
Domain = make_special('Domain', 'domain')
Multihash = make_special('Multihash', 'multihash')

IPDELink = NewType('IPDELink', str)
