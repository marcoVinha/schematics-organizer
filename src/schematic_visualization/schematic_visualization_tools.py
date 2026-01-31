from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx

from graph.networkx_utils import build_net_multigraph_from_vertices


def _draw_net_multigraph(G: nx.MultiGraph, *, save_path: Optional[str]) -> None:
    """
    Draw a net-projected MultiGraph: nodes are nets, edges are components (annotated).
    Uses a force layout; if planar, uses planar_layout by request.
    """
    # Choose layout: favor planar_layout when graph is planar
    pos = None
    try:
        is_planar, _ = nx.check_planarity(G)
        if is_planar:
            pos = nx.planar_layout(G)
    except Exception:
        pos = None

    if pos is None:
        pos = nx.spring_layout(G, k=0.8)

    fig, ax = plt.subplots(figsize=(10, 6))

    nx.draw_networkx_nodes(G, pos, node_color="#8ecae6", node_size=1000, ax=ax)
    nx.draw_networkx_edges(G, pos, ax=ax)

    nx.draw_networkx_labels(G, pos, font_size=9, ax=ax)

    # Annotate edges with rich labels including component name + pin_map (which pin(s) attach to each net)
    # For MultiGraph get_edge_attributes returns dict keyed (u,v,key)
    edge_labels = nx.get_edge_attributes(G, "component_name")
    if edge_labels:
        # Build a mapping (u,v) -> [label_for_each_parallel_edge]
        consolidated = {}

        # Iterate over all edges with data to access pin_map and component_name together
        for u, v, key, data in G.edges(keys=True, data=True):
            comp_name = data.get("component_name", str(data.get("component", "")))
            pin_map = data.get("pin_map")  # expected: { net_name: frozenset([...]) }

            if pin_map:
                # Create short "net:pinlist" pieces sorted by net name for determinism
                parts = []
                for net_name in sorted(pin_map.keys()):
                    pins = sorted(map(int, pin_map[net_name]))
                    pins_str = ",".join(str(p) for p in pins)
                    parts.append(f"{net_name}:{pins_str}")
                label = f"{comp_name} ({'; '.join(parts)})"
            else:
                # Fallback to just the component name
                label = comp_name

            # Use unordered key (u,v) so both directions map to same edge label location
            edge_key = (u, v)
            consolidated.setdefault(edge_key, []).append(label)

        # Turn lists of parallel-edge labels into a single string per (u,v)
        consolidated = {k: "\n".join(v) for k, v in consolidated.items()}

        # Draw labels
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=consolidated, font_size=8, ax=ax
        )

    ax.set_axis_off()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved net-graph visualization to {save_path}")


from typing import Iterable, Union

# import your builders / drawing helpers
from schematic_visualization.component_graph_conversion import (
    build_component_centric_graph,
)


def visualize_schematic(
    vertices_or_graph: Union[Iterable, nx.Graph],
    *,
    view: str = "nets",  # "nets" or "components"
    save_path: Optional[str] = None,
) -> None:
    """
    Accept either:
      - an iterable of VertexLike objects (your previous API), or
      - a ready-to-plot networkx.Graph / MultiGraph.

    If a graph is passed, use it directly. If vertex-like objects are passed,
    build the requested view's graph first.
    """
    # -------------------------
    # New: detect if argument is already a NetworkX graph
    # -------------------------
    if isinstance(vertices_or_graph, nx.Graph):
        G = vertices_or_graph
    else:
        # treat as vertices iterable and build the requested graph
        if view == "components":
            G = build_component_centric_graph(vertices_or_graph)
        else:
            G = build_net_multigraph_from_vertices(vertices_or_graph)
    # -------------------------

    # draw using your existing drawing function (which expects a networkx graph)
    _draw_net_multigraph(G, save_path=save_path)
