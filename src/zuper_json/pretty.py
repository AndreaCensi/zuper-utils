from typing import Optional, Dict, Any, TypeVar

from contracts import indent


def pprint(msg=None, **kwargs):
    print(pretty_dict(msg, kwargs))


def pretty_dict(head: Optional[str], d: Dict[str, Any], omit_falsy=False, sort_keys=False):
    if not d:
        return head + ':  (empty dict)' if head else '(empty dict)'
    s = []
    n = max(len(str(_)) for _ in d)

    ordered = sorted(d) if sort_keys else list(d)
    # ks = sorted(d)
    for k in ordered:
        v = d[k]

        if k == '__builtins__':
            v = '(hiding __builtins__)'

        if not hasattr(v, 'conclusive') and (not isinstance(v, int)) and (not v) and omit_falsy:
            continue
        prefix = (str(k) + ':').rjust(n + 1) + ' '

        if isinstance(v, TypeVar):
            # noinspection PyUnresolvedReferences
            v = f'TypeVar({v.__name__}, bound={v.__bound__})'
        if isinstance(v, dict):
            v = pretty_dict('', v)
        s.append(indent(v, '', prefix))

    return (head + ':\n' if head else '') + indent("\n".join(s), "│ ")
