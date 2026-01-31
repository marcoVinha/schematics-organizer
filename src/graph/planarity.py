from __future__ import annotations

import networkx as nx


def is_planar_graph(graph: nx.Graph) -> bool:
    is_planar, _ = nx.check_planarity(graph)

    return is_planar
