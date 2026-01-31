from __future__ import annotations

from itertools import combinations
import pytest

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType
from circuit_elements.core.base.net import Net
from circuit_elements.core.base.schematic import Schematic


class Resistor(BaseComponent):
    def __init__(self, name: str, resistance: float):
        super().__init__(
            name=name, pin_names=["1", "2"], parameters={"resistance": resistance}
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.RESISTOR


@pytest.fixture
def voltage_divider() -> tuple[Schematic, Resistor, Resistor, Net, Net, Net]:
    """
    Build a simple voltage divider:
       VCC -- R1 -- VOUT -- R2 -- GND
    Returns (schematic, r1, r2, vcc, vout, gnd)
    """
    sch = Schematic()

    r1 = Resistor("R1", 10_000)
    r2 = Resistor("R2", 10_000)

    sch.add_component(r1)
    sch.add_component(r2)

    sch.connect_create_net("VCC", "R1", "1")
    sch.connect_create_net("VOUT", "R1", "2")
    sch.connect_create_net("VOUT", "R2", "1")
    sch.connect_create_net("GND", "R2", "2")

    # ensure nets exist and return them
    vcc = sch.net("VCC")
    vout = sch.net("VOUT")
    gnd = sch.net("GND")
    return sch, r1, r2, vcc, vout, gnd


def test_voltage_divider_incidences(voltage_divider):
    sch, r1, r2, vcc, vout, gnd = voltage_divider

    # build incidence list (net, component, pin_index)
    incidences = []
    for net in sch.nets:
        for comp, pin_set in net.connections.items():
            for pin_idx in pin_set:
                incidences.append((net.name, comp.name, pin_idx))

    expected = {
        ("VCC", "R1", 0),
        ("VOUT", "R1", 1),
        ("VOUT", "R2", 0),
        ("GND", "R2", 1),
    }

    assert set(incidences) == expected


def test_bipartite_view(voltage_divider):
    sch, r1, r2, vcc, vout, gnd = voltage_divider

    # nodes: union of net names and component names
    net_names = {net.name for net in sch.nets}
    comp_names = {c.name for c in sch.components}
    nodes = net_names.union(comp_names)

    # edges: (net_name, comp_name, pin_index)
    edges = []
    for net in sch.nets:
        for comp, pin_set in net.connections.items():
            for pin_idx in pin_set:
                edges.append((net.name, comp.name, pin_idx))

    assert "VCC" in net_names and "VOUT" in net_names and "GND" in net_names
    assert "R1" in comp_names and "R2" in comp_names

    # R1 must be adjacent to VCC and VOUT
    r1_adj = {net for net, comp, _ in edges if comp == "R1"}
    assert r1_adj == {"VCC", "VOUT"}

    # VOUT must be adjacent to R1 and R2
    vout_adj = {comp for net, comp, _ in edges if net == "VOUT"}
    assert vout_adj == {"R1", "R2"}


def test_net_to_net_pairs_projection(voltage_divider):
    sch, r1, r2, vcc, vout, gnd = voltage_divider

    # derived net-to-net pairs per component (ordered as frozenset pairs for set equality)
    derived_pairs = set()
    for comp in sch.components:
        nets = {p.net.name for p in comp.pins if p.net is not None}
        if len(nets) < 2:
            continue
        for a, b in combinations(sorted(nets), 2):
            derived_pairs.add((a, b, comp.name))

    expected_pairs = {
        ("VCC", "VOUT", "R1"),
        ("GND", "VOUT", "R2"),
    }

    assert derived_pairs == expected_pairs


def test_incidence_completeness_and_uniqueness(voltage_divider):
    sch, r1, r2, vcc, vout, gnd = voltage_divider

    # every pin of every component must appear exactly once in the incidence list
    incidences = []
    for net in sch.nets:
        for comp, pin_set in net.connections.items():
            for pin_idx in pin_set:
                incidences.append((comp.name, pin_idx))

    # build set of (component_name, pin_index) for all defined component pins
    all_pins = {(c.name, p.index) for c in sch.components for p in c.pins}

    assert set(incidences) == all_pins
