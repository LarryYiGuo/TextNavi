"""nav_router.py — goal-aware navigation: graph routing + instruction generation.

Built on top of the existing topology graph (`backend/topology.json`) and the
struct→topology mapping in `backend/topology_eval.py`. Pure functions; no I/O
side effects beyond module import.

Public API
----------
- ``find_path(current_struct, goal_struct)`` -> dict
- ``generate_instruction(current_struct, goal_struct, lang='en')`` -> str
- ``match_goal_text(goal_text, retriever, site_id=None)`` -> Optional[str]
- ``KNOWN_NODES`` -> set[str]   — every struct node we know about

Design notes
------------
- The user can be predicted at fine-grained *struct* nodes (e.g.
  ``poi05_desk_3d_printer``). The topology graph in ``topology.json`` is at
  coarser *topology* cells (e.g. ``poi_3d_printer_table``). Many struct nodes
  share a single topology cell — that's why 4 vs 5 is "useful but not strict".
- For routing we lift current/goal up to their topology cells, BFS the
  adjacency graph, and turn that into voice-friendly instructions.
- Three navigation regimes:
    1. ``arrived``: current_struct == goal_struct
    2. ``same_cell``: same topology cell, different struct → fall back to
       fine-grained local guidance using the struct's ``unique_features``.
    3. ``cross_cell``: BFS path through the topology graph; instruct the user
       to head toward the next topology cell on the path.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Optional

from topology_eval import STRUCT_TO_TOPOLOGY, _ADJ as TOPO_ADJ

ROOT = Path(__file__).resolve().parent  # backend/
TEXTMAP_PATH = ROOT / "data" / "textmap_clean.jsonl"


# ---------------------------------------------------------------------------
# Friendly names — voice-output strings for topology cells and struct nodes.
# ---------------------------------------------------------------------------
# Topology-cell friendly names (one entry per cell that appears in topology.json).
TOPOLOGY_FRIENDLY_EN: dict[str, str] = {
    # SCENE_A_MS
    "dp_ms_entrance":              "the Maker Space entrance",
    "atrium_entry":                "the atrium entry",
    "dp_bookshelf_qr":             "the QR bookshelf",
    "poi_3d_printer_table":        "the 3D printer area",
    "poi_component_drawer_wall":   "the component drawer wall",
    # SCENE_B_STUDIO
    "dp_studio_entry":             "the studio entrance",
    "node_window_glass":           "the window seating area",
    "poi_orange_sofa":             "the orange sofa zone",
    "poi_orange_sofa_chair":       "the orange chair area",
    "node_mid_studio":             "the central studio workspace",
}
TOPOLOGY_FRIENDLY_ZH: dict[str, str] = {
    "dp_ms_entrance":              "Maker Space 入口",
    "atrium_entry":                "中庭入口",
    "dp_bookshelf_qr":             "二维码书架区",
    "poi_3d_printer_table":        "3D 打印机区域",
    "poi_component_drawer_wall":   "元件抽屉墙区",
    "dp_studio_entry":             "工作室入口",
    "node_window_glass":           "窗边休息区",
    "poi_orange_sofa":             "橙色沙发区",
    "poi_orange_sofa_chair":       "橙色椅子区",
    "node_mid_studio":             "工作室中央工作区",
}


def _topo_friendly(topo: Optional[str], lang: str) -> str:
    if not topo:
        return "the destination" if lang == "en" else "目的地"
    table = TOPOLOGY_FRIENDLY_ZH if lang == "zh" else TOPOLOGY_FRIENDLY_EN
    return table.get(topo, topo.replace("_", " "))


# ---------------------------------------------------------------------------
# Struct-node short descriptions (loaded once from textmap_clean.jsonl). Used
# for "same_cell" disambiguation guidance and as the matching pool for
# ``match_goal_text``.
# ---------------------------------------------------------------------------
def _load_struct_meta() -> dict[str, dict]:
    meta: dict[str, dict] = {}
    if not TEXTMAP_PATH.exists():
        return meta
    for line in TEXTMAP_PATH.open():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        nid = rec["node_id"]
        # Short label: prettify the node id, e.g. "desk 3d printer"
        # (strip the leading "poiNN_" if present)
        label = nid
        if "_" in label:
            head, _, rest = label.partition("_")
            if head.startswith("poi") and head[3:].isdigit():
                label = rest
        label = label.replace("_", " ")
        meta[nid] = {
            "scene":              rec.get("scene", ""),
            "nl_text":            rec.get("nl_text", ""),
            "unique_features":    rec.get("unique_features", []),
            "short_label":        label,
            # Optional hand-written Chinese labels. When absent (older textmap),
            # zh output silently falls back to the English version.
            "short_label_zh":     rec.get("short_label_zh"),
            "unique_features_zh": rec.get("unique_features_zh") or [],
        }
    return meta


STRUCT_META: dict[str, dict] = _load_struct_meta()
KNOWN_NODES: set[str] = set(STRUCT_META.keys())


def _struct_short(struct_id: Optional[str], lang: str) -> str:
    """Voice-friendly short name for a struct node. Prefers a hand-written
    Chinese label when lang='zh' and one is available; falls back to the
    English slug-derived label otherwise."""
    if not struct_id:
        return "the target" if lang == "en" else "目标位置"
    m = STRUCT_META.get(struct_id)
    if not m:
        return struct_id.replace("_", " ")
    if lang == "zh" and m.get("short_label_zh"):
        return m["short_label_zh"]
    return m["short_label"]


def _struct_features(struct_id: Optional[str], lang: str = "en") -> list[str]:
    """Distinctive visible features for a struct node. Returns the Chinese
    versions when ``lang='zh'`` and they exist; falls back to English."""
    if not struct_id:
        return []
    m = STRUCT_META.get(struct_id)
    if not m:
        return []
    if lang == "zh" and m.get("unique_features_zh"):
        return m["unique_features_zh"]
    return m.get("unique_features", [])


# ---------------------------------------------------------------------------
# Path finding (topology-level BFS).
# ---------------------------------------------------------------------------
def find_path(current_struct: Optional[str], goal_struct: Optional[str]) -> dict:
    """Plan a navigation path from current struct node to goal struct node.

    Returns a dict::

        {
            'status':       'arrived' | 'same_cell' | 'cross_cell' | 'unknown',
            'current_topo': str | None,
            'goal_topo':    str | None,
            'path':         list[str],  # topology cells, full path inc. endpoints
            'hops':         int,        # len(path) - 1  (0 for arrived/same_cell)
        }

    'unknown' covers the case where either side has no struct→topology mapping,
    or the goal cell is unreachable from the current cell in the graph.
    """
    if not goal_struct:
        return {"status": "unknown", "current_topo": None, "goal_topo": None,
                "path": [], "hops": 0}

    current_topo = STRUCT_TO_TOPOLOGY.get(current_struct) if current_struct else None
    goal_topo = STRUCT_TO_TOPOLOGY.get(goal_struct)

    if not goal_topo:
        return {"status": "unknown", "current_topo": current_topo,
                "goal_topo": None, "path": [], "hops": 0}

    if current_struct and current_struct == goal_struct:
        return {"status": "arrived", "current_topo": current_topo,
                "goal_topo": goal_topo, "path": [current_topo], "hops": 0}

    if not current_topo:
        # We have a goal but the system can't place the user. Caller decides
        # whether to ask the user to retake.
        return {"status": "unknown", "current_topo": None,
                "goal_topo": goal_topo, "path": [], "hops": 0}

    if current_topo == goal_topo:
        return {"status": "same_cell", "current_topo": current_topo,
                "goal_topo": goal_topo, "path": [current_topo], "hops": 0}

    # BFS on topology graph
    parent: dict[str, Optional[str]] = {current_topo: None}
    frontier = deque([current_topo])
    while frontier:
        node = frontier.popleft()
        if node == goal_topo:
            break
        for nb in TOPO_ADJ.get(node, set()):
            if nb not in parent:
                parent[nb] = node
                frontier.append(nb)

    if goal_topo not in parent:
        return {"status": "unknown", "current_topo": current_topo,
                "goal_topo": goal_topo, "path": [], "hops": 0}

    # Reconstruct
    path = [goal_topo]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()

    return {"status": "cross_cell", "current_topo": current_topo,
            "goal_topo": goal_topo, "path": path, "hops": len(path) - 1}


# ---------------------------------------------------------------------------
# Instruction synthesis.
# ---------------------------------------------------------------------------
def generate_instruction(current_struct: Optional[str],
                         goal_struct: Optional[str],
                         lang: str = "en") -> str:
    """Voice-friendly one-shot navigation instruction.

    The output is intentionally short (≤ ~2 sentences) so it's suitable for
    TTS playback. For low-confidence or unknown cases the caller should
    suppress this and ask the user to retake instead.
    """
    plan = find_path(current_struct, goal_struct)
    status = plan["status"]
    is_zh = (lang == "zh")
    goal_label = _struct_short(goal_struct, lang)

    if status == "arrived":
        if is_zh:
            return f"您已到达目的地：{goal_label}。"
        return f"You have arrived at {goal_label}."

    if status == "unknown":
        # Distinguish the two flavours: goal-not-in-map vs current-not-placed
        if not plan["goal_topo"]:
            if is_zh:
                return "抱歉，我不认识这个目的地。请换一个目标。"
            return "Sorry, I don't recognise that destination. Please pick another goal."
        if not plan["current_topo"]:
            if is_zh:
                return "我还无法判断您的位置，请换个角度再拍一张。"
            return "I can't place your location yet — please retake the photo from a different angle."
        # Reachable-but-not in graph (shouldn't happen if data is consistent)
        if is_zh:
            return f"暂时找不到去{goal_label}的路线，请重新拍照。"
        return f"I can't find a route to {goal_label} right now — please retake the photo."

    if status == "same_cell":
        # Local intra-cell disambiguation. We don't have spatial relations
        # between struct nodes in the same cell, so the safest move is to
        # describe the *goal's* distinctive features and ask the user to look.
        features = _struct_features(goal_struct, lang)
        if features:
            # Pick up to two short features; voice playback friendly.
            feat_str = features[0]
            if len(features) > 1 and len(features[1]) < 60:
                if is_zh:
                    feat_str = f"{features[0]}；{features[1]}"
                else:
                    feat_str = f"{features[0]}, and {features[1]}"
            if is_zh:
                return (f"您已经非常接近{goal_label}了。请寻找：{feat_str}。"
                        f"如果看不到，请慢慢转动方向再拍一张。")
            return (f"You are very close to {goal_label}. Look for: {feat_str}. "
                    f"If you can't see it, turn slowly and retake a photo.")
        # No features available
        if is_zh:
            return f"您已经在{goal_label}附近。请慢慢看一圈寻找它。"
        return f"You are near {goal_label}. Please look around to spot it."

    # cross_cell
    path = plan["path"]
    next_topo = path[1] if len(path) > 1 else plan["goal_topo"]
    goal_topo = plan["goal_topo"]
    hops = plan["hops"]
    next_friendly = _topo_friendly(next_topo, lang)
    goal_topo_friendly = _topo_friendly(goal_topo, lang)

    # Suppress the redundant "look for X there" tail when the goal's short
    # label is essentially the same as the destination cell's friendly name
    # (e.g. cell `poi_3d_printer_table` → "the 3D printer area" and struct
    # `poi05_desk_3d_printer` → "desk 3d printer" — close enough that saying
    # both is awkward).
    def _label_is_redundant(label: str, cell_friendly: str) -> bool:
        a = label.lower().strip()
        b = cell_friendly.lower().strip()
        return a and (a in b or b.endswith(a))

    if hops == 1:
        if _label_is_redundant(goal_label, next_friendly):
            if is_zh:
                return f"请朝{next_friendly}方向走过去。"
            return f"Head toward {next_friendly}."
        if is_zh:
            return (f"请朝{next_friendly}方向走过去，到了以后寻找{goal_label}。")
        return (f"Head toward {next_friendly}, then look for {goal_label} there.")

    # Multi-hop: tell the user the immediate next cell + the destination cell.
    # When the route is unusually long (hops >= 3, well beyond the current
    # scene-graph diameter of 2), append a gentle suspicion prompt — either the
    # graph is wrong or the user is on the far side of the building from a
    # surprising start. Future-proofs for bigger floor plans.
    far_suffix_en = (" The goal is several rooms away — if that surprises you, "
                     "please retake a photo to confirm your current location.")
    far_suffix_zh = "（目标离您较远，如果这看起来不对，请重新拍照确认当前位置。）"

    if is_zh:
        base = (f"请先朝{next_friendly}方向走，然后继续前往{goal_topo_friendly}，"
                f"在那里寻找{goal_label}。")
        return base + far_suffix_zh if hops >= 3 else base
    base = (f"First head toward {next_friendly}, then continue on to "
            f"{goal_topo_friendly}, where you'll find {goal_label}.")
    return base + far_suffix_en if hops >= 3 else base


# ---------------------------------------------------------------------------
# Natural-language goal matching — reuse SigLIP's text encoder + pre-computed
# 18-node text embeddings to map a free-form goal_text to one of the known
# struct nodes.
# ---------------------------------------------------------------------------
def match_goal_text(goal_text: str, retriever, site_id: Optional[str] = None,
                    min_score: float = 0.25) -> Optional[dict]:
    """Match ``goal_text`` to one of the known struct nodes via SigLIP text
    similarity.

    Parameters
    ----------
    goal_text : str
        Free-form description of the goal, e.g. "the small open 3D printer".
    retriever : siglip_retriever.SigLipRetriever
        A loaded retriever instance — we reuse its model/processor and the
        pre-computed ``text_embeds`` for the 18 nodes.
    site_id : Optional[str]
        If set, restrict candidates to that scene.
    min_score : float
        If best cosine is below this, return None (caller should ask for
        clarification rather than route to a low-confidence match).

    Returns
    -------
    Optional[dict]
        ``{'node_id': str, 'score': float, 'short_label': str}`` or None.
    """
    if not goal_text or retriever is None:
        return None

    import torch

    with torch.no_grad():
        tin = retriever.proc(text=[goal_text], return_tensors="pt",
                             padding="max_length", truncation=True)
        q = retriever.model.get_text_features(**tin)
        q = q / q.norm(dim=-1, keepdim=True)
        sims = (q @ retriever.text_embeds.T).squeeze(0)
    cosines = sims.tolist()

    eligible = [(i, c) for i, c in enumerate(cosines)
                if not site_id or retriever.node_scenes[i] == site_id]
    if not eligible:
        return None
    eligible.sort(key=lambda x: -x[1])
    best_i, best_c = eligible[0]
    if best_c < min_score:
        return None
    nid = retriever.node_ids[best_i]
    return {
        "node_id":     nid,
        "score":       float(best_c),
        "short_label": _struct_short(nid, "en"),
    }
