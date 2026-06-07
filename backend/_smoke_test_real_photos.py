"""Smoke test driven by photo captions."""
import os, sys
os.environ.setdefault("LOWCONF_SCORE_TH", "0.50")
os.environ.setdefault("LOWCONF_MARGIN_TH", "0.10")
os.environ.setdefault("FUSION_TEMPERATURE", "0.25")
print("Importing app.py ...")
import app
retriever = app.get_unified_retriever()

CASES = [
    ("Photo 1 (Sense_B Studio)", "POI11/POI18/POI20", "SCENE_B_STUDIO",
     "Open studio space with a large black display screen on the right wall, "
     "purple orange and green office chairs scattered around, a glass-walled "
     "GDI Hub office on the left, blue and green sofas near tall windows in "
     "the back, a yellow line on the grey floor, and exposed industrial ceiling."),
    ("Photo 2 (Sense_A Maker Space)", "POI04/POI03", "SCENE_A_MS",
     "Indoor maker space with two large black Ultimaker 3D printers stacked "
     "on a wooden workbench against the left wall, a tall black drawer cabinet "
     "with many small drawers on the right wall, filament spools and tools on "
     "the bench, a yellow guide line on the floor, and a small open frame "
     "3D printer on a low table in the foreground."),
]

for label, hint, scene, cap in CASES:
    print("\n" + "=" * 78)
    print(f"### {label}")
    print(f"expected: {hint}    scene: {scene}")
    print(f"caption:  {cap}")
    print("-" * 78)
    cands = retriever.retrieve(cap, top_k=5, scene_filter=scene, session_id=None)
    if not cands:
        print("  ⚠️ no candidates"); continue
    print(f"\n  Top-5:")
    for i, c in enumerate(cands[:5]):
        print(f"    {i+1}. {c['id']:40s}  fused={c['score']:.4f}  "
              f"struct={c.get('structure_score', 0):.3f}  detail={c.get('detail_score', 0):.3f}")
    conf, margin, raw1, raw2 = app.calculate_calibrated_confidence_and_margin(
        cands, top_k=5, session_id=None, site_id=scene)
    decision = "NAVIGATE" if not (conf < app.LOWCONF_SCORE_TH or margin < app.LOWCONF_MARGIN_TH) else "CLARIFY/REFUSE"
    print(f"\n  → confidence={conf:.4f}  margin={margin:.4f}  → {decision}  (th={app.LOWCONF_SCORE_TH}/{app.LOWCONF_MARGIN_TH})")
