from __future__ import annotations

from typing import Callable, Optional

import matplotlib.pyplot as plt
import networkx as nx


def save_graph_visualization(
    G: nx.Graph,
    *,
    layout: Optional[Callable[[nx.Graph], dict]] = None,
    with_labels: bool = True,
    node_size: int = 1200,
    font_size: int = 10,
    save_path: Optional[str] = None,
) -> None:
    if layout is None:
        layout = nx.spring_layout

    pos = layout(G)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1)

    nx.draw(
        G,
        pos,
        with_labels=with_labels,
        node_size=node_size,
        font_size=font_size,
        ax=ax,
    )

    # draw edge labels if present
    edge_labels = nx.get_edge_attributes(G, "component_name")
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    ax.set_axis_off()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Graph saved to {save_path}")

        fallback_path = save_path or "graph.png"
        if not save_path:
            fig.savefig(fallback_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
