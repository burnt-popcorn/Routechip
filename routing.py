"""RouteChip Routing Module (DAA: Design and Analysis of Algorithms).

Module 3: Dijkstra's Algorithm (3.13)
Implements Dijkstra's Single-Source Shortest Path algorithm using a Greedy
approach with a Min-Heap (Priority Queue) on weighted network topologies.

Key Concepts:
- Greedy Choice Property: Always visit the unvisited node with minimum tentative distance.
- Optimal Substructure: Subpaths of shortest paths are themselves shortest paths.
- Relaxation Step: if d[u] + w(u, v) < d[v], update d[v] = d[u] + w(u, v) and parent[v] = u.
- Time Complexity: O((V + E) log V) with binary heap.
- Space Complexity: O(V + E) for adjacency list, distances, heap, and predecessors.
"""

from copy import deepcopy
import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

# Default 5-node topology with router 'E' intentionally disconnected/isolated
GRAPH: Dict[str, Dict[str, int]] = {
    'A': {'B': 4, 'C': 2},
    'B': {'A': 4, 'C': 5, 'D': 3},
    'C': {'A': 2, 'B': 5, 'D': 2},
    'D': {'B': 3, 'C': 2},
    'E': {},
}

PRESET_TOPOLOGIES: Dict[str, Dict[str, Dict[str, int]]] = {
    'Default (5 Routers, Isolated E)': GRAPH,
    'Ring Network (A-B-C-D-E)': {
        'A': {'B': 3, 'E': 6},
        'B': {'A': 3, 'C': 2},
        'C': {'B': 2, 'D': 4},
        'D': {'C': 4, 'E': 1},
        'E': {'D': 1, 'A': 6},
    },
    'Full Mesh (4 Routers)': {
        'A': {'B': 2, 'C': 5, 'D': 7},
        'B': {'A': 2, 'C': 1, 'D': 4},
        'C': {'A': 5, 'B': 1, 'D': 2},
        'D': {'A': 7, 'B': 4, 'C': 2},
    },
    'Star Network (Central Hub C)': {
        'A': {'C': 3},
        'B': {'C': 1},
        'C': {'A': 3, 'B': 1, 'D': 4, 'E': 5},
        'D': {'C': 4},
        'E': {'C': 5},
    },
    'Linear Backbone (A-B-C-D-E)': {
        'A': {'B': 2},
        'B': {'A': 2, 'C': 3},
        'C': {'B': 3, 'D': 1},
        'D': {'C': 1, 'E': 4},
        'E': {'D': 4},
    },
}


def shortest_path(graph: Dict[str, Dict[str, int]], start: str, end: str) -> Tuple[List[str], Optional[int], List[str]]:
    """Standard Dijkstra's implementation preserving existing API contract.

    Returns:
        (path, total_cost, trace_steps)
    """
    if start not in graph or end not in graph:
        raise ValueError('Unknown router')

    distances: Dict[str, float] = {node: float('inf') for node in graph}
    distances[start] = 0
    previous: Dict[str, str] = {}
    heap: List[Tuple[float, str]] = [(0, start)]
    visited: Set[str] = set()
    steps: List[str] = []

    while heap:
        distance, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        steps.append(f'Visit {node}, current distance = {distance}')
        if node == end:
            break

        for neighbor, weight in graph[node].items():
            if weight < 0:
                raise ValueError('Dijkstra requires non-negative weights')
            new_distance = distance + weight
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = node
                heapq.heappush(heap, (new_distance, neighbor))
                steps.append(f'Relax {node} → {neighbor}: distance = {new_distance}')

    if distances[end] == float('inf'):
        return [], None, steps

    path: List[str] = []
    node = end
    while node != start:
        path.append(node)
        node = previous[node]
    path.append(start)
    path.reverse()
    return path, int(distances[end]), steps


def dijkstra_detailed(
    graph: Dict[str, Dict[str, int]], start: str, end: str
) -> Dict[str, Any]:
    """Detailed Dijkstra execution engine with full priority queue snapshots,

    distance tables at every iteration, and analytical metrics.
    """
    if start not in graph or end not in graph:
        raise ValueError(f"Unknown router: start '{start}' or end '{end}' not found in topology")

    distances: Dict[str, float] = {node: float('inf') for node in graph}
    distances[start] = 0
    previous: Dict[str, Optional[str]] = {node: None for node in graph}
    heap: List[Tuple[float, str]] = [(0, start)]
    visited: Set[str] = set()
    steps: List[str] = []
    history: List[Dict[str, Any]] = []

    # Record initialization snapshot
    history.append({
        'step_num': 0,
        'action': 'INITIALIZATION',
        'current_node': None,
        'neighbor': None,
        'edge_weight': None,
        'distance': 0,
        'heap_contents': sorted(list(heap)),
        'distances_snapshot': dict(distances),
        'visited_snapshot': set(visited),
        'previous_snapshot': dict(previous),
        'explanation': f"Initialize: Set dist[{start}] = 0, all other nodes = ∞. Push (0, '{start}') to priority queue.",
    })

    relaxations_count = 0
    heap_operations_count = 1  # 1 push so far
    step_num = 1

    while heap:
        distance, node = heapq.heappop(heap)
        heap_operations_count += 1

        if node in visited:
            continue

        visited.add(node)
        steps.append(f'Visit {node}, current distance = {distance}')

        history.append({
            'step_num': step_num,
            'action': 'EXTRACT_MIN',
            'current_node': node,
            'neighbor': None,
            'edge_weight': None,
            'distance': distance,
            'heap_contents': sorted(list(heap)),
            'distances_snapshot': dict(distances),
            'visited_snapshot': set(visited),
            'previous_snapshot': dict(previous),
            'explanation': (
                f"Greedy choice: Dequeue node '{node}' with minimum tentative distance = {distance}. "
                f"Mark '{node}' as VISITED/FINALIZED."
            ),
        })
        step_num += 1

        if node == end:
            history.append({
                'step_num': step_num,
                'action': 'REACHED_DEST',
                'current_node': node,
                'neighbor': None,
                'edge_weight': None,
                'distance': distance,
                'heap_contents': sorted(list(heap)),
                'distances_snapshot': dict(distances),
                'visited_snapshot': set(visited),
                'previous_snapshot': dict(previous),
                'explanation': f"Target destination '{end}' extracted from min-heap. Shortest path guaranteed by Greedy Choice property.",
            })
            step_num += 1
            break

        for neighbor, weight in sorted(graph[node].items()):
            if weight < 0:
                raise ValueError('Dijkstra requires non-negative weights')

            new_distance = distance + weight
            if new_distance < distances[neighbor]:
                old_distance = distances[neighbor]
                distances[neighbor] = new_distance
                previous[neighbor] = node
                heapq.heappush(heap, (new_distance, neighbor))
                heap_operations_count += 1
                relaxations_count += 1

                steps.append(f'Relax {node} → {neighbor}: distance = {new_distance}')
                history.append({
                    'step_num': step_num,
                    'action': 'RELAXATION',
                    'current_node': node,
                    'neighbor': neighbor,
                    'edge_weight': weight,
                    'distance': new_distance,
                    'heap_contents': sorted(list(heap)),
                    'distances_snapshot': dict(distances),
                    'visited_snapshot': set(visited),
                    'previous_snapshot': dict(previous),
                    'explanation': (
                        f"Relax edge ({node} → {neighbor}, weight={weight}): "
                        f"New dist = {distance} + {weight} = {new_distance} < previous "
                        f"({old_distance if old_distance != float('inf') else '∞'}). "
                        f"Update parent[{neighbor}] = '{node}'."
                    ),
                })
                step_num += 1

    # Reconstruct path
    is_reachable = distances[end] != float('inf')
    if is_reachable:
        path = []
        curr = end
        while curr != start:
            path.append(curr)
            curr = previous[curr]  # type: ignore
        path.append(start)
        path.reverse()
        cost: Optional[int] = int(distances[end])
    else:
        path = []
        cost = None

    # Graph properties
    total_vertices = len(graph)
    total_edges = sum(len(neighbors) for neighbors in graph.values()) // 2

    return {
        'path': path,
        'cost': cost,
        'steps': steps,
        'history': history,
        'final_distances': distances,
        'previous': previous,
        'visited': visited,
        'is_reachable': is_reachable,
        'metrics': {
            'total_vertices': total_vertices,
            'total_edges': total_edges,
            'relaxations_count': relaxations_count,
            'heap_operations_count': heap_operations_count,
            'time_complexity': 'O((V + E) log V)',
            'space_complexity': 'O(V + E)',
        },
    }


def get_network_dot(
    graph: Dict[str, Dict[str, int]],
    path: Optional[List[str]] = None,
    source: Optional[str] = None,
    destination: Optional[str] = None,
    visited: Optional[Set[str]] = None,
) -> str:
    """Generate Graphviz DOT string for network topology with path highlighting."""
    path = path or []
    visited = visited or set()
    path_set = set(path)

    # Path edges set for quick undirected lookup
    path_edges = set()
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        path_edges.add((u, v))
        path_edges.add((v, u))

    dot_lines = [
        'graph NetworkTopology {',
        '  graph [layout=neato, overlap=false, splines=true, bgcolor="transparent", margin=0.1];',
        '  node [fontname="Helvetica, Arial, sans-serif", fontsize=12, shape=circle, style="filled,bold", width=0.55, height=0.55];',
        '  edge [fontname="Helvetica, Arial, sans-serif", fontsize=11, fontcolor="#334155", len=1.4];',
        '',
    ]

    # Style nodes
    for node in sorted(graph.keys()):
        is_src = node == source
        is_dst = node == destination
        in_path = node in path_set
        is_vis = node in visited

        if is_src and is_dst:
            # Same router
            style = 'fillcolor="#ecfdf5", color="#059669", fontcolor="#065f46", penwidth=3.5'
            label = f'{node}\\n[SRC/DST]'
        elif is_src:
            style = 'fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d", penwidth=3.0'
            label = f'{node}\\n[SRC]'
        elif is_dst:
            style = 'fillcolor="#fef3c7", color="#d97706", fontcolor="#78350f", penwidth=3.0'
            label = f'{node}\\n[DST]'
        elif in_path:
            style = 'fillcolor="#e0f2fe", color="#0284c7", fontcolor="#075985", penwidth=2.5'
            label = f'{node}'
        elif is_vis:
            style = 'fillcolor="#f3e8ff", color="#9333ea", fontcolor="#581c87", penwidth=2.0'
            label = f'{node}'
        else:
            style = 'fillcolor="#f8fafc", color="#94a3b8", fontcolor="#334155", penwidth=1.5'
            label = f'{node}'

        dot_lines.append(f'  {node} [{style}, label="{label}"];')

    dot_lines.append('')

    # Render undirected edges once
    drawn_edges = set()
    for u, neighbors in sorted(graph.items()):
        for v, weight in sorted(neighbors.items()):
            edge_key = tuple(sorted([u, v]))
            if edge_key in drawn_edges:
                continue
            drawn_edges.add(edge_key)

            if (u, v) in path_edges:
                dot_lines.append(
                    f'  {u} -- {v} [label=" {weight}", color="#2563eb", fontcolor="#1d4ed8", penwidth=3.8];'
                )
            else:
                dot_lines.append(
                    f'  {u} -- {v} [label=" {weight}", color="#94a3b8", fontcolor="#64748b", penwidth=1.3];'
                )

    dot_lines.append('}')
    return '\n'.join(dot_lines)
