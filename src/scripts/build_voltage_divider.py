from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType
from circuit_elements.core.base.net import Net
from circuit_elements.core.base.schematic import Schematic

from graph.start_expansion import star_expansion_from_vertices
from graph.networkx_utils import (
    build_bipartite_graph_from_vertices,
    build_net_multigraph_from_vertices,
)


# ─────────────────────────────────────────────
# Concrete component: Resistor
# ─────────────────────────────────────────────


class Resistor(BaseComponent):
    def __init__(self, name: str, resistance_ohm: float):
        super().__init__(
            name=name,
            pin_names=["1", "2"],
            parameters={"resistance": resistance_ohm},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.RESISTOR


# ─────────────────────────────────────────────
# Build a voltage divider
#
#   VCC ── R1 ──┬── VOUT
#               |
#              R2
#               |
#              GND
# ─────────────────────────────────────────────


def build_voltage_divider() -> Schematic:
    sch = Schematic()

    # Nets
    vcc = Net("VCC")
    vout = Net("VOUT")
    gnd = Net("GND", is_ground=True)

    sch.add_net(vcc)
    sch.add_net(vout)
    sch.add_net(gnd)

    # Components
    r1 = Resistor("R1", 10_000)
    r2 = Resistor("R2", 10_000)

    sch.add_component(r1)
    sch.add_component(r2)

    # Connections
    # R1: VCC → VOUT
    vcc.connect(r1, "1")
    vout.connect(r1, "2")

    # R2: VOUT → GND
    vout.connect(r2, "1")
    gnd.connect(r2, "2")

    sch.freeze()
    return sch


# ─────────────────────────────────────────────
# Manual inspection
# ─────────────────────────────────────────────

if __name__ == "__main__":
    schematic = build_voltage_divider()

    print(schematic)

    print("\nNets:")
    for net in schematic.nets:
        print(f"  {net}")

    print("\nComponents:")
    for comp in schematic.components:
        print(f"  {comp}")
        for pin in comp.pins:
            print(f"    {pin}")

    incidences = star_expansion_from_vertices(schematic.nets)

    for v, comp, pin in incidences:
        print(f"({v.name}, {comp.name}, pin_index={pin})")

    bipartite_graph = build_bipartite_graph_from_vertices(schematic.nets)
    print("Bipartite nodes:", bipartite_graph.nodes(data=True))
    print("Bipartite edges:", list(bipartite_graph.edges(data=True)))

    multi_graph = build_net_multigraph_from_vertices(schematic.nets)
    print("Net multigraph nodes:", multi_graph.nodes(data=True))
    print("Net multigraph edges:", list(multi_graph.edges(data=True)))
