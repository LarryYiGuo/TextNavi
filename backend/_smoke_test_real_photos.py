"""
Photo-driven smoke test.

Two usage modes:
  1. Manual captions (no photo files needed) — uses captions Claude wrote by
     looking at the images. Tests retrieval + confidence logic end-to-end.
  2. Real BLIP captions — pass image paths via env IMG1/IMG2; the script
     will run hf_caption() and use whatever the real model produces.
"""

import os
import sys

os.environ.setdefault("LOWCONF_SCORE_TH", "0.50")
os.environ.setdefault("LOWCONF_MARGIN_TH", "0.10")
os.environ.setdefault("FUSION_TEMPERATURE", "0.25")

print("Importing app.py ...")
import app  # noqa: E402

retriever = app.get_unified_retriever()


# --- Manual captions (Claude-eyeballed) ---
MANUAL_CASES = [
    # (label, expected POI hint, scene, caption)
    ("Photo 1 (Sense_B Studio, near entrance)",
     "POI11 GDI glass box / POI18 large display / POI20 sofa zone",
     "SCENE_B_STUDIO",
     "Open studio space with a large black display screen on the right wall, "
     "purple orange and green office chairs scattered around, a glass-walled "
     "GDI Hub office on the left, blue and green sofas near tall windows in "
     "the back, a yellow line on the grey floor, and exposed industrial ceiling."),

    ("Photo 2 (Sense_A Maker Space, near 3D printer wall)",
     "POI04 wall 3D printers / POI03 black drawer cabinet",
     "SCENE_A_MS",
     "Indoor maker space with two large black Ultimaker 3D printers stacked "
     "on a wooden workbench against the left wall, a tall black drawer cabinet "
     "with many small drawers on the right wall, filament spools and tools on "
     "the bench, a yellow guide line on the floor, and a small open frame "
     "3D printer on a low table in the foreground."),
]


def run_case(label, hint, scene, caption, session_id=None):
    print("\n" + "=" * 78)
    print(f"### {label}")
    print(f"expected: {hint}")
    print(f"scene:    {scene}")
    print(f"caption:  {caption}")
    print("-" * 78)

    cands = retriever.retrieve(caption, top_k=5, scene_filter=scene, session_id=session_id)
    if not cands:
        print("  ⚠️ no candidates")
        return

    print(f"\n  Top-5 candidates:")
    for i, c in enumerate(cands[:5]):
        print(f"    {i+1}. {c['id']:40s}  fused={c['score']:.4f}  "
              f"struct={c.get('structure_score', 0):.3f}  detail={c.get('detail_score', 0):.3f}")

    conf, margin, raw_top1, raw_top2 = app.calculate_calibrated_confidence_and_margin(
        cands, top_k=5, session_id=session_id, site_id=scene
    )
    decision = "NAVIGATE" if not (conf < app.LOWCONF_SCORE_TH or margin < app.LOWCONF_MARGIN_TH) \
        else "CLARIFY/REFUSE"
    print(f"\n  → confidence = {conf:.4f}")
    print(f"  → margin     = {margin:.4f}")
    print(f"  → decision   = {decision}  (th={app.LOWCONF_SCORE_TH}/{app.LOWCONF_MARGIN_TH})")


# --- Run ---
print("\n" + "#" * 78)
print("# PASS 1: cold (no session)")
print("#" * 78)
for label, hint, scene, cap in MANUAL_CASES:
    run_case(label, hint, scene, cap)


# --- If user provided IMG1/IMG2 env vars, run real BLIP too ---
img_paths = [os.environ.get("IMG1"), os.environ.get("IMG2")]
if any(img_paths):
    print("\n" + "#" * 78)
    print("# PASS 2: real BLIP captions")
    print("#" * 78)
    for i, img_path in enumerate(img_paths, 1):
        if not img_path or not os.path.exists(img_path):
            continue
        print(f"\n📸 Loading {img_path} ...")
        with open(img_path, 'rb') as f:
            img_bytes = f.read()
        try:
            blip_caption = app.hf_caption(img_bytes)
            print(f"   BLIP caption: {blip_caption}")
            # Use the corresponding scene from MANUAL_CASES if available
            scene = MANUAL_CASES[i - 1][2] if i - 1 < len(MANUAL_CASES) else "SCENE_A_MS"
            run_case(f"Photo {i} (real BLIP)", "—", scene, blip_caption)
        except Exception as e:
            print(f"   ⚠️ BLIP failed: {e}")
else:
    print("\n(set IMG1=/path IMG2=/path to also run real BLIP)")

print("\nDone.")
