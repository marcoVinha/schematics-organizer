from __future__ import annotations

import pytest

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType
from circuit_elements.core.base.net import Net
from circuit_elements.core.base.schematic import Schematic


class DummyComponent(BaseComponent):
    @property
    def type(self) -> ComponentType:
        return ComponentType.IC


# ─────────────────────────────────────────────
# Existing Net / Component tests (unchanged)
# ─────────────────────────────────────────────


def test_component_requires_at_least_one_pin():
    with pytest.raises(ValueError):
        DummyComponent("X1", [])


def test_component_creates_named_pins():
    c = DummyComponent("X1", ["A", "B", "C"])

    assert [p.name for p in c.pins] == ["A", "B", "C"]
    assert [p.index for p in c.pins] == [0, 1, 2]


def test_duplicate_pin_names_are_rejected():
    with pytest.raises(ValueError):
        DummyComponent("X1", ["A", "A"])


def test_pin_lookup_by_name():
    c = DummyComponent("X1", ["D", "S", "G"])
    assert c.pin("G") is c.pins[2]


def test_pin_lookup_invalid_name():
    c = DummyComponent("X1", ["A", "B"])
    with pytest.raises(KeyError):
        c.pin("C")


def test_net_initial_state():
    n = Net("N1")
    assert n.degree == 0
    assert n.connections == {}
    assert n.is_ground is False


def test_ground_net_flag():
    gnd = Net("GND", is_ground=True)
    assert gnd.is_ground is True


def test_connect_by_pin_index():
    c = DummyComponent("X1", ["A", "B"])
    n = Net("N1")
    n.connect(c, 0)
    assert c.pins[0].net is n
    assert c.pins[1].net is None
    assert n.degree == 1
    assert 0 in n.connections[c]


def test_connect_by_pin_name():
    c = DummyComponent("X1", ["D", "S", "G"])
    n = Net("N1")
    n.connect(c, "G")
    assert c.pin("G").net is n
    assert n.degree == 1
    assert n.connections[c] == frozenset({2})


def test_iadd_operator():
    c = DummyComponent("X1", ["A", "B"])
    n = Net("N1")
    n += (c, "A")
    assert c.pin("A").net is n
    assert n.degree == 1


def test_cannot_connect_same_pin_twice():
    c = DummyComponent("X1", ["A"])
    n1 = Net("N1")
    n2 = Net("N2")
    n1.connect(c, "A")
    with pytest.raises(ValueError):
        n2.connect(c, "A")


def test_invalid_pin_index():
    c = DummyComponent("X1", ["A", "B"])
    n = Net("N1")
    with pytest.raises(IndexError):
        n.connect(c, 10)


def test_multiple_pins_same_component_same_net():
    c = DummyComponent("X1", ["A", "B", "C"])
    n = Net("N1")
    n.connect(c, "A")
    n.connect(c, "B")
    assert n.degree == 2
    assert c.pin("A").net is n
    assert c.pin("B").net is n
    assert n.connections[c] == frozenset({0, 1})


def test_connections_are_read_only_snapshot():
    c = DummyComponent("X1", ["A"])
    n = Net("N1")
    n.connect(c, "A")
    snapshot = n.connections
    with pytest.raises(AttributeError):
        snapshot[c].add(1)


def test_component_connected_nets():
    c = DummyComponent("X1", ["A", "B"])
    n1 = Net("N1")
    n2 = Net("N2")
    n1.connect(c, "A")
    n2.connect(c, "B")
    nets = list(c.connected_nets())
    assert set(nets) == {n1, n2}


def test_component_type_is_enum():
    c = DummyComponent("X1", ["A"])
    assert isinstance(c.type, ComponentType)
    assert c.type is ComponentType.IC


def test_repr_does_not_crash():
    c = DummyComponent("X1", ["A", "B"])
    n = Net("N1")
    n.connect(c, "A")
    assert isinstance(repr(c), str)
    assert isinstance(repr(n), str)


# ─────────────────────────────────────────────
# New Schematic-level tests (connect_pins, auto-nets, merges)
# ─────────────────────────────────────────────


def test_connect_pins_creates_auto_net_when_both_unconnected():
    sch = Schematic()
    a = DummyComponent("R1", ["1", "2"])
    b = DummyComponent("R2", ["1", "2"])

    sch.add_component(a)
    sch.add_component(b)

    net = sch.connect_pins(a, "2", b, "1")  # object args
    assert net is not None
    assert net.name.startswith("N$")
    # net must be registered in schematic
    assert any(n.name == net.name for n in sch.nets)
    # pins must reference the created net
    assert a.pin("2").net is net
    assert b.pin("1").net is net


def test_connect_pins_accepts_names_and_objects_and_attaches_to_existing_net():
    sch = Schematic()
    a = DummyComponent("R1", ["1", "2"])
    b = DummyComponent("R2", ["1", "2"])

    sch.add_component(a)
    sch.add_component(b)
    # create a named net first
    sch.add_net(Net("VCC"))
    sch.connect("VCC", "R1", "1")  # connect by names
    # attach b by using connect_pins mixing name and object
    net = sch.connect_pins("R1", "1", b, "2")  # first arg is component name
    assert net.name == "VCC"
    assert a.pin("1").net is net
    assert b.pin("2").net is net


def test_connect_pins_requires_explicit_merge_for_different_nets():
    sch = Schematic()
    a = DummyComponent("R1", ["1", "2"])
    b = DummyComponent("R2", ["1", "2"])

    sch.add_component(a)
    sch.add_component(b)

    sch.add_net(Net("N_A"))
    sch.add_net(Net("N_B"))

    sch.connect("N_A", "R1", "1")
    sch.connect("N_B", "R2", "1")

    # attempting to connect pins on different nets without allow_merge should raise
    with pytest.raises(ValueError):
        sch.connect_pins("R1", "1", "R2", "1")

    # explicit merge allowed
    merged_net = sch.connect_pins("R1", "1", "R2", "1", allow_merge=True)
    assert merged_net is not None
    # after merge, both pins must reference the merged net
    assert a.pin("1").net is merged_net
    assert b.pin("1").net is merged_net
    # net name should be the target net's name (first pin's net before merge)
    assert merged_net.name in {n.name for n in sch.nets}


def test_connect_create_net_convenience_and_duplicate_net_error():
    sch = Schematic()
    c = DummyComponent("X1", ["A"])
    sch.add_component(c)

    # connect_create_net should create net and connect in one call
    sch.connect_create_net("AUTO1", "X1", "A")
    assert sch.net("AUTO1").connections  # non-empty

    # adding the same net twice raises
    with pytest.raises(ValueError):
        sch.add_net(Net("AUTO1"))


def test_connect_pins_unregistered_component_raises():
    sch = Schematic()
    a = DummyComponent("R1", ["1", "2"])
    b = DummyComponent("R2", ["1", "2"])
    sch.add_component(a)
    # do not add b
    with pytest.raises(KeyError):
        sch.connect_pins(a, "1", b, "1")
