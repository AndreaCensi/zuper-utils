import json
import os
import subprocess
import tempfile
import threading
from abc import abstractmethod, ABCMeta
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Tuple, Dict, Iterator, Optional

import networkx as nx

from zuper_ipce.constants import CanonicalJSONString
from zuper_ipce.ipce_constants import LINKS
from zuper_json.json_utils import json_dump
from zuper_json.pretty import pretty_dict
from zuper_json.types import Hash, MemoryJSON


@dataclass
class HashResult:
    hash: Hash
    info: Dict


class Register(metaclass=ABCMeta):

    @abstractmethod
    def hash_from_string(self, s: CanonicalJSONString) -> HashResult:
        """ """

    @abstractmethod
    def string_from_hash(self, h: Hash) -> CanonicalJSONString:
        """ """


class IPFSDagRegister(Register):

    def hash_from_string(self, s: CanonicalJSONString) -> HashResult:

        fid, fn = tempfile.mkstemp()
        with open(fn, 'w') as f:
            f.write(s)

        cmd = ['ipfs', 'dag', 'put', fn]
        res = subprocess.check_output(cmd)
        res = res.decode()
        h = res.strip()

        try:
            os.unlink(fn)
        except OSError:  # pragma: no cover
            pass
        return HashResult(h, {})

    def string_from_hash(self, h: Hash) -> CanonicalJSONString:
        cmd = ['ipfs', 'dag', 'get', h]
        try:
            # TODO: read standard error
            res = subprocess.check_output(cmd, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            msg = f'Cannot get dag object {h!r}'
            raise KeyError(msg) from e
        res = res.decode()
        return res.strip()


def get_links_prefix(h: Hash) -> Iterator[Tuple[Tuple[str, ...], Hash]]:
    """ Returns the links to other hashes from h. """
    j = string_from_hash(h)
    ob = json.loads(j)
    from .as_json import get_links_hash_with_prefix
    yield from get_links_hash_with_prefix(ob)


def _substitute(x: MemoryJSON) -> MemoryJSON:
    if isinstance(x, dict):
        if '/' in x:
            h = x['/']
            return recall_json(h)

        return {k: _substitute(v) for k, v in x.items()
                if k != LINKS}
    return x


def hash_from_string(s: CanonicalJSONString) -> HashResult:
    register = get_register()
    return register.hash_from_string(s)


def string_from_hash(h: Hash) -> CanonicalJSONString:
    register = get_register()
    return register.string_from_hash(h)


def store_json(x: MemoryJSON) -> Hash:
    from .as_json import to_canonical_json
    cj = to_canonical_json(x)
    s: CanonicalJSONString = json_dump(cj)
    r = hash_from_string(s)
    return r.hash


def recall_json(h: Hash) -> MemoryJSON:
    """
        Reconstruct the original JSON string.
    """
    j = string_from_hash(h)
    ob = json.loads(j)
    res = _substitute(ob)
    from .as_json import assert_regular_memory_json
    assert_regular_memory_json(res)
    return res


import sqlite3


class ConcreteRegister(Register):
    parent: Optional[Register]

    def __init__(self, path='sq.db', parent: Register = None):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

        self._create_schema()
        self._load_graph()
        self.parent = parent
        #
        if not parent:
            raise ValueError()

    def _create_schema(self):
        sql = """

        CREATE TABLE IF NOT EXISTS blobs (
            hash text not null primary key,
            n_links int not null,
            n_nodes int not null, 
            descendants_size int not null,
            depth int not null,
            data text
        );
        
       
            """
        self.cur.execute(sql)
        sql = """
        
         CREATE TABLE IF NOT EXISTS links (
            parent_hash text not null references blobs(hash),
            key VARCHAR(128) not null,
            child_hash text not null references blobs(hash),
            primary key (parent_hash, key, child_hash)
        );

        """
        self.cur.execute(sql)

        sql = """

         CREATE TABLE IF NOT EXISTS links_closure (
            parent_hash text not null references blobs(hash),
            key text not null,
            child_hash text not null references blobs(hash),
            primary key (parent_hash, key, child_hash)
        );

        """
        self.cur.execute(sql)
        self.con.commit()

    def _load_graph(self):
        self.G = nx.MultiDiGraph()
        sql = """
            select hash, n_links, n_nodes, depth, descendants_size from blobs
        """
        self.cur.execute(sql)

        for h, n_links, n_nodes, depth, descendants_size in self.cur.fetchall():
            self.G.add_node(h, n_links=n_links, n_nodes=n_nodes,
                            depth=depth, descendants_size=descendants_size)

        sql = """
            select parent_hash, key, child_hash from links;
        """
        self.cur.execute(sql)
        for parent_hash, key, child_hash in self.cur.fetchall():
            assert parent_hash in self.G
            assert child_hash in self.G

            self.G.add_edge(parent_hash, child_hash, key=key)

        # print(f'Loaded graph with {len(self.G)} nodes')

    def hash_from_string(self, s: CanonicalJSONString) -> HashResult:
        # check first if we already have it
        sql = 'select hash from blobs where data = ?'
        self.cur.execute(sql, (s,))
        found = [_ for _, in self.cur.fetchall()]
        if found:
            # print('can skip')
            h = found[0]
        else:
            hr = self.parent.hash_from_string(s)
            h = hr.hash

        from .as_json import get_links_hash_with_prefix
        j = json.loads(s)

        links = list(get_links_hash_with_prefix(j))

        depth = 0

        for prefix, hchild in links:

            # need to load it
            self.string_from_hash(hchild)

            key = "/".join(prefix)
            sql = """
                INSERT OR IGNORE INTO links (parent_hash, key, child_hash) values (?, ?, ?);
            """
            self.cur.execute(sql, (h, key, hchild))

            sql = """
                INSERT OR IGNORE INTO links_closure (parent_hash, key, child_hash) values (?, ?, ?);
            """
            self.cur.execute(sql, (h, key, hchild))

            sql = """
                SELECT key, child_hash FROM links_closure where parent_hash = ? 
            """
            self.cur.execute(sql, (hchild,))
            for k, cc in self.cur.fetchall():
                sql = """
                insert or ignore into links_closure (parent_hash, key, child_hash) values (?, ?, ?)
                """
                kk = key + '/' + k
                self.cur.execute(sql, (h, kk, cc))

            self.G.add_edge(h, hchild, key=key)

            sql = """
                select depth, length(data) from blobs where hash = ?
            """
            self.cur.execute(sql, (hchild,))
            child_depth, child_blob_size = self.cur.fetchone()
            depth = max(depth, child_depth + 1)

        sql = """
              SELECT child_hash from links_closure where parent_hash = ?
        """
        self.cur.execute(sql, (h,))
        hashes = [_ for _, in self.cur.fetchall()]

        num_descendants = len(hashes)
        num_descendants_unique = len(set(hashes))

        sql = """
            SELECT distinct(blobs.hash), length(data) as l from blobs, links_closure where 
                parent_hash = ? and child_hash = blobs.hash
         """
        self.cur.execute(sql, (h,))
        descendants_size = sum([x for _, x in self.cur.fetchall()])

        # language = sql
        sql = """
            INSERT OR IGNORE INTO blobs (hash, n_links, n_nodes, descendants_size, depth, data) values (?, ?, ?, ?, ?, ?);

        """

        self.cur.execute(sql, (h, num_descendants, num_descendants_unique, descendants_size, depth, s))

        # if True:
        #     if not os.path.exists('tmp'): # pragma: no cover
        #         os.makedirs('tmp')
        #     with open(os.path.join('tmp', h + '.json'), 'w') as f:
        #         f.write(s)

        self.con.commit()

        # add node always, as it might not have children
        self.G.add_node(h, n_links=num_descendants, n_nodes=num_descendants_unique,
                        depth=depth, descendants_size=descendants_size)

        info = {}
        if num_descendants:
            info['n_links'] = num_descendants
        if num_descendants:
            info['n_nodes'] = num_descendants_unique
        if descendants_size:
            info['descendants_size'] = descendants_size
        if depth:
            info['depth'] = depth

        return HashResult(h, info)

    def string_from_hash(self, h: Hash) -> CanonicalJSONString:
        assert isinstance(h, str), h
        sql = """
            SELECT data FROM blobs WHERE hash = ?        
        """
        self.cur.execute(sql, (h,))
        # if not self.cur.rowcount:
        #     msg = f'Could not find hash {h}'
        #     raise KeyError(msg)
        res = self.cur.fetchone()
        if res is None:

            data = self.parent.string_from_hash(h)

            # logger.info(f'obtained data = {data}')
            r = self.hash_from_string(data)
            h2 = r.hash
            assert h == h2, (h, h2)
            return data

            # raise KeyError(msg)
        else:
            data, = res
            return data

    def pretty_print(self) -> str:
        all_data = {}
        sql = """
            SELECT hash, data FROM blobs        
        """
        self.cur.execute(sql)
        for h, data in self.cur.fetchall():
            all_data[h] = data

        return pretty_dict('Register', all_data)


class MyData(threading.local):
    def __init__(self):
        self.stack = []


data = MyData()


def get_register() -> ConcreteRegister:
    if not data.stack:
        msg = 'You did not specify any register. Use "with use_register(register)"'
        raise ValueError(msg)

    return data.stack[-1]


@contextmanager
def use_register(register: ConcreteRegister):
    # print(f'using register {register}')
    push_register(register)
    try:
        yield
    finally:
        pop_register()


def push_register(register):
    data.stack.append(register)


def pop_register():
    data.stack.pop()


def get_cbor_dag_hash(ob):
    """ Returns a base58 string of a CID pointing to ob expressed in CBOR format"""
    import cbor2
    import hashlib
    import multihash
    from cid.cid import make_cid
    ob_cbor = cbor2.dumps(ob)
    ob_cbor_hash = hashlib.sha256(ob_cbor).digest()
    mh = multihash.encode(digest=ob_cbor_hash, code=18)
    # the above returns a bytearray
    mh = bytes(mh)
    cid = make_cid(1, 'dag-cbor', mh)
    return cid.encode().decode('ascii')
