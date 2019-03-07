from typing import Iterator, Tuple

from .ipce_constants import LINKS
from zuper_json.json_utils import json_dump
from zuper_json.pretty import pretty_dict
from .register import hash_from_string
from zuper_json.types import MemoryJSON, Hash
from zuper_ipce.constants import CanonicalJSONString


def assert_regular_memory_json(x):
    try:
        if isinstance(x, dict):
            if LINKS in x:
                msg = f'Should have dropped the {LINKS} part.'
                raise ValueError(msg)

            links = set(get_links_hash(x))

            if links:
                msg = f'Should not contain links, found {links}'
                raise ValueError(msg)
    except ValueError as e:
        msg = f'Invalid json compact: \n{json_dump(x)}'
        raise ValueError(msg) from e


def to_canonical_json(x: MemoryJSON) -> MemoryJSON:
    if x is None:
        raise ValueError(x)
    if isinstance(x, list):
        return x
        # msg = f'Lists are not supported yet:\n{x}'
        # raise TypeError(msg)

    if isinstance(x, (int, str, float)):
        return x

    if isinstance(x, dict):

        canonical = {}
        canonical[LINKS] = link_info = {}
        for k, v0 in x.items():
            if v0 is None:
                raise ValueError(f'{k}: {v0}\n{x}')
            # should, allow_recursive = should_abbreviate(x, k, v0)

            v = to_canonical_json(v0)  # , allowed=allow_recursive and allowed)

            # if should and allowed:
            s: CanonicalJSONString = json_dump(v)

            r = hash_from_string(s)

            link_info[r.hash] = r.info
            v = {'/': r.hash}

            canonical[k] = v

        if not canonical[LINKS]:
            canonical.pop(LINKS)

        assert_good_canonical(canonical)
        assert_reconstruct(x, canonical)
        return canonical

    assert False, type(x)  # pragma: no cover


def assert_good_canonical(x):
    assert isinstance(x, dict), x

    keys = list(get_keys(x))

    try:

        # only allow LINKS in first position
        for k in keys:
            if len(k) > 1 and LINKS in k[1:]:
                msg = f'Invalid {LINKS} entry.'
                raise ValueError(msg)

        links = set(get_links_hash(x))

        if links and not LINKS in x:
            msg = f'key {LINKS} not found'
            raise ValueError(msg)
        if LINKS in x:
            found = set(x[LINKS])

            if links != found:
                msg = f'Divergence between links and found.\nlinks: {links}\nfound: {found}'
                raise ValueError(msg)

    except ValueError as e:
        msg = f'Invalid json compact: {e} \n{json_dump(x)}'
        raise ValueError(msg) from e


def assert_reconstruct(original, x):
    from zuper_ipce.register import _substitute
    recon = _substitute(x)
    if recon != original:  # pragma: no cover
        # print(register.pretty_print())
        msg = pretty_dict('Problem', dict(original=original, x=x, recon=recon))
        raise ValueError(msg)


def get_links_hash(x):
    if isinstance(x, dict):
        if '/' in x:
            yield x['/']

        for k, v in x.items():
            yield from get_links_hash(v)
    else:
        return


def get_links_hash_with_prefix(x) -> Iterator[Tuple[Tuple[str, ...], Hash]]:
    if isinstance(x, dict):
        if '/' in x:
            yield (), x['/']

        for k, v in x.items():
            for p, h in get_links_hash_with_prefix(v):
                yield (k,) + p, h
    else:
        return


def get_keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield (k,)
            for _ in get_keys(v):
                yield (k,) + _
    else:
        return
