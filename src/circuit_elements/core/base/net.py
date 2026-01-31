from __future__ import annotations

from typing import Any


class Net:
    def __init__(
        self,
        name: str,
        is_ground: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        self.name = name
        self.is_ground = is_ground
        self.metadata = metadata or {}
        self._connections: dict[Any, set[int]] = {}

    def connect(self, component: Any, pin: int | str) -> None:
        if isinstance(pin, str):
            p = component.pin(pin)
        else:
            if not (0 <= pin < len(component.pins)):
                raise IndexError(f"Pin index {pin} out of range for {component.name}")
            p = component.pins[pin]

        if p.net is not None:
            raise ValueError(f"Pin {p.name} already connected to net {p.net.name}")

        self._connections.setdefault(component, set()).add(p.index)
        p.net = self

    def __iadd__(self, other):
        try:
            component, pin = other
        except Exception:
            raise TypeError("Use `net += (component, pin)`")
        self.connect(component, pin)
        return self

    @property
    def connections(self) -> dict[Any, set[int]]:
        return {c: frozenset(p) for c, p in self._connections.items()}

    @property
    def degree(self) -> int:
        return sum(len(p) for p in self._connections.values())

    def __repr__(self) -> str:
        conns = ", ".join(f"{c.name}:{sorted(p)}" for c, p in self._connections.items())
        return f"<Net {self.name} degree={self.degree} [{conns}]>"
