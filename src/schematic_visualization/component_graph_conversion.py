from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Set, Tuple

import networkx as nx


def collect_comp_net_info(vertices: Iterable) -> Dict[Any, Dict[str, Set[int]]]:
    """
    Traverse vertex-like objects and return a mapping:
        component_obj -> { net_name -> set(pin_indices) }

    Expected minimal vertex interface:
      - vertex.name : str
      - vertex.connections : Mapping[component_obj -> Iterable[int]]
    """
    comp_to_net_info: Dict[Any, Dict[str, Set[int]]] = {}
    for v in vertices:
        net_name = getattr(v, "name", None)
        if net_name is None:
            raise ValueError("Vertex missing 'name' attribute")

        conns: Mapping = getattr(v, "connections", {})
        for comp, pin_indices in conns.items():
            comp_entry = comp_to_net_info.setdefault(comp, {})
            pins = comp_entry.setdefault(net_name, set())
            for idx in pin_indices:
                pins.add(int(idx))
    return comp_to_net_info


def convert_indices_to_pin_names(
    comp_to_net_info: Dict[Any, Dict[str, Set[int]]],
) -> Dict[Any, Dict[str, List[str]]]:
    """
    Convert pin indices to pin names.

    Expects each component object to have:
      - .pins : sequence where .pins[index].name is available

    Returns:
      component_obj -> { net_name -> [pin_name, ...] }
    """
    comp_to_net_pin_names: Dict[Any, Dict[str, List[str]]] = {}
    for comp, net_map in comp_to_net_info.items():
        if not hasattr(comp, "pins"):
            raise ValueError(
                f"Component '{getattr(comp, 'name', comp)}' missing 'pins' attribute"
            )
        pins_list = getattr(comp, "pins")
        comp_pin_map: Dict[str, List[str]] = {}
        for net_name, index_set in net_map.items():
            names: List[str] = []
            for idx in sorted(index_set):
                if not (0 <= idx < len(pins_list)):
                    raise IndexError(
                        f"Pin index {idx} out of range for component {getattr(comp, 'name', comp)}"
                    )
                pin_obj = pins_list[idx]
                pin_name = getattr(pin_obj, "name", None)
                if pin_name is None:
                    # fallback to index string
                    pin_name = str(idx)
                names.append(str(pin_name))
            comp_pin_map[net_name] = names
        comp_to_net_pin_names[comp] = comp_pin_map
    return comp_to_net_pin_names


def build_component_centric_graph(
    vertices: Iterable,
) -> nx.MultiGraph:
    """
    Build a component-centric MultiGraph using *strict star expansion*.

    Nodes:
      - component nodes
      - net hub nodes (one per net)

    Edges:
      - component <-> net hub
      - each edge represents exactly one (component, net) incidence
    """
    comp_to_net_info = collect_comp_net_info(vertices)
    comp_to_pin_names = convert_indices_to_pin_names(comp_to_net_info)

    # net_name -> { component -> [pin_names] }
    net_to_comp_pinmap: Dict[str, Dict[Any, List[str]]] = {}

    for comp, net_map in comp_to_pin_names.items():
        for net_name, pin_names in net_map.items():
            net_to_comp_pinmap.setdefault(net_name, {})[comp] = list(pin_names)

    G = nx.MultiGraph()

    # add component nodes
    for comp in comp_to_net_info.keys():
        comp_name = getattr(comp, "name", str(comp))
        G.add_node(
            comp_name,
            label=comp_name,
            kind="component",
            meta={"obj": comp},
        )

    # add net hubs and incidence edges
    for net_name, comp_pinmap in net_to_comp_pinmap.items():
        comps = list(comp_pinmap.keys())

        if not comps:
            continue

        hub_name = f"__NET__:{net_name}"
        G.add_node(
            hub_name,
            label=net_name,
            kind="net",
            meta={"net": net_name},
        )

        for comp, pin_names in comp_pinmap.items():
            comp_name = getattr(comp, "name", str(comp))
            G.add_edge(
                hub_name,
                comp_name,
                label=net_name,
                kind="net",
                meta={
                    "nets": [net_name],
                    "pin_map": {comp_name: list(pin_names)},
                },
            )

    return G


def _iter_edges_with_data(G: nx.Graph):
    """
    Helper that yields tuples (u, v, key, data) for both Graph and MultiGraph.
    For Graph, key is None.
    """
    if isinstance(G, nx.MultiGraph):
        for u, v, k, data in G.edges(keys=True, data=True):
            yield u, v, k, data
    else:
        for u, v, data in G.edges(data=True):
            yield u, v, None, data


def normalize_graph_contract(G: nx.Graph) -> nx.Graph:
    """
    Ensure the graph follows the domain-neutral contract:

    Node attrs added (if missing):
        - 'label' : str  (defaults to str(node_key))
        - 'kind'  : str  (defaults to 'node')
        - 'meta'  : dict (defaults to {})

    Edge attrs added (if missing):
        - 'label' : str  (defaults to ','.join(meta['nets']) if available else '')
        - 'meta'  : dict (defaults to {})
        - 'kind'  : str  (defaults to 'edge')

    The function mutates and returns the same graph.
    """
    # nodes
    for n, data in G.nodes(data=True):
        if "label" not in data:
            data["label"] = str(n)
        if "kind" not in data:
            data["kind"] = "node"
        if "meta" not in data:
            data["meta"] = {}

    # edges
    for u, v, k, data in _iter_edges_with_data(G):
        if "meta" not in data or data["meta"] is None:
            data["meta"] = {}
        if "label" not in data:
            # try to derive from meta['nets'] if present
            meta = data["meta"]
            nets = meta.get("nets")
            if isinstance(nets, (list, tuple)) and nets:
                try:
                    data["label"] = ",".join(str(x) for x in nets)
                except Exception:
                    data["label"] = str(nets)
            else:
                data["label"] = ""
        if "kind" not in data:
            data["kind"] = "edge"

    return G


def validate_graph_contract(G: nx.Graph) -> Tuple[bool, str]:
    """
    Validate the graph contract *without* mutating the graph.

    Returns (is_valid, message). If is_valid is False, message describes the first problem found.
    Checks that:
      - every node has 'label' (non-empty str), 'kind' (str), 'meta' (dict)
      - every edge has 'label' (non-empty str), 'meta' (dict), 'kind' (str)

    Note: This is a stricter check than normalize_graph_contract. Call normalize_graph_contract
    first if you want defaults to be added.
    """
    # nodes
    for n, data in G.nodes(data=True):
        if "label" not in data:
            return False, f"Node {n!r} missing 'label'"
        if not isinstance(data["label"], str) or data["label"] == "":
            return False, f"Node {n!r} has empty or non-string 'label'"
        if "kind" not in data or not isinstance(data["kind"], str):
            return False, f"Node {n!r} missing or invalid 'kind'"
        if "meta" not in data or not isinstance(data["meta"], dict):
            return False, f"Node {n!r} missing or invalid 'meta'"

    # edges
    for u, v, k, data in _iter_edges_with_data(G):
        if "label" not in data:
            return False, f"Edge {(u, v, k)!r} missing 'label'"
        if not isinstance(data["label"], str) or data["label"] == "":
            return False, f"Edge {(u, v, k)!r} has empty or non-string 'label'"
        if "kind" not in data or not isinstance(data["kind"], str):
            return False, f"Edge {(u, v, k)!r} missing or invalid 'kind'"
        if "meta" not in data or not isinstance(data["meta"], dict):
            return False, f"Edge {(u, v, k)!r} missing or invalid 'meta'"

    return True, "ok"
