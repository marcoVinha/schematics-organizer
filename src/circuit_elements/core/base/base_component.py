from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator

from .component_type import ComponentType
from .net import Net
from .pin import Pin


class BaseComponent(ABC):
    def __init__(
        self,
        name: str,
        pin_names: list[str],
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if not pin_names:
            raise ValueError("Component must have at least one pin")

        self.name = name
        self.parameters = parameters or {}

        self.pins: list[Pin] = [Pin(i, pn) for i, pn in enumerate(pin_names)]
        self._pin_by_name: dict[str, Pin] = {p.name: p for p in self.pins}

        if len(self._pin_by_name) != len(self.pins):
            raise ValueError("Duplicate pin names are not allowed")

    def pin(self, name: str) -> Pin:
        try:
            return self._pin_by_name[name]
        except KeyError:
            raise KeyError(f"Component {self.name} has no pin named '{name}'")

    @property
    @abstractmethod
    def type(self) -> ComponentType: ...

    def connected_nets(self) -> Iterator[Net]:
        return (p.net for p in self.pins if p.net is not None)

    def __repr__(self) -> str:
        pin_state = ", ".join(
            f"{p.index}:{p.net.name if p.net else 'NC'}" for p in self.pins
        )
        return f"<{self.__class__.__name__} {self.name} [{pin_state}]>"
