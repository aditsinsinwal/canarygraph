# Call graph

Nodes are qualified application functions/methods. Edges point from caller to callee. FastAPI and
Flask decorators annotate function nodes as externally reachable entry points.

- Direct callers/callees: O(node degree).
- Transitive callers/callees: DFS, O(V + E).
- Shortest impact path: unweighted BFS, O(V + E).
- Blast radius for `k` direct uses: O(k(V + E)) in the initial implementation.

External SDK functions appear at the end of reported impact paths but are not application graph
nodes. This keeps graph construction independent from a particular SDK comparison.

