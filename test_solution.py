"""
Comprehensive Unit Test Suite for solution.py
Campus Reachability and Emergency Route Audit
Validates solution.py against exact problem specifications and edge cases:
1. Supplied Sample 1 with exact output
2. Supplied Sample 2 with exact output
3. Graph with no edges (m = 0)
4. Source-to-itself route query (distance 0, [s])
5. Multiple shortest paths with deterministic BFS first-discovery parents
6. Disconnected components (labels, no crossing components)
7. Graph with one isolated vertex
8. Multiple reachable and unreachable targets in preserved order
9. Edges supplied in unsorted order and reversed endpoints (u > v)
10. Single-vertex graph (n = 1, m = 0)
"""

import subprocess
import sys
import unittest


def run_solution(input_str: str) -> str:
    """Helper to execute solution.py via subprocess and capture standard output."""
    proc = subprocess.run(
        [sys.executable, "solution.py"],
        input=input_str,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


class TestCampusReachabilityAudit(unittest.TestCase):

    def test_sample_1_exact(self):
        """Supplied Sample Test Case 1: connected components, BFS tie-breaking, reachable & unreachable."""
        input_data = (
            "6 5\n"
            "0 2\n"
            "0 1\n"
            "1 3\n"
            "2 3\n"
            "4 5\n"
            "0 3\n"
            "3\n"
            "5\n"
            "0\n"
        )
        expected_output = (
            "COMPONENTS 2\n"
            "LABELS 0 0 0 0 4 4\n"
            "DFS 0 1 3 2\n"
            "BFS 0 1 2 3\n"
            "ROUTE 3 2 0 1 3\n"
            "ROUTE 5 UNREACHABLE\n"
            "ROUTE 0 0 0\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_sample_2_exact(self):
        """Supplied Sample Test Case 2: all vertices isolated, source-to-itself and unreachable."""
        input_data = (
            "3 0\n"
            "1 2\n"
            "1\n"
            "0\n"
        )
        expected_output = (
            "COMPONENTS 3\n"
            "LABELS 0 1 2\n"
            "DFS 1\n"
            "BFS 1\n"
            "ROUTE 1 0 1\n"
            "ROUTE 0 UNREACHABLE\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_graph_with_no_edges(self):
        """Graph with n=4 vertices and m=0 edges: all vertices form separate components."""
        input_data = (
            "4 0\n"
            "2 4\n"
            "2\n"
            "0\n"
            "1\n"
            "3\n"
        )
        expected_output = (
            "COMPONENTS 4\n"
            "LABELS 0 1 2 3\n"
            "DFS 2\n"
            "BFS 2\n"
            "ROUTE 2 0 2\n"
            "ROUTE 0 UNREACHABLE\n"
            "ROUTE 1 UNREACHABLE\n"
            "ROUTE 3 UNREACHABLE\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_source_to_itself(self):
        """Verify source-to-itself query produces distance 0 and contains only source."""
        # Graph with 4 vertices in a line 0-1-2-3
        input_data = (
            "4 3\n"
            "0 1\n"
            "1 2\n"
            "2 3\n"
            "2 1\n"
            "2\n"
        )
        expected_output = (
            "COMPONENTS 1\n"
            "LABELS 0 0 0 0\n"
            "DFS 2 1 0 3\n"
            "BFS 2 1 3 0\n"
            "ROUTE 2 0 2\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_multiple_shortest_paths_deterministic_bfs_parents(self):
        """
        Verify deterministic tie-breaking when multiple shortest paths exist.
        Source: 0. Target: 4.
        Paths to 4:
          0 -> 1 -> 4 (length 2)
          0 -> 2 -> 4 (length 2)
          0 -> 3 -> 4 (length 2)
        Because neighbors of 0 are explored in increasing order [1, 2, 3],
        1 is enqueued before 2 and 3.
        When 1 is dequeued, it discovers 4 first, setting parent[4] = 1.
        The resulting route must be: 0 1 4.
        """
        input_data = (
            "5 6\n"
            "0 3\n"
            "0 1\n"
            "0 2\n"
            "1 4\n"
            "2 4\n"
            "3 4\n"
            "0 1\n"
            "4\n"
        )
        expected_output = (
            "COMPONENTS 1\n"
            "LABELS 0 0 0 0 0\n"
            "DFS 0 1 4 2 3\n"
            "BFS 0 1 2 3 4\n"
            "ROUTE 4 2 0 1 4\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_multiple_disconnected_components(self):
        """
        Graph with 3 disconnected components:
        Comp 1: {0, 1} -> root label 0
        Comp 2: {2, 3, 4} -> root label 2
        Comp 3: {5, 6, 7} -> root label 5
        Source s=3 is in Component 2.
        Ensure DFS and BFS stay within Component 2 and do not cross components.
        """
        input_data = (
            "8 5\n"
            "0 1\n"
            "2 3\n"
            "3 4\n"
            "5 6\n"
            "6 7\n"
            "3 4\n"
            "4\n"
            "1\n"
            "7\n"
            "3\n"
        )
        expected_output = (
            "COMPONENTS 3\n"
            "LABELS 0 0 2 2 2 5 5 5\n"
            "DFS 3 2 4\n"
            "BFS 3 2 4\n"
            "ROUTE 4 1 3 4\n"
            "ROUTE 1 UNREACHABLE\n"
            "ROUTE 7 UNREACHABLE\n"
            "ROUTE 3 0 3\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_one_isolated_vertex(self):
        """Graph where vertices {0, 1, 2} form a triangle, and vertex 3 is completely isolated."""
        input_data = (
            "4 3\n"
            "0 1\n"
            "1 2\n"
            "2 0\n"
            "0 2\n"
            "3\n"
            "2\n"
        )
        expected_output = (
            "COMPONENTS 2\n"
            "LABELS 0 0 0 3\n"
            "DFS 0 1 2\n"
            "BFS 0 1 2\n"
            "ROUTE 3 UNREACHABLE\n"
            "ROUTE 2 1 0 2\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_multiple_reachable_and_unreachable_targets_preserve_order(self):
        """Verify queries in arbitrary order preserve target ordering and output correct routes."""
        # Component A: 0-1-2, Component B: 3-4, Component C: 5
        input_data = (
            "6 3\n"
            "0 1\n"
            "1 2\n"
            "3 4\n"
            "1 6\n"
            "5\n"
            "2\n"
            "4\n"
            "0\n"
            "1\n"
            "3\n"
        )
        expected_output = (
            "COMPONENTS 3\n"
            "LABELS 0 0 0 3 3 5\n"
            "DFS 1 0 2\n"
            "BFS 1 0 2\n"
            "ROUTE 5 UNREACHABLE\n"
            "ROUTE 2 1 1 2\n"
            "ROUTE 4 UNREACHABLE\n"
            "ROUTE 0 1 1 0\n"
            "ROUTE 1 0 1\n"
            "ROUTE 3 UNREACHABLE\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_edges_supplied_in_unsorted_order_and_reversed_endpoints(self):
        """
        Verify that input edge order is arbitrary and endpoints (u, v) with u > v
        do not affect sorted adjacency lists or traversal results.
        Uses same structure as Sample 1 but scrambled edge list.
        """
        input_data = (
            "6 5\n"
            "5 4\n"
            "3 1\n"
            "2 0\n"
            "3 2\n"
            "1 0\n"
            "0 3\n"
            "3\n"
            "5\n"
            "0\n"
        )
        expected_output = (
            "COMPONENTS 2\n"
            "LABELS 0 0 0 0 4 4\n"
            "DFS 0 1 3 2\n"
            "BFS 0 1 2 3\n"
            "ROUTE 3 2 0 1 3\n"
            "ROUTE 5 UNREACHABLE\n"
            "ROUTE 0 0 0\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)

    def test_single_vertex_graph(self):
        """Boundary test: minimal graph constraint n = 1, m = 0, q = 1, t = 0."""
        input_data = (
            "1 0\n"
            "0 1\n"
            "0\n"
        )
        expected_output = (
            "COMPONENTS 1\n"
            "LABELS 0\n"
            "DFS 0\n"
            "BFS 0\n"
            "ROUTE 0 0 0\n"
        )
        actual = run_solution(input_data)
        self.assertEqual(actual, expected_output)


if __name__ == "__main__":
    unittest.main()

