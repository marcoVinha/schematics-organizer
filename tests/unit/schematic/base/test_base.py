from __future__ import annotations

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType
from circuit_elements.core.base.net import Net
import pytest



class DummyComponent(BaseComponent):
    @property
    def type(self) -> ComponentType:
        return ComponentType.IC


# ─────────────────────────────────────────────
# Component / Pin construction
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


# ─────────────────────────────────────────────
# Pin lookup
# ─────────────────────────────────────────────


def test_pin_lookup_by_name():
    c = DummyComponent("X1", ["D", "S", "G"])

    assert c.pin("G") is c.pins[2]


def test_pin_lookup_invalid_name():
    c = DummyComponent("X1", ["A", "B"])

    with pytest.raises(KeyError):
        c.pin("C")


# ─────────────────────────────────────────────
# Net construction
# ─────────────────────────────────────────────


def test_net_initial_state():
    n = Net("N1")

    assert n.degree == 0
    assert n.connections == {}
    assert n.is_ground is False


def test_ground_net_flag():
    gnd = Net("GND", is_ground=True)

    assert gnd.is_ground is True


# ─────────────────────────────────────────────
# Connectivity
# ─────────────────────────────────────────────


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


# ─────────────────────────────────────────────
# Illegal connections
# ─────────────────────────────────────────────


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


# ─────────────────────────────────────────────
# Multiple pins on same net
# ─────────────────────────────────────────────


def test_multiple_pins_same_component_same_net():
    c = DummyComponent("X1", ["A", "B", "C"])
    n = Net("N1")

    n.connect(c, "A")
    n.connect(c, "B")

    assert n.degree == 2
    assert c.pin("A").net is n
    assert c.pin("B").net is n
    assert n.connections[c] == frozenset({0, 1})


# ─────────────────────────────────────────────
# Snapshot immutability
# ─────────────────────────────────────────────


def test_connections_are_read_only_snapshot():
    c = DummyComponent("X1", ["A"])
    n = Net("N1")

    n.connect(c, "A")
    snapshot = n.connections

    with pytest.raises(AttributeError):
        snapshot[c].add(1)


# ─────────────────────────────────────────────
# Component helpers
# ─────────────────────────────────────────────


def test_component_connected_nets():
    c = DummyComponent("X1", ["A", "B"])
    n1 = Net("N1")
    n2 = Net("N2")

    n1.connect(c, "A")
    n2.connect(c, "B")

    nets = list(c.connected_nets())
    assert set(nets) == {n1, n2}


# ─────────────────────────────────────────────
# Enum usage
# ─────────────────────────────────────────────


def test_component_type_is_enum():
    c = DummyComponent("X1", ["A"])

    assert isinstance(c.type, ComponentType)
    assert c.type is ComponentType.IC


# ─────────────────────────────────────────────
# Repr sanity
# ─────────────────────────────────────────────


def test_repr_does_not_crash():
    c = DummyComponent("X1", ["A", "B"])
    n = Net("N1")

    n.connect(c, "A")

    assert isinstance(repr(c), str)
    assert isinstance(repr(n), str)
