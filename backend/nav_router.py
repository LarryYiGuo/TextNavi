"""nav_router.py — goal-aware navigation: graph routing + instruction generation.

Routes on the STRUCT-level graph embedded in the paper's structure files
(``Sense_*_Finetuned.fixed.jsonl``): 10 nodes per scene with metric
coordinates (local 10×7 m plans) and 10 directed edges per scene with
voice-ready action hints ("veer left to shelf"). A hand-added bridge edge
connects the two scenes through the atrium, so cross-scene goals are routable.

The coarse topology-cell graph (``topology.json`` + ``STRUCT_TO_TOPOLOGY``)
remains the EVAL layer — it defines the paper's "useful top-1" metric and is
deliberately NOT used for routing anymore. The two layers are decoupled:
upgrading navigation cannot silently change the published metric.

Public API
----------
- ``find_path(current_struct, goal_struct)`` -> dict
    status: 'arrived' | 'route' | 'unknown'; for 'route' also path (struct
    nodes), legs ([{to, hint, forward, steps}]), hops, cross_scene.
- ``generate_instruction(current_struct, goal_struct, lang='en')`` -> str
- ``match_goal_text(goal_text, retriever, site_id=None)`` -> Optional[dict]
- ``KNOWN_NODES`` -> set[str] — struct nodes that can be localisation outputs
    and goals (the 18 textmap nodes; poi13/poi17 exist only in the struct
    graph and can appear as transit waypoints, not goals).
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Optional

from topology_eval import STRUCT_TO_TOPOLOGY

ROOT = Path(__file__).resolve().parent  # backend/
TEXTMAP_PATH = ROOT / "data" / "textmap_clean.jsonl"


# ---------------------------------------------------------------------------
# Struct-level navigation graph — loaded from the paper's structure files.
# Each scene: 10 nodes with metric coordinates (local 10×7 m plan) + 10
# directed edges with voice-ready action hints. The hints are valid only in
# the recorded direction; reverse traversal falls back to a generic
# "head toward X" template (left/right would be mirrored).
# ---------------------------------------------------------------------------
STRUCT_FILES = {
    "SCENE_A_MS":     ROOT / "data" / "Sense_A_Finetuned.fixed.jsonl",
    "SCENE_B_STUDIO": ROOT / "data" / "Sense_B_Finetuned.fixed.jsonl",
}
# The immutable paper data still uses the old poi09 id; rename on load.
_ID_RENAMES = {"poi09_qr_bookshelf": "poi09_chair_on_yline"}

# Cross-scene bridge: the structure data names poi08 "To Atrium (SenseB
# connection)" and the Studio entrance (poi11) sits across the atrium.
# One physical link, two directed hints — makes cross-scene goals routable.
_BRIDGE = [
    ("poi08_to_atrium", "poi11_di_hub_glass_box",
     "cross the atrium to the Studio entrance"),
    ("poi11_di_hub_glass_box", "poi08_to_atrium",
     "cross the atrium back to the Maker Space"),
]

# Hand-translated zh versions of every action hint (keys = exact en strings).
HINT_ZH = {
    # SCENE_A
    "veer left to shelf":                    "斜向左走到书架",
    "continue left a few steps":             "继续向左走几步",
    "open threshold to Atrium":              "穿过开口进入中庭",
    "move right along the bottom wall":      "沿底侧墙向右走",
    "continue forward along right wall":     "沿右侧墙继续直行",
    "continue forward to printer bay":       "继续直行到打印机区",
    "left of printer bay, desk printer":     "在打印机区左侧找桌面打印机",
    "turn slightly left across aisle":       "稍向左转穿过走道",
    "continue left toward top-left":         "继续向左前方走",
    "follow yellow line via brown pad chair": "沿黄色引导线走，途经软垫椅",
    # SCENE_B
    "left along bottom edge":                "沿底边向左走",
    "left to inset wall":                    "向左走到内嵌墙",
    "forward to main table":                 "直行到主工作桌",
    "left toward window edge":               "向左朝窗边走",
    "right a few steps to green sofa":       "向右走几步到绿沙发",
    "left to corner storage":                "向左到角落储物区",
    "right toward filming table":            "向右朝拍摄桌走",
    "slight right to large TV":              "稍向右到大屏幕",
    "forward to sofa zone":                  "直行到沙发区",
    "diagonal right across the corner":      "沿对角线向右穿过角落",
    # Bridge
    "cross the atrium to the Studio entrance":  "穿过中庭，前往工作室入口",
    "cross the atrium back to the Maker Space": "穿过中庭，回到创客空间",
}


def _load_struct_graph():
    """Build {node: [(neighbour, hint, hint_is_forward)]} + coords + scene."""
    adj: dict[str, list] = {}
    coords: dict[str, tuple] = {}
    node_scene: dict[str, str] = {}

    def _rn(nid):
        return _ID_RENAMES.get(nid, nid)

    for scene, path in STRUCT_FILES.items():
        try:
            topo = json.load(open(path))["input"]["topology"]
        except Exception as e:
            print(f"⚠️ nav_router: failed to load struct graph from {path.name}: {e}")
            continue
        for n in topo.get("nodes", []):
            nid = _rn(n["id"])
            c = n.get("geometry", {}).get("center")
            if c and len(c) == 2:
                coords[nid] = (float(c[0]), float(c[1]))
            node_scene[nid] = scene
            adj.setdefault(nid, [])
        for e in topo.get("edges", []):
            a, b = _rn(e["from"]), _rn(e["to"])
            hint = e.get("action_hint", "")
            adj.setdefault(a, []).append((b, hint, True))   # recorded direction
            adj.setdefault(b, []).append((a, hint, False))  # reverse: hint invalid
    for a, b, hint in _BRIDGE:
        if a in adj and b in adj:
            adj[a].append((b, hint, True))
    return adj, coords, node_scene


STRUCT_ADJ, STRUCT_COORDS, STRUCT_NODE_SCENE = _load_struct_graph()

_STEP_METERS = 0.6  # cautious indoor step length for BVI users


def _steps_between(a: str, b: str) -> Optional[int]:
    """Approximate step count between two nodes in the SAME scene. The two
    scenes use separate local coordinate frames, so cross-scene distances
    are meaningless (returns None — instruction omits the step count)."""
    if STRUCT_NODE_SCENE.get(a) != STRUCT_NODE_SCENE.get(b):
        return None
    ca, cb = STRUCT_COORDS.get(a), STRUCT_COORDS.get(b)
    if not ca or not cb:
        return None
    dist = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
    return max(1, round(dist / _STEP_METERS))


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
# Path finding — BFS on the struct-level graph (bridge edge makes the whole
# building one connected component, so cross-scene goals route normally).
# ---------------------------------------------------------------------------
def find_path(current_struct: Optional[str], goal_struct: Optional[str]) -> dict:
    """Plan a navigation path from current struct node to goal struct node.

    Returns::

        {
            'status':       'arrived' | 'route' | 'unknown',
            'path':         list[str],   # struct nodes incl. both endpoints
            'legs':         list[dict],  # per edge: {to, hint, forward, steps}
            'hops':         int,         # len(path) - 1
            'cross_scene':  bool,        # route crosses the atrium bridge
            'current_topo': str | None,  # coarse cells, telemetry only
            'goal_topo':    str | None,
        }

    'unknown' = either endpoint missing from the struct graph (e.g. the
    caller couldn't place the user). The graph is connected, so a known pair
    always routes.
    """
    current_topo = STRUCT_TO_TOPOLOGY.get(current_struct) if current_struct else None
    goal_topo = STRUCT_TO_TOPOLOGY.get(goal_struct) if goal_struct else None
    base = {"current_topo": current_topo, "goal_topo": goal_topo,
            "path": [], "legs": [], "hops": 0, "cross_scene": False}

    if not goal_struct or goal_struct not in STRUCT_ADJ:
        return {"status": "unknown", **base, "goal_known": False}
    if not current_struct or current_struct not in STRUCT_ADJ:
        return {"status": "unknown", **base, "goal_known": True}
    if current_struct == goal_struct:
        return {"status": "arrived", **base, "path": [current_struct],
                "goal_known": True}

    parent: dict[str, Optional[str]] = {current_struct: None}
    parent_edge: dict[str, tuple] = {}
    frontier = deque([current_struct])
    while frontier:
        node = frontier.popleft()
        if node == goal_struct:
            break
        for nbr, hint, fwd in STRUCT_ADJ.get(node, []):
            if nbr not in parent:
                parent[nbr] = node
                parent_edge[nbr] = (hint, fwd)
                frontier.append(nbr)

    if goal_struct not in parent:
        # Shouldn't happen (graph is connected) — defensive.
        return {"status": "unknown", **base, "goal_known": True}

    path = [goal_struct]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()

    legs = []
    for i in range(1, len(path)):
        hint, fwd = parent_edge[path[i]]
        legs.append({"to": path[i], "hint": hint, "forward": fwd,
                     "steps": _steps_between(path[i - 1], path[i])})

    cross = any(STRUCT_NODE_SCENE.get(path[i]) != STRUCT_NODE_SCENE.get(path[i + 1])
                for i in range(len(path) - 1))

    return {"status": "route", **base, "path": path, "legs": legs,
            "hops": len(path) - 1, "cross_scene": cross, "goal_known": True}


# ---------------------------------------------------------------------------
# Instruction synthesis.
# ---------------------------------------------------------------------------
def generate_instruction(current_struct: Optional[str],
                         goal_struct: Optional[str],
                         lang: str = "en") -> str:
    """Voice-friendly one-shot navigation instruction (≤ ~2 sentences for TTS).

    Built from the struct-level route: the first leg uses the recorded action
    hint when traversing the edge in its recorded direction ("veer left to
    shelf"); reverse traversals fall back to "head toward X" (the hint's
    left/right would be mirrored). Step counts come from the metric node
    coordinates (~0.6 m per cautious indoor step).
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
        if not plan.get("goal_known"):
            if is_zh:
                return "抱歉，我不认识这个目的地。请换一个目标。"
            return "Sorry, I don't recognise that destination. Please pick another goal."
        if is_zh:
            return "我还无法判断您的位置，请换个角度再拍一张。"
        return "I can't place your location yet — please retake the photo from a different angle."

    # status == "route"
    legs = plan["legs"]
    first = legs[0]
    steps = first["steps"]

    # First-leg lead: recorded hint when walking the edge forward, otherwise
    # a generic "head toward" with the next waypoint's label.
    if first["forward"] and first["hint"]:
        lead_en = first["hint"][0].upper() + first["hint"][1:]
        lead_zh = HINT_ZH.get(first["hint"], first["hint"])
    else:
        nxt = _struct_short(first["to"], lang)
        lead_en = f"Head toward {nxt}"
        lead_zh = f"朝{nxt}方向走"

    steps_en = f", about {steps} steps" if steps else ""
    steps_zh = f"，大约 {steps} 步" if steps else ""

    if len(legs) == 1:
        feats = _struct_features(goal_struct, lang)
        feat_en = f" Look for {feats[0]}." if feats else ""
        feat_zh = f"到达后请寻找：{feats[0]}。" if feats else ""
        if not (first["forward"] and first["hint"]):
            # Fallback lead already names the goal ("Head toward X") — don't
            # repeat it with "to reach X".
            if is_zh:
                return f"{lead_zh}{steps_zh}。{feat_zh}"
            return f"{lead_en}{steps_en}.{feat_en}"
        if is_zh:
            return f"{lead_zh}{steps_zh}，即可到达{goal_label}。{feat_zh}"
        return f"{lead_en}{steps_en} to reach {goal_label}.{feat_en}"

    # Multi-leg: speak the first leg, summarise the rest. Cross-scene routes
    # get an explicit "other area" note instead of a step count (the scenes
    # use separate coordinate frames).
    remaining = plan["hops"] - 1
    wp_en = "waypoint" if remaining == 1 else "waypoints"
    if plan["cross_scene"]:
        if is_zh:
            return (f"{lead_zh}{steps_zh}，然后继续前往{goal_label}"
                    f"（目的地在另一个区域，途经 {remaining} 个参照点）。")
        return (f"{lead_en}{steps_en}, then continue toward {goal_label} "
                f"(it's in the other area, {remaining} {wp_en} to go).")
    if is_zh:
        return (f"{lead_zh}{steps_zh}，然后继续前往{goal_label}"
                f"（还需经过 {remaining} 个参照点）。")
    return (f"{lead_en}{steps_en}, then continue toward {goal_label} "
            f"({remaining} more {wp_en}).")


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


def match_landmark_text(text: str, retriever, site_id: Optional[str] = None,
                        lang: str = "en") -> Optional[dict]:
    """Match a user's *stated landmark* ("I just passed the green trash bin")
    to a known struct node. Used by the Secondary Prompt clarification loop.

    zh: character-bigram overlap against the hand-written zh labels/features
    (SigLIP's text tower is English-trained, so embedding Chinese input
    against English node texts scores near-noise). en: SigLIP text-text
    matching via ``match_goal_text`` with a stricter threshold — a stated
    landmark drives relocalisation, so a weak match must be rejected.

    Returns ``{'node_id', 'score', 'short_label'}`` or None.
    """
    if not text:
        return None

    if lang == "zh":
        def _bigrams(s):
            s = "".join(ch for ch in s if not ch.isspace())
            return {s[i:i + 2] for i in range(len(s) - 1)}
        tb = _bigrams(text)
        best_nid, best_hits = None, 0
        for nid, m in STRUCT_META.items():
            if site_id and m.get("scene") and m["scene"] != site_id:
                continue
            cand_text = (m.get("short_label_zh") or "") + "".join(m.get("unique_features_zh") or [])
            hits = len(tb & _bigrams(cand_text))
            if hits > best_hits:
                best_nid, best_hits = nid, hits
        # ≥2 shared bigrams ≈ at least one meaningful 3-char overlap;
        # 1 bigram is too easy to hit by chance ("打印" appears everywhere).
        if best_nid and best_hits >= 3:
            return {"node_id": best_nid, "score": float(best_hits),
                    "short_label": _struct_short(best_nid, "zh")}
        return None

    return match_goal_text(text, retriever, site_id=site_id, min_score=0.30)
