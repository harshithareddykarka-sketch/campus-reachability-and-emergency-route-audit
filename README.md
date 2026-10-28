# Campus Reachability and Emergency Route Audit

A comprehensive graph analysis and emergency route planning tool for university and corporate campuses. This project audits campus connectivity, detects isolated hazard zones using **Recursive Depth-First Search (DFS)**, explores radial reachability using **Queue-Based Breadth-First Search (BFS)**, and reconstructs optimal evacuation routes using **BFS distances and first-discovery parent pointers**.

---

## 📌 Project Overview & Algorithms

In an emergency (fire, power failure, flood, or medical event), emergency response units need to know:
1. **Is the campus fully connected?** Or are certain buildings/clusters severed into isolated hazard zones?
2. **Which buildings are reachable from the Emergency Hub?**
3. **What is the minimum-hop route to each building?**

### Algorithmic Highlights
- **Adjacency List Modeling**: Space-efficient $\mathcal{O}(V + E)$ undirected graph with deterministic numerical neighbor ordering.
- **Recursive DFS for Connected Components**: Identifies all isolated components, starts each component at the smallest unvisited vertex, and labels every vertex with that component's root index.
- **Independent Recursive Source DFS**: Explores depth-first reachability strictly from the designated emergency station $s$.
- **Independent Queue-Based Source BFS**: Explores concentric levels from the emergency station using a FIFO queue (`collections.deque`), marking vertices on enqueue and recording discovery on dequeue.
- **Shortest Route Reconstruction**: Records `dist[v] = dist[u] + 1` and `parent[v] = u` on the exact moment node `v` is first discovered. Reconstructs shortest path in reverse from destination to source without crossing components.
- **Exact Assignment Formatting**: Produces predictable, cleanly aligned text reports formatted for automated test grading.
- **Safe In-Process Flask Backend**: Avoids all shell execution to prevent command injection vulnerabilities; Python remains the single source of truth for all calculations.

---

## 📂 Project Structure

```
c:\Users\HARSHITHA REDDY\OneDrive\Desktop\DAA folder\
├── solution.py               # Official standalone submission: pure Python 3 stdin/stdout engine
├── campus_route_audit.py     # Pure Python 3 comprehensive algorithmic engine & CLI runner
├── test_solution.py          # Dedicated automated unit test suite for solution.py (10 tests)
├── test_audit.py             # Integration test suite for CLI, samples, and Flask API (12 tests)
├── app.py                    # Flask web application bridging solution.py to SVG UI
├── requirements.txt          # Python dependencies (Flask)
├── templates/
│   └── index.html            # University EOC Dashboard with SVG vector graph
├── static/
│   ├── css/
│   │   └── style.css         # Authoritative navy text, security blue accents, container queries
│   └── js/
│       └── app.js            # Interactive SVG graph visualizer, draggable nodes & API bridge
├── samples/
│   ├── problem_sample1.txt   # Official Problem 02 Sample Case 1 raw stdin
│   ├── problem_sample2.txt   # Official Problem 02 Sample Case 2 raw stdin
│   ├── sample1_connected.txt # Sample Case 1: Standard connected campus grid
│   └── sample2_hazard.txt    # Sample Case 2: Disconnected campus with isolated hazard zone
└── README.md                 # Project documentation & run instructions
```

---

## 💻 Windows Setup & Run Instructions

### Step 1: Environment Setup

Open **PowerShell** or **Command Prompt** in the project directory:
```powershell
cd "c:\Users\HARSHITHA REDDY\OneDrive\Desktop\DAA folder"
```

*(Optional but recommended)* Create and activate a Python virtual environment:
```powershell
# In PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install requirements:
```powershell
pip install -r requirements.txt
```

---

### Step 2: Run Official Challenge Solution (`solution.py`)

`solution.py` operates as a standalone script using standard I/O streams (`sys.stdin` and `sys.stdout`). It has **zero external library dependencies** (standard library only).

#### In PowerShell:
```powershell
# Run Sample Case 1:
Get-Content samples\problem_sample1.txt | python solution.py

# Run Sample Case 2:
Get-Content samples\problem_sample2.txt | python solution.py
```

#### In Windows Command Prompt (`cmd.exe`):
```cmd
python solution.py < samples\problem_sample1.txt
python solution.py < samples\problem_sample2.txt
```

#### Expected Output for Sample Case 1:
```text
COMPONENTS 2
LABELS 0 0 0 0 4 4
DFS 0 1 3 2
BFS 0 1 2 3
ROUTE 3 2 0 1 3
ROUTE 5 UNREACHABLE
ROUTE 0 0 0
```

#### Expected Output for Sample Case 2:
```text
COMPONENTS 3
LABELS 0 1 2
DFS 1
BFS 1
ROUTE 1 0 1
ROUTE 0 UNREACHABLE
```

---

### Step 3: Run the Interactive Web Dashboard

Launch the lightweight Flask application:
```powershell
python app.py
```

Once started, open your web browser to:
```
http://127.0.0.1:5000
```

#### Key Dashboard Capabilities:
- **Sample Case 1 & 2 Quick-Load**: Populates inputs and immediately executes the real Python algorithm via `POST /api/audit`.
- **Interactive SVG Vector Map**: Scalable vector campus layout with component color-coding, draggable nodes, and illuminated shortest routes.
- **Exact Assignment Console**: Displays verbatim `sys.stdout` text matching challenge specifications with a one-click **Copy Text** button.
- **One-Click Script Download**: Download [`solution.py`](file:///c:/Users/HARSHITHA%20REDDY/OneDrive/Desktop/DAA%20folder/solution.py) directly from the header navigation.
- **Security & Safety**: Calls Python functions directly in-process without any shell execution (`shell=False`), preventing command injection vulnerabilities.

---

### Step 4: Run Automated Tests

Run the dedicated test suite for `solution.py`:
```powershell
python test_solution.py -v
```
Expected output:
```text
test_edges_supplied_in_unsorted_order_and_reversed_endpoints ... ok
test_graph_with_no_edges ... ok
test_multiple_disconnected_components ... ok
test_multiple_reachable_and_unreachable_targets_preserve_order ... ok
test_multiple_shortest_paths_deterministic_bfs_parents ... ok
test_one_isolated_vertex ... ok
test_sample_1_exact ... ok
test_sample_2_exact ... ok
test_single_vertex_graph ... ok
test_source_to_itself ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.981s

OK
```

Run the complete integration and API test suite:
```powershell
python test_audit.py
```
Expected output:
```text
............
----------------------------------------------------------------------
Ran 12 tests in 1.247s

OK
```
