from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml
from nose.tools import assert_equal, raises

from zuper_ipce.ipce import ipce_from_object
from zuper_ipcl import CID, CID_from_object, IPCE, IPCL, LINKS
from zuper_ipcl.constants import LINKS_SELF
from zuper_ipcl.ipcl import ipcl_from_ipce, ipcl_from_object
from zuper_ipcl_tests.test_utils import with_private_register


@dataclass
class Tree:
    data: int
    branches: 'List[Tree]'


def create_tree(nlevels, branching, x) -> Tree:
    if nlevels == 0:
        branches = []
    else:
        branches = []
        for i in range(branching):
            branches.append(create_tree(nlevels - 1, branching, x * (branching + 1) + i + 1))

    return Tree(x, branches)


@dataclass
class TreeDict:
    data: int
    branches: 'Dict[str, TreeDict]'


def create_tree_dict(nlevels, branching, x) -> TreeDict:
    if nlevels == 0:
        branches = {}
    else:
        branches = {}
        for i in range(branching):
            branches[str(i)] = create_tree_dict(nlevels - 1, branching, x * (branching + 1) + i + 1)

    return TreeDict(x, branches)


@dataclass
class Chain:
    data: Any
    next_link: 'Optional[Chain]' = None


def create_chain(nlevels, x):
    if nlevels == 0:
        n = None
    else:
        n = create_chain(nlevels - 1, x + 1)

    return Chain(x, n)


def test_recursive_chain_ipce():
    t = create_chain(100, 0)

    ipce: IPCE = ipce_from_object(t, {})


def test_recursive_ipce():
    n = 6
    t = create_tree(n, 2, 0)
    # print(debug_print(t))
    ipce: IPCE = ipce_from_object(t, {})

#
# async def test_recursive_chain_2():
#     n = 1000
#     t = None
#     for i in range(n):
#         t = Chain(i, t)
#
#     cid: CID = await CID_from_object(t)
#
#     print(f'cid: {cid}')
#     ipcl: IPCL = await ipcl_from_object(t)
#     print(yaml.dump(ipcl))


# @with_private_register
# async def test_recursive_chain_ok():
#     n = 1000
#     # XXX: you should try with 1000 or more
#     n = 100
#     t = None
#     for i in range(n):
#         t = Chain(i, t)
#         cid: CID = await CID_from_object(t)
#         # print(f'iteration {i} -> {cid}')
#
#     cid: CID = await CID_from_object(t)
#
#     print(f'cid: {cid}')
#     ipcl: IPCL = await ipcl_from_object(t)
#     print(yaml.dump(ipcl))


if __name__ == '__main__':
    test_recursive_chain_ipce()
