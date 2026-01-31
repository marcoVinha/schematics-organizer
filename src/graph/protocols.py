from typing import Protocol, Iterable


class VertexLike(Protocol):
    """Vertexes of a graph."""

    name: str


class HyperedgeLike(Protocol):
    """A hyperedge connects more than two vertexes (unlike normal edges)."""

    name: str


class IncidenceLike(Protocol):
    """Carries info about how the vertex connects to the hyperedge."""

    vertex: VertexLike
    hyperedge: HyperedgeLike


class HypergraphLike(Protocol):
    """
    A hypergraph is a graph with hyperedges, and it can be represented
    by an incidence list telling what vertexes are connected to what
    hyperedges and how they're connected.
    """

    vertices: Iterable[VertexLike]
    hyperedges: Iterable[HyperedgeLike]
    incidences: Iterable[tuple[VertexLike, HyperedgeLike, int]]
