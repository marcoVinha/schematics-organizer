from circuit_elements.components.resistor import Resistor
from circuit_elements.components.capacitor import Capacitor
from circuit_elements.components.npn_transistor import NPNTransistor
from circuit_elements.components.potentiometer import Potentiometer

from circuit_elements.core.base.net import Net
from circuit_elements.core.base.schematic import Schematic

from graph.start_expansion import star_expansion_from_vertices
from graph.networkx_utils import (
    build_bipartite_graph_from_vertices,
    build_net_multigraph_from_vertices,
)


def build_common_emitter_amplifier() -> Schematic:
    sch = Schematic()

    # Nets
    vcc = Net("Vcc")
    gnd = Net("GND", is_ground=True)
    input_signal = Net("InputSignal")
    output_signal = Net("OutputSignal")

    sch.add_net(vcc)
    sch.add_net(gnd)
    sch.add_net(input_signal)
    sch.add_net(output_signal)

    # Components
    r1 = Resistor("R1", 10_000)
    r2 = Resistor("R2", 470_000)
    r3 = Resistor("R3", 47_000)
    r4 = Resistor("R4", 390)

    c1 = Capacitor("C1", 22e-9)
    c2 = Capacitor("C2", 10e-6)

    q1 = NPNTransistor("Q1", 458.7, part_number="BC549B")

    pot1 = Potentiometer("VOL", 100_000)

    output_load = Resistor("OutputLoad", float("inf"))

    sch.add_component(r1)
    sch.add_component(r2)
    sch.add_component(r3)
    sch.add_component(r4)
    sch.add_component(c1)
    sch.add_component(c2)
    sch.add_component(q1)
    sch.add_component(pot1)
    sch.add_component(output_load)

    # CONNECTION
    # Vcc: one leg of R1 and R2
    vcc.connect(r1, pin="1")
    vcc.connect(r2, pin="1")

    # GND: one leg of R3, R4 and Output Load
    gnd.connect(r3, pin="2")
    gnd.connect(r4, pin="2")
    gnd.connect(pot1, pin="3")
    gnd.connect(output_load, pin="2")

    # InputSignal: one leg of C1
    input_signal.connect(c1, pin="1")

    # OutputSignal: wiper of VOL, one leg of Output Load
    output_signal.connect(pot1, pin="2")
    output_signal.connect(output_load, pin="1")

    # Base of transistor
    sch.connect_pins(q1, "base", c1, "2")
    sch.connect_pins(q1, "base", r2, "2")
    sch.connect_pins(q1, "base", r3, "1")

    # Collector of transistor
    sch.connect_pins(q1, "collector", r1, "2")
    sch.connect_pins(q1, "collector", c2, "1")

    # emitter of transistor
    sch.connect_pins(q1, "emitter", r4, "1")

    # Remaining legs of pot1
    sch.connect_pins(pot1, "1", c2, "2")

    sch.freeze()

    sch.validate()

    return sch


# ─────────────────────────────────────────────
# Manual inspection
# ─────────────────────────────────────────────

if __name__ == "__main__":
    schematic = build_common_emitter_amplifier()

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
