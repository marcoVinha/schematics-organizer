from itertools import combinations
from typing import Iterable

import networkx as nx


def build_bipartite_graph_from_vertices(vertices: Iterable) -> nx.MultiGraph:
    """
    Build a bipartite MultiGraph from an iterable of Net-like vertices.

    - net nodes are added with node attribute: kind='net', obj=net
    - component nodes are added with node attribute: kind='component', obj=component
    - edges connect net.name <-> component.name, with edge attrs: pin_index, net_obj, comp_obj
    Using MultiGraph allows multiple pins connecting the same net/component to create distinct edges.
    """
    graph = nx.MultiGraph()
    for net in vertices:
        net_id = getattr(net, "name", net)  # accept str or object with name
        graph.add_node(
            net_id, kind="net", obj=net, is_ground=getattr(net, "is_ground", False)
        )

        for comp, pin_set in net.connections.items():
            comp_id = getattr(comp, "name", comp)
            if comp_id not in graph:
                graph.add_node(comp_id, kind="component", obj=comp)
            for pin_idx in pin_set:
                graph.add_edge(
                    net_id, comp_id, pin_index=int(pin_idx), net_obj=net, comp_obj=comp
                )
    return graph


def build_net_multigraph_from_vertices(vertices: Iterable) -> nx.MultiGraph:
    """
    Build a projected MultiGraph on nets (nodes = net.name).
    For each component, emit an edge for every unordered pair of *distinct* nets it touches.
    Edge attributes: component (object), component_name (str), nets (tuple of names), pin_map (mapping).
    """
    multi_graph = nx.MultiGraph()
    # ensure all nets are nodes (so isolated nets appear)
    for net in vertices:
        net_id = getattr(net, "name", net)
        multi_graph.add_node(
            net_id, obj=net, is_ground=getattr(net, "is_ground", False)
        )

    # Build per-component net-sets and pin mappings
    comp_to_nets = {}
    for net in vertices:
        for comp, pin_set in net.connections.items():
            comp_to_nets.setdefault(comp, {}).setdefault(net, set()).update(pin_set)

    # For each component, create edges between every unordered pair of nets it touches
    for comp, net_map in comp_to_nets.items():
        nets = list(net_map.keys())
        if len(nets) < 2:
            continue
        comp_name = getattr(comp, "name", comp)
        for a, b in combinations(nets, 2):
            a_id, b_id = getattr(a, "name", a), getattr(b, "name", b)
            # pin map for this particular pair (useful metadata)
            pin_map = {
                a_id: frozenset(net_map[a]),
                b_id: frozenset(net_map[b]),
            }
            multi_graph.add_edge(
                a_id,
                b_id,
                component=comp,
                component_name=comp_name,
                nets=(a_id, b_id),
                pin_map=pin_map,
            )
    return multi_graph
