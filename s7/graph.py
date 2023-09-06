"""Graph"""
from copy import deepcopy
from typing import Any, Generator, List, Optional, Tuple

from graphviz import Digraph
from rdflib import Graph as RDFGraph

Triple = Tuple[Any, Any, Any]


class Graph:
    """RDF Triple Graph."""

    def __init__(self, triples: Optional[List[Triple]] = None) -> None:
        self.triples: List[Triple] = triples or []

    def clear(self):
        """Clear graph."""
        self.triples.clear()

    def append(self, triple: Triple):
        """Add an RDF triple."""
        if triple not in self.triples:
            self.triples.append(triple)

    def match(self, s=None, p=None, o=None):
        """Yield all matching triples."""
        for triple in self.triples:
            if (
                (not s or triple[0] == s)
                and (not p or triple[1] == p)
                and (not o or triple[2] == o)
            ):
                yield triple

    def parse(self, uri, fmt="ttl"):
        """Create Graph from an ontology file."""
        graph = RDFGraph().parse(uri, format=fmt)
        for triple in graph.triples(  # pylint: disable=not-an-iterable
            (None, None, None)
        ):
            self.append(triple)

    def path(
        self,
        origin: str,
        destination: str,
        predicate_filter: Optional[list[str]] = None,
        node_avoidance_filter: Optional[list[str]] = None,
    ) -> list[list[str]]:
        """Return all graph traversal paths between `origin` and `destination`."""
        return list(
            self.recur_find(
                origin, destination, predicate_filter, node_avoidance_filter
            )
        )

    def find(
        self,
        origin: str,
        dest: str,
        predicate_filter: Optional[list[str]] = None,
        node_avoidance_filter: Optional[list[str]] = None,
        visited: Optional[list[str]] = None,
    ) -> tuple[list[str], list[str], bool]:
        """Find path from `origin` to `dest`, used mainly by `recur_find`."""
        if visited and origin == dest:
            visited.append(origin)
            return [], visited, True
        if not visited:
            visited = []

        visited.append(origin)
        to_visit = []
        for s, p, o in self.match(origin, None, None):
            if (
                (predicate_filter is None or p in predicate_filter)
                and (node_avoidance_filter is None or o not in node_avoidance_filter)
                and o not in visited
            ):
                to_visit.append(o)

        for s, p, o in self.match(None, None, origin):
            if (
                (predicate_filter is None or p in predicate_filter)
                and (node_avoidance_filter is None or s not in node_avoidance_filter)
                and s not in visited
            ):
                to_visit.append(s)

        return to_visit, visited, False

    def recur_find(
        self,
        origin: str,
        dest: str,
        predicate_filter: Optional[list[str]] = None,
        node_avoidance_filter: Optional[list[str]] = None,
        visited: Optional[list[str]] = None,
    ) -> Generator[list[str], None, None]:
        """Recursively find path from `origin` to `dest`."""
        if visited and origin == dest:
            visited.append(origin)
            yield visited
        else:
            to_visit, new_visited, _ = self.find(  # _ is "found"
                origin, dest, predicate_filter, node_avoidance_filter, visited
            )
            for p in to_visit:
                yield from self.recur_find(
                    p,
                    dest,
                    predicate_filter,
                    node_avoidance_filter,
                    deepcopy(new_visited),
                )

    def plot(self):
        """
        Create Digraph plot
        """
        dot = Digraph("wide")
        # Add nodes 1 and 2
        for s, p, o in self.match():
            dot.node(str(s), color="lightgrey", style="filled")
            dot.node(str(o), color="lightgrey", style="filled")
            dot.edge(str(s), str(o), label=p)

        # Visualize the graph
        return dot
