import json
from typing import Set, Dict, NewType, Any

from IPython.display import Javascript, display, HTML

from .register import get_register, get_links_prefix
from zuper_json.types import Hash


def vis_display(data, element, options):
    jsonGraph = json.dumps(data, indent=4)
    options = json.dumps(options, indent=4)
    s = f"""
    var container = document.getElementById({json.dumps(element)});
    var options = {options};
    var data = {jsonGraph};
    var network = new vis.Network(container, data, options);
    """
    # print(s)
    return Javascript(s)


VisGraph = NewType('VisGraph', Dict[str, Any])


def draw_diagram(data, options=None, css="width: 400px; height: 600px"):
    options = options or {}
    import random
    en = f"network{random.randint(1, 1000)}"
    html = HTML(f'''
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>

    <div id="{en}" style={json.dumps(css)}></div>

''')
    js = vis_display(data, en, options=options)

    display(html, js)


def get_test_diagram() -> VisGraph:
    nodes = [
        {'id': 1, 'label': 'Beyonce', 'group': 'United States'},
        {'id': 2, 'label': 'Barak Obama', 'group': 'United States'},
        {'id': 3, 'label': 'Miley Cyrus', 'group': 'United States'},
        {'id': 4, 'label': 'Pope Francis', 'group': 'Vatican'},
        {'id': 5, 'label': 'Vladimir Putin', 'group': 'Rusia'}
    ]

    edges = [
        {'from': 1, 'to': 2},
        {'from': 1, 'to': 3},
        {'from': 2, 'to': 4},
        {'from': 2, 'to': 5}
    ]
    data: VisGraph = {"nodes": nodes, "edges": edges}
    return data


import networkx as nx


def visjs_from_nx(G: nx.MultiDiGraph, prefix='') -> VisGraph:
    M = 10
    register = get_register()

    def f(x):
        # assert isinstance(x, str), x
        return prefix + str(x)

    SCHEMA_COLOR = 'red'

    nodes = []
    for h, attrs in list(G.nodes.items()):
        level = attrs['depth']
        n = {'id': f(h), 'level': level}
        if level == 0:
            label = register.string_from_hash(h)
            if len(label) > M:
                label = label[:M - 3] + '...'
            n['label'] = label

        its_schema = False
        # is this a schema?
        # yes if it has an attribute $schema that is a string
        successors = G.successors(h)
        for h1 in successors:
            if '$schema' in G[h][h1]:
                s = register.string_from_hash(h1)
                if s == '"http://json-schema.org/draft-07/schema#"':
                    its_schema = True

        if its_schema:
            n['color'] = SCHEMA_COLOR
        nodes.append(n)
    edges = []

    for nfrom, nto, edge_key in G.edges(keys=True):
        e = {'from': f(nfrom), 'to': f(nto), 'label': edge_key}
        if edge_key == '$schema':
            e['color'] = {'color': SCHEMA_COLOR}
        edges.append(e)
        # pass
    data: VisGraph = {'nodes': nodes, 'edges': edges}
    return data


def visualize_objects(heads: Set[Hash]) -> VisGraph:
    register = get_register()
    hs = transitive_closure_without_schema(heads)
    # print(f'found: {hs}')
    G2 = register.G.subgraph(hs)
    return visjs_from_nx(G2)


def transitive_closure_without_schema(heads: Set[Hash]) -> Set[Hash]:
    """
        Traverse to get all the nodes, ignoring schemas.
    """
    # register = get_register()
    open: Set[Hash] = set()
    closed: Set[Hash] = set()
    open.update(heads)

    while open:
        one = open.pop()
        print(one)
        closed.add(one)
        for prefix, h in get_links_prefix(one):
            if prefix != ('$schema',):
                if h not in closed:
                    open.add(h)
    return closed
