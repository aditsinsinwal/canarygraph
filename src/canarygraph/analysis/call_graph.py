"""Function-level directed graph with blast-radius-oriented queries."""

from __future__ import annotations

import networkx as nx

from canarygraph.analysis.resolution import SymbolResolver
from canarygraph.domain import CallGraphEdge, Confidence, PythonModule


class CallGraph:
    """A caller -> callee graph.

    Direct-neighbor queries are O(degree), reachability is O(V + E), and shortest
    unweighted paths use BFS via NetworkX in O(V + E).
    """

    def __init__(self) -> None:
        self.graph: nx.DiGraph[str] = nx.DiGraph()

    @classmethod
    def build(cls, modules: tuple[PythonModule, ...]) -> CallGraph:
        result = cls()
        resolver = SymbolResolver(modules)
        known = resolver.function_names
        result.graph.add_nodes_from(known)
        for module in modules:
            for function in module.all_functions:
                for call in function.calls:
                    resolved = resolver.resolve_call(module, function, call.expression)
                    if resolved.target in known:
                        result.graph.add_edge(
                            function.qualified_name,
                            resolved.target,
                            confidence=resolved.confidence.value,
                        )
        return result

    @property
    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self.graph.nodes))

    @property
    def edges(self) -> tuple[CallGraphEdge, ...]:
        return tuple(
            CallGraphEdge(caller, callee, Confidence(data.get("confidence", "HIGH")))
            for caller, callee, data in sorted(self.graph.edges(data=True))
        )

    def direct_callers(self, callee: str) -> tuple[str, ...]:
        return tuple(sorted(self.graph.predecessors(callee))) if callee in self.graph else ()

    def direct_callees(self, caller: str) -> tuple[str, ...]:
        return tuple(sorted(self.graph.successors(caller))) if caller in self.graph else ()

    def transitive_callers(self, callee: str) -> tuple[str, ...]:
        return tuple(sorted(nx.ancestors(self.graph, callee))) if callee in self.graph else ()

    def transitive_callees(self, caller: str) -> tuple[str, ...]:
        return tuple(sorted(nx.descendants(self.graph, caller))) if caller in self.graph else ()

    def shortest_path(self, caller: str, callee: str) -> tuple[str, ...]:
        try:
            return tuple(nx.shortest_path(self.graph, caller, callee))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return ()

    def paths_to_any(self, targets: set[str]) -> tuple[tuple[str, ...], ...]:
        paths: list[tuple[str, ...]] = []
        for node in self.graph.nodes:
            candidates = [self.shortest_path(node, target) for target in targets]
            candidates = [candidate for candidate in candidates if candidate]
            if candidates:
                paths.append(min(candidates, key=len))
        return tuple(sorted(set(paths)))
