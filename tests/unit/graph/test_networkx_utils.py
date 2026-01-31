from __future__ import annotations

import networkx as nx

from graph.networkx_utils import (
    build_bipartite_graph_from_vertices,
    build_net_multigraph_from_vertices,
)


# -------------------------
# Minimal protocol-satisfying fakes
# -------------------------


class FakeComponent:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<FakeComponent {self.name}>"


class FakeNet:
    """
    Minimal object matching the VertexLike protocol used by the builders:
      - .name : str
      - .is_ground : bool (optional, used as node attribute)
      - .connections : mapping FakeComponent -> iterable of pin indices (frozenset preferred)
    """

    def __init__(self, name: str, is_ground: bool = False):
        self.name = name
        self.is_ground = is_ground
        self.connections: dict[FakeComponent, frozenset[int]] = {}

    def connect(self, comp: FakeComponent, *pin_indices: int):
        """Convenience helper for tests to populate .connections"""
        s = set(self.connections.get(comp, frozenset()))
        for idx in pin_indices:
            s.add(int(idx))
        self.connections[comp] = frozenset(s)

    def __repr__(self):
        return f"<FakeNet {self.name}>"


# -------------------------
# Tests for bipartite builder
# -------------------------


def test_bipartite_graph_nodes_and_kinds_using_fakes():
    n1 = FakeNet("N1")
    n2 = FakeNet("N2")
    comp = FakeComponent("C1")

    n1.connect(comp, 0)
    n2.connect(comp, 1)

    G = build_bipartite_graph_from_vertices([n1, n2])

    assert set(G.nodes) == {"N1", "N2", "C1"}
    assert G.nodes["N1"]["kind"] == "net"
    assert G.nodes["N2"]["kind"] == "net"
    assert G.nodes["C1"]["kind"] == "component"


def test_bipartite_graph_edges_have_pin_index_using_fakes():
    n1 = FakeNet("N1")
    comp = FakeComponent("C1")

    n1.connect(comp, 0)

    G = build_bipartite_graph_from_vertices([n1])

    edges = list(G.edges(data=True))
    assert len(edges) == 1

    u, v, data = edges[0]
    assert {u, v} == {"N1", "C1"}
    assert data["pin_index"] == 0
    # ensure the obj attributes reference the original test objects
    assert data["net_obj"] is n1
    assert data["comp_obj"] is comp


def test_bipartite_allows_multiple_edges_same_net_component_using_fakes():
    n1 = FakeNet("N1")
    comp = FakeComponent("C1")

    # two different pins of the same component attached to the same net
    n1.connect(comp, 0)
    n1.connect(comp, 1)

    G = build_bipartite_graph_from_vertices([n1])

    assert isinstance(G, nx.MultiGraph)
    assert G.number_of_edges("N1", "C1") == 2


def test_bipartite_includes_isolated_net_using_fakes():
    n1 = FakeNet("N1")
    n2 = FakeNet("N2")  # isolated net, no connections

    G = build_bipartite_graph_from_vertices([n1, n2])

    assert "N2" in G.nodes
    assert G.degree("N2") == 0


# -------------------------
# Tests for net multigraph builder
# -------------------------


def test_net_multigraph_simple_two_pin_component_using_fakes():
    vcc = FakeNet("VCC")
    gnd = FakeNet("GND")
    r1 = FakeComponent("R1")

    vcc.connect(r1, 0)
    gnd.connect(r1, 1)

    MG = build_net_multigraph_from_vertices([vcc, gnd])

    assert isinstance(MG, nx.MultiGraph)
    assert set(MG.nodes) == {"VCC", "GND"}
    assert MG.number_of_edges("VCC", "GND") == 1

    # get the data from the first (and only) edge
    edge_data = list(MG.edges(data=True))[0][2]
    assert edge_data["component"] is r1
    assert edge_data["component_name"] == "R1"
    assert edge_data["nets"] == ("VCC", "GND")
    assert "pin_map" in edge_data and "VCC" in edge_data["pin_map"]


def test_net_multigraph_component_with_more_than_two_pins_using_fakes():
    n1 = FakeNet("N1")
    n2 = FakeNet("N2")
    n3 = FakeNet("N3")

    u1 = FakeComponent("U1")

    n1.connect(u1, 0)
    n2.connect(u1, 1)
    n3.connect(u1, 2)

    MG = build_net_multigraph_from_vertices([n1, n2, n3])

    # for three nets, we expect 3 unordered pairs (3 edges)
    assert MG.number_of_edges() == 3

    expected_pairs = {
        frozenset(("N1", "N2")),
        frozenset(("N1", "N3")),
        frozenset(("N2", "N3")),
    }

    actual_pairs = {frozenset((u, v)) for u, v in MG.edges()}
    assert actual_pairs == expected_pairs


def test_net_multigraph_parallel_edges_for_multiple_components_using_fakes():
    n1 = FakeNet("N1")
    n2 = FakeNet("N2")

    r1 = FakeComponent("R1")
    r2 = FakeComponent("R2")

    n1.connect(r1, 0)
    n2.connect(r1, 1)

    n1.connect(r2, 0)
    n2.connect(r2, 1)

    MG = build_net_multigraph_from_vertices([n1, n2])

    assert MG.number_of_edges("N1", "N2") == 2

    component_names = {data["component_name"] for _, _, data in MG.edges(data=True)}
    assert component_names == {"R1", "R2"}


def test_net_multigraph_ignores_single_net_components_using_fakes():
    n1 = FakeNet("N1")
    r1 = FakeComponent("R1")

    n1.connect(r1, 0)

    MG = build_net_multigraph_from_vertices([n1])

    # no edges should be created because the single-pin component touches only one net
    assert MG.number_of_edges() == 0
    assert "N1" in MG.nodes
