from copy import deepcopy
from typing import Tuple, List, Any, Optional, Generator
from rdflib import Graph as RDFGraph
from graphviz import Digraph

NTuple = Tuple[Any, ...]


class Graph:

    def __init__(self, triples: Optional[List[Tuple[Any, Any, Any]]] = None) -> None:
        self.triples: List[Tuple[Any, Any, Any]] = triples or []

    def clear(self):
        self.triples.clear()

    def append(self, nt: NTuple):
        if not nt in self.triples:
            self.triples.append(nt)

    def match(self, s=None, p=None, o=None):
        for t in self.triples:
            if (not s or t[0] == s) and (not p or t[1] == p) and (not o or t[2] == o):
                yield t

    def parse(self, uri, fmt="ttl"):
        g = RDFGraph().parse(uri, format=fmt)
        for s, p, o in g.triples((None, None, None)):
            self.append((s, p, o))

    def path(self, origin: str, destination: str, predicate_filter: Optional[list[str]] = None, node_avoidance_filter: Optional[list[str]] = None) -> list[list[str]]:
        return [_ for _ in self.recur_find(origin, destination, predicate_filter, node_avoidance_filter)]

    def find(
            self, origin: str, dest: str, predicate_filter: Optional[list[str]] = None, node_avoidance_filter: Optional[list[str]] = None, visited: Optional[list[str]] = None
        ) -> tuple[list[str], list[str], bool]:
            if origin == dest:
                visited.append(origin)
                return [], visited, True
            if not visited:
                visited=[]

            visited.append(origin)
            to_visit = []    
            for s, p, o in self.match(origin, None, None):   
                if (
                    predicate_filter is None or p in predicate_filter
                ) and (
                    node_avoidance_filter is None or o not in node_avoidance_filter
                ) and o not in visited:
                    to_visit.append(o)

            for s, p, o in self.match(None, None, origin):
                if (
                    predicate_filter is None or p in predicate_filter
                ) and (
                    node_avoidance_filter is None or s not in node_avoidance_filter
                ) and s not in visited:
                    to_visit.append(s)

            return to_visit, visited, False

    def recur_find(
        self, origin: str, dest: str, predicate_filter: Optional[list[str]] = None, node_avoidance_filter: Optional[list[str]] = None, visited: Optional[list[str]] = None
    ) -> Generator[list[str], None, None]:
        if origin == dest:
            visited.append(origin)
            yield visited
        else:
            to_visit, new_visited, found = self.find(origin, dest, predicate_filter, node_avoidance_filter, visited)
            for p in to_visit:        
                yield from self.recur_find(p, dest, predicate_filter, node_avoidance_filter, deepcopy(new_visited)) 

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
