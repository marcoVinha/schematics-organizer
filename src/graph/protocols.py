from __future__ import annotations

from typing import FrozenSet, Iterable, Mapping, Protocol, Tuple


class VertexLike(Protocol):
    name: str
    connections: Mapping["HyperedgeLike", FrozenSet[int]]


class HyperedgeLike(Protocol):
    name: str


class HypergraphLike(Protocol):
    @property
    def vertices(self) -> Iterable[VertexLike]: ...


Incidence = Tuple[VertexLike, HyperedgeLike, int]
