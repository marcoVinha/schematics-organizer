from __future__ import annotations

from .net import Net


class Pin:
    def __init__(self, index: int, name: str | None = None):
        self.index = index
        self.name = name
        self.net: Net | None = None

    def __repr__(self) -> str:
        return f"<Pin {self.name} -> {self.net.name if self.net else 'NC'}>"
