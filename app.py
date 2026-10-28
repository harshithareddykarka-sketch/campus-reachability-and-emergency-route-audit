"""
Flask Web Application for Campus Reachability and Emergency Route Audit
Connects Python algorithmic engine (solution.py) with the SVG emergency dashboard.
The Python backend remains the single source of truth for all algorithms.
Uses in-process execution to avoid any shell command injection.
"""

import os
from typing import Any, Dict, List, Tuple
from flask import Flask, render_template, request, jsonify, send_file
from solution import execute_audit

app = Flask(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTION_SCRIPT_PATH = os.path.join(CURRENT_DIR, "solution.py")
CORE_SCRIPT_PATH = os.path.join(CURRENT_DIR, "campus_route_audit.py")


@app.route("/")
def index():
    """Render main university emergency operations dashboard."""
    return render_template("index.html")


@app.route("/api/sample/<sample_id>")
def get_sample(sample_id):
    """Return official Challenge Sample Cases."""
    if sample_id == "1":
        return jsonify({
            "name": "Sample Case 1: Standard Multi-Component Campus Grid",
            "n": 6,
            "edges": [[0, 2], [0, 1], [1, 3], [2, 3], [4, 5]],
            "edges_text": "0 2\n0 1\n1 3\n2 3\n4 5",
            "source": 0,
            "targets": [3, 5, 0],
            "targets_text": "3\n5\n0"
        })
    elif sample_id == "2":
        return jsonify({
            "name": "Sample Case 2: Isolated Vertices with Disconnected Areas",
            "n": 3,
            "edges": [],
            "edges_text": "",
            "source": 1,
            "targets": [1, 0],
            "targets_text": "1\n0"
        })
    return jsonify({"error": "Unknown sample case"}), 404


@app.route("/api/audit", methods=["POST"])
def run_audit():
    """
    Execute emergency reachability and route audit using solution.py engine.
    Accepts JSON with:
        - n: int (number of vertices, 1 <= n <= 200)
        - edges: list of [u, v] pairs OR edges_text: str (lines of u v)
        - source: int (source vertex s, 0 <= s < n)
        - targets: list of target ints OR targets_text: str (lines/space-separated)
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request payload. Expected JSON object."}), 400

    try:
        # 1. Validate n
        n_raw = data.get("n")
        if n_raw is None or str(n_raw).strip() == "":
            return jsonify({"error": "Total locations count (n) is required."}), 400
        n = int(n_raw)
        if n < 1 or n > 200:
            return jsonify({"error": "Total locations count (n) must be an integer between 1 and 200."}), 400

        # 2. Parse and validate undirected edges (supports both list of pairs and text lines)
        edges: List[Tuple[int, int]] = []
        raw_edges = data.get("edges")
        edges_text = data.get("edges_text")

        if isinstance(raw_edges, list):
            for idx, item in enumerate(raw_edges):
                if not (isinstance(item, (list, tuple)) and len(item) == 2):
                    return jsonify({"error": f"Invalid edge at index {idx}. Must be a pair [u, v]."}), 400
                u, v = int(item[0]), int(item[1])
                if u < 0 or u >= n or v < 0 or v >= n:
                    return jsonify({"error": f"Edge endpoint out of range at index {idx}: [{u}, {v}]. Vertices must be in [0, {n - 1}]."}), 400
                edges.append((u, v))
        elif edges_text is not None:
            for line_no, line in enumerate(str(edges_text).splitlines(), start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    return jsonify({"error": f"Invalid edge on line {line_no}: '{line}'. Must contain two vertex numbers."}), 400
                u, v = int(parts[0]), int(parts[1])
                if u < 0 or u >= n or v < 0 or v >= n:
                    return jsonify({"error": f"Edge endpoint out of range on line {line_no}: ({u}, {v}). Vertices must be between 0 and {n - 1}."}), 400
                edges.append((u, v))

        # 3. Validate source vertex s
        s_raw = data.get("source")
        if s_raw is None or str(s_raw).strip() == "":
            return jsonify({"error": "Emergency Hub source vertex (s) is required."}), 400
        s = int(s_raw)
        if s < 0 or s >= n:
            return jsonify({"error": f"Source vertex {s} is out of range. Must be between 0 and {n - 1}."}), 400

        # 4. Parse and validate target vertices (supports both list and text lines)
        targets: List[int] = []
        raw_targets = data.get("targets")
        targets_text = data.get("targets_text")

        if isinstance(raw_targets, list):
            for t_val in raw_targets:
                t = int(t_val)
                if t < 0 or t >= n:
                    return jsonify({"error": f"Target vertex {t} is out of range. Must be between 0 and {n - 1}."}), 400
                targets.append(t)
        elif targets_text is not None:
            for tok in str(targets_text).split():
                t = int(tok)
                if t < 0 or t >= n:
                    return jsonify({"error": f"Target vertex {t} is out of range. Must be between 0 and {n - 1}."}), 400
                targets.append(t)

        # 5. Execute pure Python 3 algorithm (solution.py) directly in-process
        # This completely eliminates any shell command injection risk
        result = execute_audit(n, edges, s, targets)

        # Provide both canonical and extended keys for seamless UI and API integration
        response_payload: Dict[str, Any] = {
            "n": n,
            "m": len(edges),
            "edges": edges,
            "source": s,
            "targets": targets,
            "component_count": result["num_components"],
            "num_components": result["num_components"],
            "labels": result["component_labels"],
            "component_labels": result["component_labels"],
            "component_groups": result["component_groups"],
            "dfs": result["dfs_order"],
            "dfs_order": result["dfs_order"],
            "bfs": result["bfs_order"],
            "bfs_order": result["bfs_order"],
            "distances": result["distances"],
            "parents": result["parents"],
            "routes": result["routes"],
            "exact_output": result["exact_output"],
        }

        return jsonify(response_payload)

    except ValueError as ve:
        return jsonify({"error": f"Numerical format error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Audit execution failed: {str(e)}"}), 500


@app.route("/api/download")
def download_script():
    """Download solution.py, CODE-DOC.pdf, or campus_route_audit.py directly."""
    target_file = request.args.get("file", "solution.py")
    if target_file == "CODE-DOC.pdf":
        path = os.path.join(CURRENT_DIR, "CODE-DOC.pdf")
        name = "CODE-DOC.pdf"
        mimetype = "application/pdf"
    elif target_file == "campus_route_audit.py":
        path = CORE_SCRIPT_PATH
        name = "campus_route_audit.py"
        mimetype = "text/x-python"
    else:
        path = SOLUTION_SCRIPT_PATH
        name = "solution.py"
        mimetype = "text/x-python"

    if os.path.exists(path):
        return send_file(
            path,
            as_attachment=True,
            download_name=name,
            mimetype=mimetype
        )
    return jsonify({"error": "Script file not found."}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
