"""
Campus Reachability and Emergency Route Audit
Core Algorithmic Engine & CLI Runner
Author: Senior Python Developer & Algorithms Engineer

This module models an undirected campus building graph and provides:
1. Adjacency list representation with deterministic sorting.
2. Recursive Depth-First Search (DFS) for connected components and isolated hazard zones.
3. Recursive Depth-First Search (DFS) for reachable subgraphs from a designated emergency source.
4. Queue-based Breadth-First Search (BFS) for level-order exploration from source.
5. Shortest route identification using BFS distances and first-discovery parent pointers.
6. Exact assignment text formatting and structured JSON data export.
"""

from collections import deque
import json
import sys
from typing import Dict, List, Optional, Set, Tuple


class CampusGraph:
    """
    Undirected Graph Representation for Campus Reachability & Emergency Route Audit.
    All neighbor explorations enforce lexicographical tie-breaking for deterministic output.
    """

    def __init__(self):
        self.adj: Dict[str, List[str]] = {}

    def add_vertex(self, u: str) -> None:
        """Ensure vertex u is registered in the adjacency list."""
        u = u.strip()
        if not u:
            return
        if u not in self.adj:
            self.adj[u] = []

    def add_edge(self, u: str, v: str) -> None:
        """
        Add an undirected edge between vertex u and vertex v.
        Avoids duplicate edges and self-loops.
        """
        u = u.strip()
        v = v.strip()
        if not u or not v:
            return
        self.add_vertex(u)
        self.add_vertex(v)
        if u == v:
            # Self-loops do not contribute to reachability across distinct campus locations
            return

        if v not in self.adj[u]:
            self.adj[u].append(v)
            self.adj[u].sort()
        if u not in self.adj[v]:
            self.adj[v].append(u)
            self.adj[v].sort()

    @property
    def vertices(self) -> List[str]:
        """Return all vertices in sorted order."""
        return sorted(self.adj.keys())

    @property
    def edge_count(self) -> int:
        """Return total undirected edge count."""
        return sum(len(neighbors) for neighbors in self.adj.values()) // 2

    @classmethod
    def from_edge_lines(cls, lines: List[str]) -> "CampusGraph":
        """
        Parse raw line input.
        Supports space, comma, tab, dash, or arrow separated pairs:
        e.g. 'A B', 'Gate, Admin', 'Library - Cafeteria', or 'Hostel' (isolated node).
        """
        graph = cls()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if line specifies an isolated vertex without edges
            tokens = []
            for sep in [",", "-", "<->", "--", "->", "\t"]:
                if sep in line:
                    parts = [p.strip() for p in line.split(sep) if p.strip()]
                    if len(parts) >= 2:
                        tokens = parts
                        break

            if not tokens:
                tokens = line.split()

            if len(tokens) == 1:
                graph.add_vertex(tokens[0])
            elif len(tokens) >= 2:
                graph.add_edge(tokens[0], tokens[1])

        return graph

    # -------------------------------------------------------------------------
    # 1. RECURSIVE DFS FOR CONNECTED COMPONENTS
    # -------------------------------------------------------------------------
    def _dfs_component_recursive(
        self, u: str, visited: Set[str], current_comp: List[str]
    ) -> None:
        """Helper to recursively discover all reachable vertices in the current component."""
        visited.add(u)
        current_comp.append(u)
        for neighbor in sorted(self.adj.get(u, [])):
            if neighbor not in visited:
                self._dfs_component_recursive(neighbor, visited, current_comp)

    def get_connected_components(self) -> List[List[str]]:
        """
        Compute all connected components of the undirected campus graph using recursive DFS.
        Returns a list of components, each sorted alphabetically.
        Components are sorted by their lexicographically smallest member.
        """
        visited: Set[str] = set()
        components: List[List[str]] = []

        for vertex in self.vertices:
            if vertex not in visited:
                comp: List[str] = []
                self._dfs_component_recursive(vertex, visited, comp)
                comp.sort()
                components.append(comp)

        components.sort(key=lambda c: c[0] if c else "")
        return components

    # -------------------------------------------------------------------------
    # 2. RECURSIVE DFS FROM SOURCE
    # -------------------------------------------------------------------------
    def _dfs_source_recursive(
        self, u: str, visited: Set[str], traversal_order: List[str]
    ) -> None:
        """Recursive DFS visiting neighbors in deterministic sorted order."""
        visited.add(u)
        traversal_order.append(u)
        for neighbor in sorted(self.adj.get(u, [])):
            if neighbor not in visited:
                self._dfs_source_recursive(neighbor, visited, traversal_order)

    def dfs_from_source(self, source: str) -> List[str]:
        """
        Perform recursive DFS traversal strictly from the specified source node.
        Returns the ordered list of vertices in discovery sequence.
        """
        source = source.strip()
        if source not in self.adj:
            return []
        visited: Set[str] = set()
        traversal_order: List[str] = []
        self._dfs_source_recursive(source, visited, traversal_order)
        return traversal_order

    # -------------------------------------------------------------------------
    # 3. QUEUE-BASED BFS FROM SOURCE & FIRST-DISCOVERY PARENTS
    # -------------------------------------------------------------------------
    def bfs_from_source(
        self, source: str
    ) -> Tuple[List[str], Dict[str, int], Dict[str, Optional[str]]]:
        """
        Perform queue-based BFS traversal from source.
        Returns:
            - discovery_order: List[str] in BFS visitation sequence.
            - distances: Dict[str, int] (minimum hop count from source; inf or -1 if unreachable).
            - parents: Dict[str, Optional[str]] (first-discovery parent node for shortest path reconstruction).
        """
        source = source.strip()
        all_nodes = self.vertices
        distances: Dict[str, int] = {v: -1 for v in all_nodes}
        parents: Dict[str, Optional[str]] = {v: None for v in all_nodes}
        discovery_order: List[str] = []

        if source not in self.adj:
            return discovery_order, distances, parents

        queue: deque[str] = deque([source])
        distances[source] = 0
        parents[source] = None
        visited: Set[str] = {source}

        while queue:
            curr = queue.popleft()
            discovery_order.append(curr)

            for neighbor in sorted(self.adj.get(curr, [])):
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = distances[curr] + 1
                    parents[neighbor] = curr
                    queue.append(neighbor)

        return discovery_order, distances, parents

    # -------------------------------------------------------------------------
    # 4. SHORTEST ROUTE RECONSTRUCTION VIA FIRST-DISCOVERY PARENTS
    # -------------------------------------------------------------------------
    def reconstruct_route(
        self,
        source: str,
        destination: str,
        parents: Dict[str, Optional[str]],
        distances: Dict[str, int],
    ) -> Optional[List[str]]:
        """
        Reconstruct shortest hop route from source to destination using first-discovery parents.
        Returns:
            - List of vertex names [source, ..., destination] if reachable.
            - None if unreachable.
        """
        source = source.strip()
        destination = destination.strip()
        if destination not in distances or distances[destination] == -1:
            return None

        route = []
        curr: Optional[str] = destination
        while curr is not None:
            route.append(curr)
            if curr == source:
                break
            curr = parents.get(curr)

        if not route or route[-1] != source:
            return None

        route.reverse()
        return route

    # -------------------------------------------------------------------------
    # 5. COMPREHENSIVE AUDIT REPORT GENERATION
    # -------------------------------------------------------------------------
    def audit(self, source: str) -> Dict:
        """
        Execute full emergency audit:
        - Validates source
        - Computes connected components
        - Executes recursive DFS
        - Executes queue BFS and shortest paths
        - Formats exact assignment text output and structured JSON.
        """
        source = source.strip()
        all_nodes = self.vertices
        is_source_valid = source in self.adj

        # Connected components
        components = self.get_connected_components()
        is_fully_connected = len(components) <= 1

        if is_source_valid:
            dfs_order = self.dfs_from_source(source)
            bfs_order, distances, parents = self.bfs_from_source(source)
        else:
            dfs_order = []
            bfs_order = []
            distances = {v: -1 for v in all_nodes}
            parents = {v: None for v in all_nodes}

        # Route table calculation
        route_records = []
        reachable_count = 0
        unreachable_count = 0

        for node in all_nodes:
            dist = distances.get(node, -1)
            is_reachable = dist != -1

            if is_reachable:
                reachable_count += 1
                route = self.reconstruct_route(source, node, parents, distances)
                if node == source:
                    status = "HUB"
                else:
                    status = "REACHABLE"
            else:
                unreachable_count += 1
                route = None
                status = "UNREACHABLE"

            route_records.append(
                {
                    "destination": node,
                    "distance": dist if is_reachable else "INF",
                    "status": status,
                    "route": route,
                    "route_display": " -> ".join(route) if route else "NO ROUTE (ISOLATED)",
                }
            )

        # Build exact assignment output text
        exact_text = self._build_assignment_text(
            source=source,
            is_source_valid=is_source_valid,
            components=components,
            dfs_order=dfs_order,
            bfs_order=bfs_order,
            route_records=route_records,
            is_fully_connected=is_fully_connected,
        )

        return {
            "source": source,
            "is_source_valid": is_source_valid,
            "total_vertices": len(all_nodes),
            "total_edges": self.edge_count,
            "vertices": all_nodes,
            "adjacency_list": {v: sorted(self.adj[v]) for v in all_nodes},
            "connected_components": components,
            "is_fully_connected": is_fully_connected,
            "dfs_traversal_order": dfs_order,
            "bfs_discovery_order": bfs_order,
            "routes": route_records,
            "reachable_count": reachable_count,
            "unreachable_count": unreachable_count,
            "exact_output_text": exact_text,
        }

    def _build_assignment_text(
        self,
        source: str,
        is_source_valid: bool,
        components: List[List[str]],
        dfs_order: List[str],
        bfs_order: List[str],
        route_records: List[Dict],
        is_fully_connected: bool,
    ) -> str:
        """Construct exact formatted report matching assignment rubrics."""
        lines = []
        sep = "=" * 72
        sub_sep = "-" * 72

        lines.append(sep)
        lines.append("           CAMPUS REACHABILITY & EMERGENCY ROUTE AUDIT")
        lines.append(sep)
        lines.append(f"EMERGENCY HUB (SOURCE): {source}")
        lines.append(f"TOTAL CAMPUS LOCATIONS: {len(self.vertices)}")
        lines.append(f"TOTAL ACCESS PATHS:     {self.edge_count}")
        lines.append("")

        lines.append("--- ADJACENCY LIST REPRESENTATION ---")
        for v in self.vertices:
            neighbors = self.adj.get(v, [])
            lines.append(f"{v:15} -> {neighbors}")
        lines.append("")

        lines.append("--- CONNECTED COMPONENTS AUDIT (RECURSIVE DFS) ---")
        lines.append(f"Total Components Found: {len(components)}")
        for idx, comp in enumerate(components, 1):
            lines.append(f"Component {idx:02d}: {comp} (Size: {len(comp)})")
        if is_fully_connected:
            lines.append("Campus Connectivity Status: FULLY CONNECTED (No Isolated Zones)")
        else:
            lines.append(
                "Campus Connectivity Status: DISCONNECTED - HAZARDOUS ISOLATION DETECTED!"
            )
        lines.append("")

        if not is_source_valid:
            lines.append(f"ERROR: Specified Emergency Hub '{source}' does not exist in graph!")
            lines.append(sep)
            return "\n".join(lines)

        lines.append("--- RECURSIVE DFS TRAVERSAL FROM SOURCE ---")
        lines.append(f"Discovery Path: {' -> '.join(dfs_order)}")
        lines.append(f"Reachable Locations Count: {len(dfs_order)} / {len(self.vertices)}")
        lines.append("")

        lines.append("--- QUEUE-BASED BFS TRAVERSAL FROM SOURCE ---")
        lines.append(f"Discovery Order: {' -> '.join(bfs_order)}")
        lines.append(f"Reachable Locations Count: {len(bfs_order)} / {len(self.vertices)}")
        lines.append("")

        lines.append("--- EMERGENCY SHORTEST ROUTES (BFS FIRST-DISCOVERY PARENTS) ---")
        lines.append(f"{'Destination':<18} {'Distance':<10} {'Status':<14} {'Emergency Route'}")
        lines.append(sub_sep)
        for r in route_records:
            lines.append(
                f"{r['destination']:<18} {str(r['distance']):<10} {r['status']:<14} {r['route_display']}"
            )
        lines.append(sep)

        return "\n".join(lines)


# -----------------------------------------------------------------------------
# CLI INTERFACE & PRESET SAMPLES
# -----------------------------------------------------------------------------
SAMPLE_1_CONNECTED = """# Sample Case 1: Standard Connected Campus Grid
Gate Admin
Gate Cafeteria
Admin Library
Admin Academic_Block
Cafeteria Health_Center
Library Academic_Block
Academic_Block Health_Center
"""

SAMPLE_2_HAZARD = """# Sample Case 2: Disconnected Campus with Hazardous Isolated Zone
Main_Station Hostel_A
Main_Station Hostel_B
Hostel_A Dining_Hall
Hostel_B Dining_Hall
Research_Annex Power_Substation
"""


def main():
    """Command Line Runner for Campus Reachability and Emergency Route Audit."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Campus Reachability & Emergency Route Audit — DAA Core Engine"
    )
    parser.add_argument(
        "--file", "-f", type=str, help="Path to text file containing campus graph edges"
    )
    parser.add_argument(
        "--source", "-s", type=str, default="Gate", help="Designated Emergency Hub node"
    )
    parser.add_argument(
        "--sample",
        choices=["1", "2"],
        help="Run built-in benchmark (1: Connected, 2: Disconnected Hazard)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output audit results as JSON"
    )

    args = parser.parse_args()

    if args.sample == "1":
        raw_input = SAMPLE_1_CONNECTED
        source = args.source if args.source != "Gate" else "Gate"
    elif args.sample == "2":
        raw_input = SAMPLE_2_HAZARD
        source = args.source if args.source != "Gate" else "Main_Station"
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw_input = f.read()
        source = args.source
    else:
        # If no arguments provided, default to Sample Case 1 for immediate demonstration
        raw_input = SAMPLE_1_CONNECTED
        source = "Gate"

    graph = CampusGraph.from_edge_lines(raw_input.splitlines())
    audit_data = graph.audit(source)

    if args.json:
        print(json.dumps(audit_data, indent=2))
    else:
        print(audit_data["exact_output_text"])


if __name__ == "__main__":
    main()

