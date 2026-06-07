#!/usr/bin/env python3
"""
sweep_fusion.py — offline hyperparameter sweep for the dual-channel retriever.

Runs `/api/locate` over the 37 SENSE_A_Photo / SENSE_B_Photo images (whose
ground-truth node ids come from `photo_refs` in `data/Sense_A_MS.jsonl` and
`data/Sense_B_Studio.jsonl`), then computes top-1 accuracy + margin/confidence
distribution under each candidate set of FUSION_* env vars.

Usage:
  python tools/sweep_fusion.py baseline           # run with current defaults
  python tools/sweep_fusion.py grid               # small grid search over top 3 dims
  python tools/sweep_fusion.py apply <combo_json> # load + run a specific combo

Each "trial" spawns its own uvicorn on a free port (default 8765), waits for
/health to respond, runs all photos, then SIGTERMs uvicorn. ~70 s per trial on
this machine (~10 s warmup + ~1.5 s per photo).
"""
import json
import os
import signal
import socket
import statistics
import subprocess
import sys
import time
from collections import Counter
from contextlib import closing
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]               # backend/
PROJECT = ROOT.parent                                    # TextNavi/
PHOTO_ROOT = PROJECT.parent.parent / "VLN4VI_mages"      # VLN4VI/VLN4VI_mages
SENSE_A_DIR = PHOTO_ROOT / "SENSE_A_Photo"
SENSE_B_DIR = PHOTO_ROOT / "SENSE_B_Photo"

# struct↔detail alias (from app.py L428). Inverted so detail_node → struct_node.
ALIAS_STRUCT_FROM_DETAIL = {
    "dp_ms_entrance":       "poi01_entrance_glass_door",
    "yline_start":          "poi02_green_trash_bin",
    "yline_bend_mid":       "poi03_black_drawer_cabinet",
    "atrium_edge":          "poi04_wall_3d_printers",
    "tv_zone":              "poi05_desk_3d_printer",
    "storage_corner":       "poi06_small_open_3d_printer",
    "orange_sofa_corner":   "poi07_cardboard_boxes",
    "desks_cluster":        "poi08_to_atrium",
    "chair_on_yline":       "poi09_qr_bookshelf",
    "small_table_mid":      "poi10_metal_display_cabinet",
}


def load_dataset():
    """Return list of {file, scene, gt_struct, gt_detail} from photo_refs."""
    items = []
    # SenseA — photo_refs are in detail-id form, translate via alias
    for line in (ROOT / "data" / "Sense_A_MS.jsonl").open():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        nh = rec.get("node_hint")
        for f in rec.get("photo_refs") or []:
            p = SENSE_A_DIR / f
            if not p.exists():
                continue
            gt_struct = ALIAS_STRUCT_FROM_DETAIL.get(nh)
            if not gt_struct:
                continue
            items.append({
                "file": str(p),
                "scene": "SCENE_A_MS",
                "gt_struct": gt_struct,
                "gt_detail": nh,
            })
    # SenseB — photo_refs are already in struct-id form (poi11_di_hub_glass_box ...)
    for line in (ROOT / "data" / "Sense_B_Studio.jsonl").open():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        nh = rec.get("node_hint")
        for f in rec.get("photo_refs") or []:
            p = SENSE_B_DIR / f
            if not p.exists():
                continue
            items.append({
                "file": str(p),
                "scene": "SCENE_B_STUDIO",
                "gt_struct": nh,                   # already struct-form
                "gt_detail": nh,
            })
    return items


def free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_uvicorn(env_overrides, port, log_path):
    env = os.environ.copy()
    env.update({k: str(v) for k, v in env_overrides.items()})
    log_path.parent.mkdir(parents=True, exist_ok=True)
    f = log_path.open("w")
    proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT), env=env, stdout=f, stderr=subprocess.STDOUT,
    )
    return proc, f


def wait_ready(port, timeout=60):
    url = f"http://127.0.0.1:{port}/health"
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def stop(proc, fh):
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    fh.close()


def run_dataset(port, items, session_prefix="sweep"):
    base = f"http://127.0.0.1:{port}"
    sid = f"{session_prefix}_{int(time.time())}"
    # we start one session per scene because /api/start binds (session_id, site_id)
    by_scene = {}
    for it in items:
        by_scene.setdefault(it["scene"], []).append(it)
    rows = []
    for scene, scene_items in by_scene.items():
        scene_sid = f"{sid}_{scene[-3:]}"
        requests.post(f"{base}/api/start",
                      json={"session_id": scene_sid, "site_id": scene,
                            "opening_provider": "ft", "lang": "en"},
                      timeout=10)
        for it in scene_items:
            with open(it["file"], "rb") as img:
                r = requests.post(
                    f"{base}/api/locate",
                    files={"image": (Path(it["file"]).name, img, "image/jpeg")},
                    data={"site_id": scene, "session_id": scene_sid, "provider": "ft"},
                    timeout=90,
                )
            j = r.json()
            rows.append({
                **it,
                "pred": j.get("node_id"),
                "conf": j.get("confidence"),
                "margin": j.get("margin"),
                "low_conf": j.get("low_conf"),
                "is_first": j.get("is_first_photo", False),
            })
    return rows


def metrics(rows):
    # The first photo per session is warmup (no real prediction) — exclude
    trials = [r for r in rows if not r["is_first"] and r["conf"] is not None]
    if not trials:
        return {"n": 0}
    hits = sum(1 for r in trials if r["pred"] == r["gt_struct"])
    confs = [r["conf"] for r in trials]
    margins = [r["margin"] for r in trials if r["margin"] is not None]
    lows = sum(1 for r in trials if r["low_conf"])
    return {
        "n":              len(trials),
        "top1_acc":       hits / len(trials),
        "hits":           hits,
        "mean_conf":      statistics.mean(confs),
        "mean_margin":    statistics.mean(margins) if margins else 0,
        "median_margin":  statistics.median(margins) if margins else 0,
        "low_conf_rate":  lows / len(trials),
    }


def trial(env_overrides, items, label="trial"):
    port = free_port()
    log_path = PROJECT / "backend" / "logs" / "sweep" / f"{label}_{int(time.time())}.log"
    proc, fh = start_uvicorn(env_overrides, port, log_path)
    try:
        if not wait_ready(port, timeout=120):
            return {"label": label, "env": env_overrides, "error": "backend never ready",
                    "log": str(log_path)}
        rows = run_dataset(port, items, session_prefix=label)
        m = metrics(rows)
        return {"label": label, "env": env_overrides, **m,
                "log": str(log_path),
                "pred_dist": dict(Counter(r["pred"] for r in rows if not r["is_first"]))}
    finally:
        stop(proc, fh)


def baseline(items):
    print(f"\n=== BASELINE (n_photos={len(items)}) ===")
    res = trial({}, items, label="baseline")
    print(json.dumps({k: v for k, v in res.items() if k not in ("pred_dist",)},
                     indent=2, default=str))
    print("pred_dist:", res.get("pred_dist"))
    return res


def grid(items):
    """Tight 3×3×3 grid over (α/β fallback, FUSION_TEMPERATURE, neg_penalty)."""
    base = float(os.getenv("FUSION_TEMPERATURE", "0.25"))
    combos = []
    for a_fb in (0.50, 0.65, 0.80):
        b_fb = round(1.0 - a_fb, 2)
        for t_fusion in (0.15, 0.25, 0.40):
            for neg_pen in (0.05, 0.15, 0.30):
                combos.append({
                    "FUSION_ALPHA_FB":     a_fb,
                    "FUSION_BETA_FB":      b_fb,
                    "FUSION_TEMPERATURE":  t_fusion,
                    "FUSION_NEG_PENALTY":  neg_pen,
                })
    print(f"\n=== GRID SWEEP ({len(combos)} combos × n_photos={len(items)}) ===")
    base_res = baseline(items)
    results = [base_res]
    for i, env in enumerate(combos, 1):
        label = f"g{i:02d}_a{env['FUSION_ALPHA_FB']}_t{env['FUSION_TEMPERATURE']}_n{env['FUSION_NEG_PENALTY']}"
        print(f"\n[{i}/{len(combos)}] {label}")
        r = trial(env, items, label=label)
        line = {k: r.get(k) for k in ("top1_acc", "mean_conf", "mean_margin", "low_conf_rate")}
        print(f"  → {line}")
        results.append(r)
    # rank by top1_acc, tiebreak mean_margin
    valid = [r for r in results if "top1_acc" in r]
    valid.sort(key=lambda r: (-r["top1_acc"], -r.get("mean_margin", 0)))
    print("\n=== TOP 5 by top1_acc ===")
    for r in valid[:5]:
        env = r["env"] or {"(baseline)": ""}
        print(f"  top1={r['top1_acc']:.3f}  margin={r.get('mean_margin', 0):.3f}  "
              f"conf={r.get('mean_conf', 0):.3f}  low_conf={r.get('low_conf_rate', 0):.3f}  env={env}")
    out_path = PROJECT / "backend" / "logs" / "sweep" / f"results_{int(time.time())}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nFull results → {out_path}")
    return valid


def main():
    items = load_dataset()
    print(f"loaded {len(items)} labeled photos "
          f"({sum(1 for i in items if i['scene'] == 'SCENE_A_MS')} SenseA + "
          f"{sum(1 for i in items if i['scene'] == 'SCENE_B_STUDIO')} SenseB)")
    if len(sys.argv) < 2 or sys.argv[1] == "baseline":
        baseline(items)
    elif sys.argv[1] == "grid":
        grid(items)
    elif sys.argv[1] == "apply" and len(sys.argv) >= 3:
        env = json.loads(sys.argv[2])
        r = trial(env, items, label="apply")
        print(json.dumps(r, indent=2, default=str))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
