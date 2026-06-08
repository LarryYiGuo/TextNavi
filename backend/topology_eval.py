"""topology_eval.py — shared helpers for the paper-equivalent "useful top-1" metric.

The system's predictions and GT labels are in the *struct* namespace (e.g.
`poi02_green_trash_bin`). The paper's topology connectivity graph
(`backend/topology.json`) uses a coarser, *topology* namespace (e.g.
`dp_ms_entrance`) with about half as many nodes — multiple struct POIs map to
the same topology cell.

A prediction is "useful" (paper Table 4 metric) when the predicted topology cell
equals GT's, OR is a 1-hop neighbour of GT's in the topology graph.

The struct→topology mapping below is best-effort based on inspecting the 37
labeled photos plus the topology node names. Each comment explains the rationale.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent   # backend/  (this file lives at backend/topology_eval.py)

STRUCT_TO_TOPOLOGY = {
    # SenseA — 10 struct nodes → 5 topology cells
    "poi01_entrance_glass_door":   "dp_ms_entrance",          # entrance scene
    "poi02_green_trash_bin":       "dp_ms_entrance",          # bin sits in entrance alcove
    "poi03_black_drawer_cabinet":  "poi_component_drawer_wall",  # name match
    "poi04_wall_3d_printers":      "poi_3d_printer_table",    # printer cluster
    "poi05_desk_3d_printer":       "poi_3d_printer_table",    # printer cluster
    "poi06_small_open_3d_printer": "poi_3d_printer_table",    # printer cluster
    "poi07_cardboard_boxes":       "poi_3d_printer_table",    # boxes are on printer bench
    "poi08_to_atrium":             "atrium_entry",            # atrium-bound
    "poi09_qr_bookshelf":          "dp_bookshelf_qr",         # name match
    "poi10_metal_display_cabinet": "poi_component_drawer_wall",  # cabinet area

    # SenseB — 8 struct nodes → 5 topology cells
    "poi11_di_hub_glass_box":          "dp_studio_entry",       # entrance display case
    "poi12_wall_side_workbench":       "node_mid_studio",       # workbench in mid studio
    "poi14_main_work_table":           "node_mid_studio",       # main work area
    "poi15_floor_to_ceiling_windows":  "node_window_glass",     # window
    "poi16_green_sofa_side_table":     "node_window_glass",     # sofa adjacent to window
    "poi18_large_display_screen":      "node_mid_studio",       # TV in mid area
    "poi19_purple_chair_filming_table":"poi_orange_sofa_chair", # chair zone
    "poi20_two_tone_sofa_zone":        "poi_orange_sofa",       # sofa
}

# Scene assignment for each topology node (for adjacency lookup)
_TOPOLOGY_TO_SCENE = {}


def _load_topology():
    """Load and flatten the connectivity graph for fast lookups."""
    data = json.load(open(ROOT / "topology.json"))
    adj = {}
    for scene, nodes in data.items():
        for n, neighbours in nodes.items():
            adj[n] = set(neighbours)
            _TOPOLOGY_TO_SCENE[n] = scene
    return adj


_ADJ = _load_topology()


def to_topology(struct_id):
    """Map a struct ID (or None) to its topology cell, or None if unmapped."""
    return STRUCT_TO_TOPOLOGY.get(struct_id)


def is_useful(pred_struct, gt_struct, hop=1):
    """Paper-equivalent metric: True if predicted node is within `hop` edges of
    GT in the topology graph. hop=0 = strict (after coarsening), hop=1 = useful
    top-1 as in the paper's Table 4."""
    p = to_topology(pred_struct)
    g = to_topology(gt_struct)
    if p is None or g is None:
        return False
    if p == g:
        return True
    if hop >= 1 and p in _ADJ.get(g, set()):
        return True
    return False


def topo_distance(pred_struct, gt_struct, max_d=3):
    """BFS distance between predicted and GT topology cells. Returns max_d+1
    if unreachable within max_d steps."""
    p = to_topology(pred_struct)
    g = to_topology(gt_struct)
    if p is None or g is None:
        return max_d + 1
    if p == g:
        return 0
    frontier = {p}
    seen = {p}
    for d in range(1, max_d + 1):
        nxt = set()
        for n in frontier:
            for m in _ADJ.get(n, set()):
                if m == g:
                    return d
                if m not in seen:
                    nxt.add(m)
                    seen.add(m)
        frontier = nxt
        if not frontier:
            break
    return max_d + 1
