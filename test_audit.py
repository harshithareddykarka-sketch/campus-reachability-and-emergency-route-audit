"""
Automated Test Suite for Campus Reachability & Emergency Route Audit
Standard Library unittest
Covers:
- Sample Case 1: Connected Campus Network
- Sample Case 2: Disconnected Campus with Hazardous Isolated Zone
- Recursive DFS Connected Components
- Recursive Source DFS Traversal
- Queue-Based BFS Traversal
- BFS Distance Array and First-Discovery Parent Route Reconstruction
- Unreachable / Infinite Distance Handling
"""

import subprocess
import sys
import unittest
from campus_route_audit import CampusGraph, SAMPLE_1_CONNECTED, SAMPLE_2_HAZARD


class TestCampusReachability(unittest.TestCase):

    def setUp(self):
        # Sample 1: Fully connected campus
        self.graph1 = CampusGraph.from_edge_lines(SAMPLE_1_CONNECTED.splitlines())
        # Sample 2: Disconnected campus with hazardous isolation
        self.graph2 = CampusGraph.from_edge_lines(SAMPLE_2_HAZARD.splitlines())

    def test_sample1_graph_construction(self):
        """Verify vertex set, edge count, and adjacency list symmetry in Sample 1."""
        expected_vertices = [
            "Academic_Block",
            "Admin",
            "Cafeteria",
            "Gate",
            "Health_Center",
            "Library",
        ]
        self.assertEqual(self.graph1.vertices, expected_vertices)
        self.assertEqual(self.graph1.edge_count, 7)

        # Symmetry check (undirected property)
        for u in self.graph1.vertices:
            for v in self.graph1.adj[u]:
                self.assertIn(u, self.graph1.adj[v], f"Edge {u}-{v} must be undirected")

    def test_sample1_connected_components_recursive_dfs(self):
        """Sample 1 should yield exactly 1 connected component containing all 6 nodes."""
        components = self.graph1.get_connected_components()
        self.assertEqual(len(components), 1)
        self.assertEqual(
            components[0],
            ["Academic_Block", "Admin", "Cafeteria", "Gate", "Health_Center", "Library"],
        )

    def test_sample1_recursive_dfs_from_source(self):
        """
        DFS traversal from 'Gate' with lexicographically sorted neighbor exploration:
        Gate -> Admin -> Academic_Block -> Health_Center -> Cafeteria (backtracks to Admin) -> Library
        """
        dfs_order = self.graph1.dfs_from_source("Gate")
        self.assertEqual(len(dfs_order), 6)
        self.assertEqual(dfs_order[0], "Gate")
        # Ensure all vertices visited
        self.assertEqual(set(dfs_order), set(self.graph1.vertices))

    def test_sample1_bfs_from_source(self):
        """
        BFS from 'Gate':
        Level 0: Gate
        Level 1 (neighbors of Gate sorted): Admin, Cafeteria
        Level 2 (neighbors of Admin: Academic_Block, Library; neighbor of Cafeteria: Health_Center)
        """
        bfs_order, distances, parents = self.graph1.bfs_from_source("Gate")
        self.assertEqual(bfs_order[0], "Gate")
        self.assertEqual(bfs_order[1:3], ["Admin", "Cafeteria"])

        # Check distances
        self.assertEqual(distances["Gate"], 0)
        self.assertEqual(distances["Admin"], 1)
        self.assertEqual(distances["Cafeteria"], 1)
        self.assertEqual(distances["Academic_Block"], 2)
        self.assertEqual(distances["Library"], 2)
        self.assertEqual(distances["Health_Center"], 2)

        # Check first-discovery parents
        self.assertIsNone(parents["Gate"])
        self.assertEqual(parents["Admin"], "Gate")
        self.assertEqual(parents["Cafeteria"], "Gate")
        self.assertEqual(parents["Academic_Block"], "Admin")
        self.assertEqual(parents["Library"], "Admin")
        self.assertEqual(parents["Health_Center"], "Cafeteria")

    def test_sample1_shortest_route_reconstruction(self):
        """Verify shortest hop routes reconstructed from first-discovery parents."""
        _, distances, parents = self.graph1.bfs_from_source("Gate")

        route_to_health_center = self.graph1.reconstruct_route(
            "Gate", "Health_Center", parents, distances
        )
        self.assertEqual(route_to_health_center, ["Gate", "Cafeteria", "Health_Center"])

        route_to_library = self.graph1.reconstruct_route(
            "Gate", "Library", parents, distances
        )
        self.assertEqual(route_to_library, ["Gate", "Admin", "Library"])

    def test_sample2_disconnected_components_hazard_audit(self):
        """
        Sample 2 must detect exactly 2 connected components:
        Component 1: Dining_Hall, Hostel_A, Hostel_B, Main_Station
        Component 2: Power_Substation, Research_Annex
        """
        components = self.graph2.get_connected_components()
        self.assertEqual(len(components), 2)
        self.assertEqual(
            components[0],
            ["Dining_Hall", "Hostel_A", "Hostel_B", "Main_Station"],
        )
        self.assertEqual(
            components[1],
            ["Power_Substation", "Research_Annex"],
        )

    def test_sample2_unreachable_routes_and_infinite_distance(self):
        """
        In Sample 2, source is 'Main_Station'.
        Nodes in component 2 must be flagged unreachable (-1 in distances, None in route).
        """
        bfs_order, distances, parents = self.graph2.bfs_from_source("Main_Station")

        # Reachable component
        self.assertEqual(distances["Main_Station"], 0)
        self.assertEqual(distances["Hostel_A"], 1)
        self.assertEqual(distances["Hostel_B"], 1)
        self.assertEqual(distances["Dining_Hall"], 2)

        # Unreachable isolated hazard nodes
        self.assertEqual(distances["Research_Annex"], -1)
        self.assertEqual(distances["Power_Substation"], -1)
        self.assertNotIn("Research_Annex", bfs_order)
        self.assertNotIn("Power_Substation", bfs_order)

        # Route reconstruction
        route_isolated = self.graph2.reconstruct_route(
            "Main_Station", "Research_Annex", parents, distances
        )
        self.assertIsNone(route_isolated)

    def test_audit_exact_output_structure(self):
        """Verify audit dict output and formatted string generation."""
        audit_res = self.graph1.audit("Gate")
        self.assertTrue(audit_res["is_source_valid"])
        self.assertTrue(audit_res["is_fully_connected"])
        self.assertEqual(audit_res["reachable_count"], 6)
        self.assertEqual(audit_res["unreachable_count"], 0)
        self.assertIn("CAMPUS REACHABILITY & EMERGENCY ROUTE AUDIT", audit_res["exact_output_text"])
        self.assertIn("FULLY CONNECTED", audit_res["exact_output_text"])

        audit_res2 = self.graph2.audit("Main_Station")
        self.assertFalse(audit_res2["is_fully_connected"])
        self.assertEqual(audit_res2["reachable_count"], 4)
        self.assertEqual(audit_res2["unreachable_count"], 2)
        self.assertIn("DISCONNECTED - HAZARDOUS ISOLATION DETECTED", audit_res2["exact_output_text"])
        self.assertIn("UNREACHABLE", audit_res2["exact_output_text"])

    def test_flask_endpoints(self):
        """Verify Flask web server routes and JSON API responses."""
        from app import app
        client = app.test_client()

        # 1. Main index page
        res = client.get("/")
        self.assertEqual(res.status_code, 200)

        # 2. Sample 1 endpoint
        res = client.get("/api/sample/1")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["source"], 0)

        # 3. Audit endpoint with text lines input
        res = client.post(
            "/api/audit",
            json={
                "n": 6,
                "edges_text": "0 2\n0 1\n1 3\n2 3\n4 5",
                "source": 0,
                "targets_text": "3\n5\n0",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["n"], 6)
        self.assertEqual(data["num_components"], 2)
        self.assertEqual(data["component_count"], 2)
        self.assertEqual(data["labels"], [0, 0, 0, 0, 4, 4])
        self.assertEqual(data["dfs"], [0, 1, 3, 2])
        self.assertEqual(data["bfs"], [0, 1, 2, 3])
        self.assertEqual(data["distances"], [0, 1, 1, 2, -1, -1])
        self.assertEqual(len(data["routes"]), 3)
        self.assertIn("COMPONENTS 2", data["exact_output"])

        # 4. Audit endpoint with structured JSON arrays input
        res2 = client.post(
            "/api/audit",
            json={
                "n": 6,
                "edges": [[0, 2], [0, 1], [1, 3], [2, 3], [4, 5]],
                "source": 0,
                "targets": [3, 5, 0],
            },
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2["component_count"], 2)
        self.assertEqual(data2["labels"], [0, 0, 0, 0, 4, 4])
        self.assertEqual(data2["dfs"], [0, 1, 3, 2])
        self.assertEqual(data2["bfs"], [0, 1, 2, 3])
        self.assertEqual(data2["distances"], [0, 1, 1, 2, -1, -1])

        # 5. Validation error tests (out of range vertex)
        res_err = client.post(
            "/api/audit",
            json={"n": 4, "edges": [[0, 5]], "source": 0, "targets": [1]},
        )
        self.assertEqual(res_err.status_code, 400)
        self.assertIn("error", res_err.get_json())

        # 4. Download solution.py endpoint (default)
        res = client.get("/api/download")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"def solve", res.data)
        res.close()

        # 5. Download campus_route_audit.py endpoint
        res = client.get("/api/download?file=campus_route_audit.py")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"class CampusGraph", res.data)
        res.close()

        # 6. Download CODE-DOC.pdf endpoint
        res = client.get("/api/download?file=CODE-DOC.pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/pdf")
        self.assertTrue(res.data.startswith(b"%PDF"))
        res.close()

    def test_isolated_single_node(self):
        """Test edge case with isolated single vertex added without edges."""
        graph = CampusGraph()
        graph.add_vertex("Helipad")
        graph.add_edge("Building_A", "Building_B")
        components = graph.get_connected_components()
        self.assertEqual(len(components), 2)
        self.assertEqual(components[1], ["Helipad"])

        audit_res = graph.audit("Helipad")
        self.assertEqual(audit_res["reachable_count"], 1)
        self.assertEqual(audit_res["unreachable_count"], 2)

    def test_solution_py_sample1_exact(self):
        """Verify solution.py against official Hackathon Sample 1 exact specification."""
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
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            input=input_data,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(proc.stdout, expected_output)

    def test_solution_py_sample2_exact(self):
        """Verify solution.py against official Hackathon Sample 2 exact specification."""
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
        proc = subprocess.run(
            [sys.executable, "solution.py"],
            input=input_data,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(proc.stdout, expected_output)


if __name__ == "__main__":
    unittest.main()
