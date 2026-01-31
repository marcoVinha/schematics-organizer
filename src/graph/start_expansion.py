from __future__ import annotations
from typing import Iterable, List, Iterator
from graph.protocols import VertexLike, Incidence, HypergraphLike


def star_expansion_from_vertices(vertices: Iterable[VertexLike]) -> List[Incidence]:
    """
    Build the star-expansion incidence list from an iterable of VertexLike objects.

    Returns a list of triples (vertex, hyperedge, pin_index), one triple per pin incidence.
    """
    incidences: List[Incidence] = []
    for v in vertices:
        for he, pin_indices in v.connections.items():
            for pin_idx in pin_indices:
                incidences.append((v, he, int(pin_idx)))
    return incidences


def star_expansion(hg: HypergraphLike) -> List[Incidence]:
    """
    Convenience wrapper that accepts a HypergraphLike and delegates to
    `star_expansion_from_vertices`. Keeps the public API explicit about
    working on hypergraph-like objects.
    """
    return star_expansion_from_vertices(hg.vertices)


def star_expansion_iter(vertices: Iterable[VertexLike]) -> Iterator[Incidence]:
    """
    Memory-friendly generator variant yielding incidences one-by-one.
    Useful for very large schematics.
    """
    for v in vertices:
        for he, pin_indices in v.connections.items():
            for pin_idx in pin_indices:
                yield (v, he, int(pin_idx))
