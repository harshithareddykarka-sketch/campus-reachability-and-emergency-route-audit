"""
Problem 02: Campus Reachability and Emergency Route Audit
DAA Lab Challenge - Python 3 Core Algorithm

This module implements:
1. Undirected graph representation with sorted adjacency lists.
2. Recursive Depth-First Search (DFS) for connected components, starting at the
   smallest unvisited vertex and labeling every vertex in that component with that root vertex.
3. Independent recursive Depth-First Search (DFS) from source s, exploring neighbors in increasing order.
4. Independent queue-based Breadth-First Search (BFS) from source s, recording discovery order upon dequeue,
   marking upon enqueue, and tracking distance and first-discovery parents.
5. Reconstructing minimum-edge routes using BFS parent pointers, or outputting UNREACHABLE.
6. A reusable execution engine `execute_audit` used by both CLI and the Flask backend.
"""

from collections import deque
import sys
from typing import Any, Dict, List, Optional, Tuple


def execute_audit(
    n: int, edges: List[Tuple[int, int]], s: int, targets: List[int]
) -> Dict[str, Any]:
    """
    Execute the complete Campus Reachability and Emergency Route Audit algorithm.
    All inputs and algorithms strictly adhere to the challenge specification.
    
    Returns structured results for visualization and the exact verbatim assignment text.
    """
    # 1. Build adjacency lists for undirected edges
    adj: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        if 0 <= u < n and 0 <= v < n:
            adj[u].append(v)
            adj[v].append(u)

    # Ensure all adjacency lists are sorted in increasing vertex-number order
    for u in range(n):
        adj[u].sort()

    # -------------------------------------------------------------------------
    # PART 1: CONNECTED COMPONENTS VIA RECURSIVE DFS
    # -------------------------------------------------------------------------
    component_labels = [-1] * n
    num_components = 0
    component_groups: Dict[int, List[int]] = {}

    def dfs_component(u: int, root_label: int) -> None:
        component_labels[u] = root_label
        component_groups[root_label].append(u)
        for neighbor in adj[u]:
            if component_labels[neighbor] == -1:
                dfs_component(neighbor, root_label)

    for v in range(n):
        if component_labels[v] == -1:
            num_components += 1
            component_groups[v] = []
            # v is guaranteed to be the smallest unvisited vertex in this component
            dfs_component(v, v)

    # Sort vertices in each component group for display
    for root in component_groups:
        component_groups[root].sort()

    # -------------------------------------------------------------------------
    # PART 2: RECURSIVE SOURCE DFS
    # -------------------------------------------------------------------------
    dfs_visited = [False] * n
    dfs_order: List[int] = []

    def dfs_source(u: int) -> None:
        dfs_visited[u] = True
        dfs_order.append(u)
        for neighbor in adj[u]:
            if not dfs_visited[neighbor]:
                dfs_source(neighbor)

    if 0 <= s < n:
        dfs_source(s)

    # -------------------------------------------------------------------------
    # PART 3: QUEUE-BASED SOURCE BFS
    # -------------------------------------------------------------------------
    bfs_order: List[int] = []
    dist = [-1] * n
    parent: List[Optional[int]] = [None] * n
    enqueued = [False] * n

    if 0 <= s < n:
        bfs_queue: deque[int] = deque([s])
        enqueued[s] = True
        dist[s] = 0
        parent[s] = None

        while bfs_queue:
            curr = bfs_queue.popleft()
            bfs_order.append(curr)

            for neighbor in adj[curr]:
                if not enqueued[neighbor]:
                    enqueued[neighbor] = True
                    dist[neighbor] = dist[curr] + 1
                    parent[neighbor] = curr
                    bfs_queue.append(neighbor)

    # -------------------------------------------------------------------------
    # PART 4: ROUTE COMPUTATION FOR TARGETS
    # -------------------------------------------------------------------------
    routes_data = []
    output_lines = []

    # Exact output lines according to specification
    output_lines.append(f"COMPONENTS {num_components}")
    output_lines.append("LABELS " + " ".join(map(str, component_labels)))
    output_lines.append("DFS " + " ".join(map(str, dfs_order)))
    output_lines.append("BFS " + " ".join(map(str, bfs_order)))

    for t in targets:
        if t < 0 or t >= n or dist[t] == -1:
            output_lines.append(f"ROUTE {t} UNREACHABLE")
            routes_data.append({
                "target": t,
                "distance": "UNREACHABLE",
                "path": [],
                "is_reachable": False,
                "display": f"ROUTE {t} UNREACHABLE"
            })
        else:
            route = []
            curr: Optional[int] = t
            while curr is not None:
                route.append(curr)
                if curr == s:
                    break
                curr = parent[curr]
            route.reverse()
            d = dist[t]
            route_str = " ".join(map(str, route))
            output_lines.append(f"ROUTE {t} {d} {route_str}")
            routes_data.append({
                "target": t,
                "distance": d,
                "path": route,
                "is_reachable": True,
                "display": f"ROUTE {t} {d} {route_str}"
            })

    exact_output = "\n".join(output_lines) + "\n"

    return {
        "n": n,
        "m": len(edges),
        "edges": edges,
        "adj": adj,
        "source": s,
        "targets": targets,
        "num_components": num_components,
        "component_labels": component_labels,
        "component_groups": component_groups,
        "dfs_order": dfs_order,
        "bfs_order": bfs_order,
        "distances": dist,
        "parents": parent,
        "routes": routes_data,
        "exact_output": exact_output
    }


def solve() -> None:
    """Read problem input from standard input and output exact specification results."""
    sys.setrecursionlimit(5000)
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    it = iter(input_data)
    n = int(next(it))
    m = int(next(it))
    edges = []
    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        edges.append((u, v))

    s = int(next(it))
    q = int(next(it))
    targets = [int(next(it)) for _ in range(q)]

    result = execute_audit(n, edges, s, targets)
    sys.stdout.write(result["exact_output"])


if __name__ == "__main__":
    solve()
