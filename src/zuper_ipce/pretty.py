from typing import Any, Dict, Optional

from zuper_commons.text import indent


def pprint(msg=None, **kwargs):
    print(pretty_dict(msg, kwargs))


def pretty_dict(
    head: Optional[str], d: Dict[str, Any], omit_falsy=False, sort_keys=False
):
    if not d:
        return head + ":  (empty dict)" if head else "(empty dict)"
    s = []
    n = max(len(str(_)) for _ in d)

    ordered = sorted(d) if sort_keys else list(d)
    # ks = sorted(d)
    for k in ordered:
        v = d[k]

        prefix = (str(k) + ":").rjust(n + 1) + " "

        if isinstance(v, dict):
            v = pretty_dict("", v)
        s.append(indent(v, "", prefix))

    return (head + ":\n" if head else "") + indent("\n".join(s), "│ ")
