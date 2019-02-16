import json


def json_dump(x) -> str:
    x = recursive_sort(x)

    if False:
        s = json.dumps(x, ensure_ascii=False, allow_nan=False, check_circular=False,
                       indent=2)
    else:
        s = json.dumps(x, ensure_ascii=False, allow_nan=False, check_circular=False,
                       separators=(',', ':'))
    # (optional): put the links on the same line instead of indenting
    # "$schema": {"/": "sha6:92c65f"},

    # s = re.sub(r'\n\s+\"/\"(.*)\s*\n\s*', r'"/"\1', s)

    return s


def recursive_sort(x):
    if isinstance(x, dict):
        s = sorted(x)
        return {k: recursive_sort(x[k]) for k in s}
    else:
        return x
