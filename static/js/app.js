/**
 * Campus Reachability and Emergency Route Audit
 * Interactive SVG Dashboard & Python Backend Controller
 * University Emergency Operations Center (EOC)
 */

// Application State
let currentAuditResult = null;
let selectedTarget = null;
let svgNodes = []; // { id, x, y, vx, vy, isDragging, compId, isHub }
let svgEdges = []; // { source, target }
let isDraggingNode = null;
let dragOffset = { x: 0, y: 0 };

// Component Colors Palette
const COMPONENT_COLORS = [
    '#2563eb', // Comp 0: Royal Blue
    '#059669', // Comp 1: Emerald
    '#d97706', // Comp 2: Amber
    '#7c3aed', // Comp 3: Purple
    '#0891b2', // Comp 4: Cyan
    '#db2777', // Comp 5: Rose
    '#4f46e5', // Comp 6: Indigo
    '#65a30d', // Comp 7: Lime
    '#ea580c'  // Comp 8: Orange
];

function getComponentColor(compId) {
    return COMPONENT_COLORS[compId % COMPONENT_COLORS.length];
}

// DOM Elements
const numVerticesInput = document.getElementById('numVertices');
const sourceVertexInput = document.getElementById('sourceVertex');
const edgesInput = document.getElementById('edgesInput');
const targetsInput = document.getElementById('targetsInput');
const edgeCountHint = document.getElementById('edgeCountHint');
const validationAlert = document.getElementById('validationAlert');

const btnRunAudit = document.getElementById('btnRunAudit');
const btnSample1 = document.getElementById('btnSample1');
const btnSample2 = document.getElementById('btnSample2');
const btnReset = document.getElementById('btnReset');
const btnCenterSvg = document.getElementById('btnCenterSvg');
const btnCopyConsole = document.getElementById('btnCopyConsole');
const routeHighlightSelect = document.getElementById('routeHighlightSelect');

// Metric Elements
const statV = document.getElementById('statV');
const statE = document.getElementById('statE');
const statC = document.getElementById('statC');
const statS = document.getElementById('statS');
const connectivityBadge = document.getElementById('connectivityBadge');

// Output Panels
const exactOutputPre = document.getElementById('exactOutputPre');
const componentsCardsGrid = document.getElementById('componentsCardsGrid');
const labelsStrip = document.getElementById('labelsStrip');
const dfsChain = document.getElementById('dfsChain');
const bfsChain = document.getElementById('bfsChain');
const routesTableBody = document.getElementById('routesTableBody');
const componentLegendList = document.getElementById('componentLegendList');

// SVG Elements
const campusSvg = document.getElementById('campusSvg');
const svgEdgesLayer = document.getElementById('svgEdgesLayer');
const svgRouteLayer = document.getElementById('svgRouteLayer');
const svgNodesLayer = document.getElementById('svgNodesLayer');

// -----------------------------------------------------------------------------
// TAB NAVIGATION
// -----------------------------------------------------------------------------
document.querySelectorAll('.tab-button').forEach(tabBtn => {
    tabBtn.addEventListener('click', () => {
        document.querySelectorAll('.tab-button').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

        tabBtn.classList.add('active');
        tabBtn.setAttribute('aria-selected', 'true');
        const panelId = tabBtn.getAttribute('aria-controls');
        const targetPanel = document.getElementById(panelId);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }
    });
});

// -----------------------------------------------------------------------------
// INPUT VALIDATION & REAL-TIME FEEDBACK
// -----------------------------------------------------------------------------
function updateEdgeCountHint() {
    const lines = edgesInput.value.split('\n').filter(l => l.trim() && !l.trim().startswith('#'));
    edgeCountHint.textContent = `${lines.length} edges`;
}
edgesInput.addEventListener('input', updateEdgeCountHint);

function clearValidationError() {
    validationAlert.style.display = 'none';
    validationAlert.textContent = '';
}

function showValidationError(msg) {
    validationAlert.textContent = msg;
    validationAlert.style.display = 'block';
}

function validateClientInputs() {
    clearValidationError();
    const n = parseInt(numVerticesInput.value, 10);
    const s = parseInt(sourceVertexInput.value, 10);

    if (isNaN(n) || n < 1 || n > 200) {
        showValidationError('Total vertices (n) must be an integer between 1 and 200.');
        return false;
    }

    if (isNaN(s) || s < 0 || s >= n) {
        showValidationError(`Emergency Hub (s) must be an integer between 0 and ${n - 1}.`);
        return false;
    }

    const lines = edgesInput.value.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || line.startsWith('#')) continue;
        const parts = line.split(/\s+/);
        if (parts.length < 2) {
            showValidationError(`Invalid edge specification on line ${i + 1}: '${line}'. Must be 'u v'.`);
            return false;
        }
        const u = parseInt(parts[0], 10);
        const v = parseInt(parts[1], 10);
        if (isNaN(u) || isNaN(v) || u < 0 || u >= n || v < 0 || v >= n) {
            showValidationError(`Edge endpoint out of range on line ${i + 1}: (${parts[0]}, ${parts[1]}). Vertices must be in [0, ${n - 1}].`);
            return false;
        }
    }

    const targetTokens = targetsInput.value.trim().split(/\s+/).filter(t => t);
    for (const tok of targetTokens) {
        const t = parseInt(tok, 10);
        if (isNaN(t) || t < 0 || t >= n) {
            showValidationError(`Target vertex '${tok}' is out of range. Vertices must be in [0, ${n - 1}].`);
            return false;
        }
    }

    return true;
}

// -----------------------------------------------------------------------------
// SAMPLE DATASETS & RESET
// -----------------------------------------------------------------------------
async function loadSampleCase(sampleId) {
    clearValidationError();
    try {
        const res = await fetch(`/api/sample/${sampleId}`);
        if (res.ok) {
            const data = await res.json();
            numVerticesInput.value = data.n;
            sourceVertexInput.value = data.source;
            edgesInput.value = data.edges_text;
            targetsInput.value = data.targets_text;
        } else {
            // Fallback default
            if (sampleId === 1) {
                numVerticesInput.value = '6';
                sourceVertexInput.value = '0';
                edgesInput.value = '0 2\n0 1\n1 3\n2 3\n4 5';
                targetsInput.value = '3\n5\n0';
            } else {
                numVerticesInput.value = '3';
                sourceVertexInput.value = '1';
                edgesInput.value = '';
                targetsInput.value = '1\n0';
            }
        }
    } catch (err) {
        console.warn('Could not fetch sample from server, using built-in values:', err);
        if (sampleId === 1) {
            numVerticesInput.value = '6';
            sourceVertexInput.value = '0';
            edgesInput.value = '0 2\n0 1\n1 3\n2 3\n4 5';
            targetsInput.value = '3\n5\n0';
        } else {
            numVerticesInput.value = '3';
            sourceVertexInput.value = '1';
            edgesInput.value = '';
            targetsInput.value = '1\n0';
        }
    }
    updateEdgeCountHint();
    triggerAudit();
}

btnSample1.addEventListener('click', () => loadSampleCase(1));
btnSample2.addEventListener('click', () => loadSampleCase(2));

btnReset.addEventListener('click', () => {
    numVerticesInput.value = '1';
    sourceVertexInput.value = '0';
    edgesInput.value = '';
    targetsInput.value = '0';
    clearValidationError();
    updateEdgeCountHint();
    triggerAudit();
});

btnCopyConsole.addEventListener('click', () => {
    const text = exactOutputPre.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btnCopyConsole.innerHTML;
        btnCopyConsole.innerHTML = '<span>✓ Copied!</span>';
        setTimeout(() => { btnCopyConsole.innerHTML = originalText; }, 2000);
    });
});

// -----------------------------------------------------------------------------
// BACKEND AUDIT EXECUTION (PYTHON SOURCE OF TRUTH)
// -----------------------------------------------------------------------------
async function triggerAudit() {
    if (!validateClientInputs()) return;

    const payload = {
        n: parseInt(numVerticesInput.value, 10),
        edges_text: edgesInput.value.trim(),
        source: parseInt(sourceVertexInput.value, 10),
        targets_text: targetsInput.value.trim()
    };

    try {
        btnRunAudit.disabled = true;
        btnRunAudit.textContent = 'Auditing...';

        const res = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showValidationError(data.error || 'Failed to execute audit on backend.');
            return;
        }

        currentAuditResult = data;
        renderAuditDashboard(data);
    } catch (err) {
        console.error('Audit execution error:', err);
        showValidationError('Network or server error while connecting to Flask backend.');
    } finally {
        btnRunAudit.disabled = false;
        btnRunAudit.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Run Emergency Audit
        `;
    }
}

btnRunAudit.addEventListener('click', triggerAudit);

// -----------------------------------------------------------------------------
// RENDER DASHBOARD RESULTS
// -----------------------------------------------------------------------------
function renderAuditDashboard(data) {
    // 1. Update Metrics
    statV.textContent = data.n;
    statE.textContent = data.m;
    statC.textContent = data.num_components;
    statS.textContent = data.source;

    if (data.num_components === 1) {
        connectivityBadge.textContent = 'Fully Connected';
        connectivityBadge.className = 'status-pill status-connected';
    } else {
        connectivityBadge.textContent = `${data.num_components} Disconnected Areas`;
        connectivityBadge.className = 'status-pill status-disconnected';
    }

    // 2. Exact Assignment Output Console
    exactOutputPre.textContent = data.exact_output;

    // 3. Components & Labels Panel
    renderComponentsPanel(data);

    // 4. Traversals Panel
    renderTraversalsPanel(data);

    // 5. Routes Table
    renderRoutesTable(data);

    // 6. SVG Graph Visualization
    setupSvgGraph(data);
}

function renderComponentsPanel(data) {
    componentsCardsGrid.innerHTML = '';
    const componentRoots = Object.keys(data.component_groups).map(Number).sort((a, b) => a - b);

    componentRoots.forEach((root, idx) => {
        const members = data.component_groups[root];
        const card = document.createElement('div');
        card.className = 'component-card';
        card.style.borderLeftColor = getComponentColor(idx);

        card.innerHTML = `
            <span class="component-card-title" style="color: ${getComponentColor(idx)}">
                Component (Root ${root})
            </span>
            <div class="component-card-members">
                Vertices: [${members.join(', ')}]
            </div>
            <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">
                Size: ${members.length} location${members.length > 1 ? 's' : ''}
            </div>
        `;
        componentsCardsGrid.appendChild(card);
    });

    // LABELS array
    labelsStrip.innerHTML = '';
    data.component_labels.forEach((lbl, idx) => {
        const cell = document.createElement('div');
        cell.className = 'label-cell';
        const compIdx = componentRoots.indexOf(lbl);
        const color = getComponentColor(compIdx >= 0 ? compIdx : 0);

        cell.innerHTML = `
            <span class="label-idx">v = ${idx}</span>
            <span class="label-val" style="color: ${color}">${lbl}</span>
        `;
        labelsStrip.appendChild(cell);
    });

    // SVG Component Legend
    componentLegendList.innerHTML = '';
    componentRoots.forEach((root, idx) => {
        const color = getComponentColor(idx);
        const item = document.createElement('span');
        item.style.display = 'inline-flex';
        item.style.alignItems = 'center';
        item.style.gap = '5px';
        item.style.marginRight = '8px';
        item.innerHTML = `<span style="width: 10px; height: 10px; border-radius: 50%; background-color: ${color}; display: inline-block;"></span> Comp ${root}`;
        componentLegendList.appendChild(item);
    });
}

function renderTraversalsPanel(data) {
    if (data.dfs_order && data.dfs_order.length > 0) {
        dfsChain.innerHTML = data.dfs_order.map(v => `<span class="step-badge">${v}</span>`).join(' <span style="color: #94a3b8">➔</span> ');
    } else {
        dfsChain.textContent = '(None)';
    }

    if (data.bfs_order && data.bfs_order.length > 0) {
        bfsChain.innerHTML = data.bfs_order.map(v => `<span class="step-badge" style="background-color: #2563eb; color: #fff;">${v}</span>`).join(' <span style="color: #94a3b8">➔</span> ');
    } else {
        bfsChain.textContent = '(None)';
    }
}

function renderRoutesTable(data) {
    routesTableBody.innerHTML = '';
    routeHighlightSelect.innerHTML = '<option value="">-- Select Target Route --</option>';

    if (!data.routes || data.routes.length === 0) {
        routesTableBody.innerHTML = '<tr><td colspan="5" class="table-empty">No target queries requested.</td></tr>';
        return;
    }

    data.routes.forEach(r => {
        const tr = document.createElement('tr');
        const isReachable = r.is_reachable;

        const opt = document.createElement('option');
        opt.value = r.target;
        opt.textContent = `Target ${r.target}: ${isReachable ? `Dist ${r.distance} hops` : 'UNREACHABLE'}`;
        routeHighlightSelect.appendChild(opt);

        tr.innerHTML = `
            <td data-label="Target (t)"><strong>Vertex ${r.target}</strong></td>
            <td data-label="Distance (d)">${isReachable ? r.distance : '<span style="color: #b91c1c; font-weight: 700;">INF</span>'}</td>
            <td data-label="Status">
                <span class="${isReachable ? 'badge-status-reachable' : 'badge-status-unreachable'}">
                    ${isReachable ? (r.target === data.source ? 'HUB' : 'REACHABLE') : 'UNREACHABLE'}
                </span>
            </td>
            <td data-label="Shortest Route Path">
                <code>${isReachable ? r.path.join(' ➔ ') : 'NO WALKWAY ROUTE'}</code>
            </td>
            <td data-label="Action">
                ${isReachable ? `
                    <button type="button" class="btn-inspect" data-target="${r.target}">
                        Highlight
                    </button>
                ` : '-'}
            </td>
        `;
        routesTableBody.appendChild(tr);
    });

    document.querySelectorAll('.btn-inspect').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const t = parseInt(e.target.getAttribute('data-target'), 10);
            selectActiveTargetRoute(t);
        });
    });
}

routeHighlightSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    selectActiveTargetRoute(val === '' ? null : parseInt(val, 10));
});

function selectActiveTargetRoute(t) {
    selectedTarget = t;
    routeHighlightSelect.value = t !== null ? t : '';
    drawSvgActiveRoute();
}

// -----------------------------------------------------------------------------
// SVG GRAPH VISUALIZATION & INTERACTIVITY
// -----------------------------------------------------------------------------
function setupSvgGraph(data) {
    const width = 800;
    const height = 440;
    const n = data.n;

    // Component roots mapping for color indexing
    const componentRoots = Object.keys(data.component_groups).map(Number).sort((a, b) => a - b);

    // Group vertices by component for clear cluster distribution
    const componentCount = componentRoots.length;
    const clusterCenters = [];

    if (componentCount === 1) {
        clusterCenters.push({ cx: width / 2, cy: height / 2, r: Math.min(width, height) * 0.35 });
    } else {
        const angleStep = (2 * Math.PI) / componentCount;
        const mainRadius = Math.min(width, height) * 0.28;
        componentRoots.forEach((root, idx) => {
            const angle = idx * angleStep;
            clusterCenters.push({
                cx: width / 2 + mainRadius * Math.cos(angle),
                cy: height / 2 + mainRadius * Math.sin(angle),
                r: 80 + Math.min(60, data.component_groups[root].length * 15)
            });
        });
    }

    // Build node objects
    svgNodes = [];
    componentRoots.forEach((root, compIdx) => {
        const cluster = clusterCenters[compIdx];
        const members = data.component_groups[root];
        const mCount = members.length;

        members.forEach((v, memberIdx) => {
            let x, y;
            if (mCount === 1) {
                x = cluster.cx;
                y = cluster.cy;
            } else {
                const subAngle = (2 * Math.PI / mCount) * memberIdx;
                x = cluster.cx + cluster.r * Math.cos(subAngle);
                y = cluster.cy + cluster.r * Math.sin(subAngle);
            }

            svgNodes.push({
                id: v,
                x: Math.max(40, Math.min(width - 40, x)),
                y: Math.max(40, Math.min(height - 40, y)),
                compId: compIdx,
                rootLabel: root,
                isHub: v === data.source,
                isDragging: false
            });
        });
    });

    // Ensure sorted by id
    svgNodes.sort((a, b) => a.id - b.id);

    // Build edges
    const seenEdges = new Set();
    svgEdges = [];
    data.edges.forEach(([u, v]) => {
        const key = [u, v].sort().join('--');
        if (!seenEdges.has(key)) {
            seenEdges.add(key);
            svgEdges.push({ source: u, target: v });
        }
    });

    renderSvgGraph();
}

function renderSvgGraph() {
    // 1. Render Edges
    svgEdgesLayer.innerHTML = '';
    const nodeMap = {};
    svgNodes.forEach(n => { nodeMap[n.id] = n; });

    svgEdges.forEach(e => {
        const uNode = nodeMap[e.source];
        const vNode = nodeMap[e.target];
        if (!uNode || !vNode) return;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', uNode.x);
        line.setAttribute('y1', uNode.y);
        line.setAttribute('x2', vNode.x);
        line.setAttribute('y2', vNode.y);
        line.setAttribute('class', 'svg-edge');
        line.setAttribute('id', `edge-${Math.min(e.source, e.target)}-${Math.max(e.source, e.target)}`);
        svgEdgesLayer.appendChild(line);
    });

    // 2. Render Nodes
    svgNodesLayer.innerHTML = '';
    svgNodes.forEach(node => {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'svg-node-group');
        g.setAttribute('id', `node-group-${node.id}`);
        g.setAttribute('transform', `translate(${node.x}, ${node.y})`);

        // Emergency Hub Outer Ring
        if (node.isHub) {
            const hubRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            hubRing.setAttribute('r', 27);
            hubRing.setAttribute('class', 'svg-node-hub-ring');
            g.appendChild(hubRing);
        }

        // Selected Target Route Indicator Ring
        const targetRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        targetRing.setAttribute('r', 24);
        targetRing.setAttribute('class', 'svg-node-route-highlight');
        targetRing.setAttribute('id', `target-ring-${node.id}`);
        targetRing.style.display = 'none';
        g.appendChild(targetRing);

        // Core Circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', node.isHub ? 20 : 17);
        circle.setAttribute('fill', getComponentColor(node.compId));
        circle.setAttribute('class', 'svg-node-circle');
        g.appendChild(circle);

        // Vertex Number Text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'svg-node-text');
        text.textContent = node.id;
        g.appendChild(text);

        // Hub Tag text underneath
        if (node.isHub) {
            const hubTag = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            hubTag.setAttribute('class', 'svg-node-label');
            hubTag.setAttribute('y', 23);
            hubTag.textContent = '★ HUB';
            g.appendChild(hubTag);
        }

        // Drag & Click Events
        setupNodeInteractions(g, node);

        svgNodesLayer.appendChild(g);
    });

    drawSvgActiveRoute();
}

function drawSvgActiveRoute() {
    svgRouteLayer.innerHTML = '';
    const nodeMap = {};
    svgNodes.forEach(n => {
        nodeMap[n.id] = n;
        const ring = document.getElementById(`target-ring-${n.id}`);
        if (ring) ring.style.display = 'none';
    });

    if (selectedTarget === null || !currentAuditResult) return;

    const routeRecord = currentAuditResult.routes.find(r => r.target === selectedTarget);
    if (!routeRecord || !routeRecord.is_reachable) return;

    const path = routeRecord.path;

    // Highlight nodes on the route
    path.forEach(v => {
        const ring = document.getElementById(`target-ring-${v}`);
        if (ring) ring.style.display = 'block';
    });

    // Draw glowing route path on SVG
    for (let i = 0; i < path.length - 1; i++) {
        const u = path[i];
        const v = path[i + 1];
        const uNode = nodeMap[u];
        const vNode = nodeMap[v];
        if (!uNode || !vNode) continue;

        const routeLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        routeLine.setAttribute('x1', uNode.x);
        routeLine.setAttribute('y1', uNode.y);
        routeLine.setAttribute('x2', vNode.x);
        routeLine.setAttribute('y2', vNode.y);
        routeLine.setAttribute('class', 'svg-edge-route');
        routeLine.setAttribute('filter', 'url(#routeGlow)');
        svgRouteLayer.appendChild(routeLine);
    }
}

// -----------------------------------------------------------------------------
// SVG DRAG AND DROP & NODE INSPECT
// -----------------------------------------------------------------------------
function setupNodeInteractions(element, node) {
    let hasMoved = false;

    function onPointerDown(e) {
        e.preventDefault();
        isDraggingNode = node;
        hasMoved = false;

        const pt = getSvgCoords(e);
        dragOffset.x = pt.x - node.x;
        dragOffset.y = pt.y - node.y;

        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
    }

    function onPointerMove(e) {
        if (!isDraggingNode) return;
        hasMoved = true;
        const pt = getSvgCoords(e);
        const newX = Math.max(30, Math.min(770, pt.x - dragOffset.x));
        const newY = Math.max(30, Math.min(410, pt.y - dragOffset.y));

        isDraggingNode.x = newX;
        isDraggingNode.y = newY;

        // Update group position
        element.setAttribute('transform', `translate(${newX}, ${newY})`);

        // Update connected edges
        updateConnectedEdges(isDraggingNode.id);
        drawSvgActiveRoute();
    }

    function onPointerUp() {
        window.removeEventListener('pointermove', onPointerMove);
        window.removeEventListener('pointerup', onPointerUp);
        if (!hasMoved) {
            // Treat as click / route selection
            selectActiveTargetRoute(node.id);
        }
        isDraggingNode = null;
    }

    element.addEventListener('pointerdown', onPointerDown);
}

function getSvgCoords(e) {
    const rect = campusSvg.getBoundingClientRect();
    const scaleX = 800 / rect.width;
    const scaleY = 440 / rect.height;
    return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
    };
}

function updateConnectedEdges(nodeId) {
    const nodeMap = {};
    svgNodes.forEach(n => { nodeMap[n.id] = n; });
    const dragged = nodeMap[nodeId];
    if (!dragged) return;

    svgEdges.forEach(e => {
        if (e.source === nodeId || e.target === nodeId) {
            const edgeEl = document.getElementById(`edge-${Math.min(e.source, e.target)}-${Math.max(e.source, e.target)}`);
            if (edgeEl) {
                const uNode = nodeMap[e.source];
                const vNode = nodeMap[e.target];
                if (uNode && vNode) {
                    edgeEl.setAttribute('x1', uNode.x);
                    edgeEl.setAttribute('y1', uNode.y);
                    edgeEl.setAttribute('x2', vNode.x);
                    edgeEl.setAttribute('y2', vNode.y);
                }
            }
        }
    });
}

btnCenterSvg.addEventListener('click', () => {
    if (currentAuditResult) {
        setupSvgGraph(currentAuditResult);
    }
});

// Boot initial state on load
window.addEventListener('DOMContentLoaded', () => {
    loadSampleCase(1);
});
