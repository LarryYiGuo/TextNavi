"""
Smoke test for Stage 1 (P0) + P1 fixes.

Directly drives EnhancedDualChannelRetriever + calculate_calibrated_confidence_and_margin
on synthetic captions. NOT a unit test — just a sanity check that:
  1. Code path doesn't crash
  2. confidence / margin land in plausible ranges
  3. consistency / topology prior actually fire when data is present
"""

import os
import sys

# Make sure we use the post-fix defaults
os.environ.setdefault("LOWCONF_SCORE_TH", "0.50")
os.environ.setdefault("LOWCONF_MARGIN_TH", "0.10")
os.environ.setdefault("FUSION_TEMPERATURE", "0.25")

print("=" * 70)
print("Importing app.py (this may take a few seconds)...")
print("=" * 70)
import app  # noqa: E402

print("\n" + "=" * 70)
print("Initializing retriever...")
print("=" * 70)
retriever = app.get_unified_retriever()
print(f"  retriever class: {type(retriever).__name__}")
print(f"  α₀={retriever.alpha}, β₀={retriever.beta}, γ={retriever.gamma}")
print(f"  τ_struct={retriever.structure_tau}, τ_detail={retriever.detail_tau}")


# --- Synthetic test cases for SCENE_A_MS ---
# (Captions roughly approximating what BLIP would generate from photos near specific POIs.)
TEST_CAPTIONS = [
    ("POI01 entrance vicinity",
     "A glass entrance door with a yellow floor line on the ground leading inside."),
    ("POI04 wall 3D printers",
     "Several large 3D printers stacked against the right-side wall with filament spools."),
    ("POI09 QR bookshelf",
     "A bookshelf with a QR code, books on shelves, and a coat rack nearby."),
    ("POI07 cardboard boxes",
     "Several cardboard boxes stacked on the floor against the wall, next to an orange sofa."),
    ("Ambiguous (boxes + printer hint)",
     "A printer next to some boxes on a workbench in a maker space."),
]


def run_one(label, caption, session_id=None, site_id="SCENE_A_MS"):
    print("\n" + "-" * 70)
    print(f"### {label}")
    print(f"caption: {caption!r}")
    print(f"session_id: {session_id}, site_id: {site_id}")
    print("-" * 70)

    cands = retriever.retrieve(caption, top_k=5, scene_filter=site_id, session_id=session_id)
    if not cands:
        print("  ⚠️ no candidates returned")
        return None

    print(f"\n  Top-5 candidates (post-fusion-softmax):")
    for i, c in enumerate(cands[:5]):
        print(f"    {i+1}. {c['id']:40s}  score={c['score']:.4f}  "
              f"struct={c.get('structure_score', 0):.3f}  detail={c.get('detail_score', 0):.3f}")

    conf, margin, raw_top1, raw_top2 = app.calculate_calibrated_confidence_and_margin(
        cands, top_k=5, session_id=session_id, site_id=site_id
    )
    print(f"\n  → confidence = {conf:.4f}")
    print(f"  → margin     = {margin:.4f}")
    print(f"  → raw top1   = {raw_top1:.4f}")
    print(f"  → raw top2   = {raw_top2:.4f}")
    print(f"  → low_conf?  = {conf < app.LOWCONF_SCORE_TH or margin < app.LOWCONF_MARGIN_TH} "
          f"(th={app.LOWCONF_SCORE_TH}/{app.LOWCONF_MARGIN_TH})")
    return cands[0]['id'], conf, margin


# --- Run without session (no previous_location, no same_as_last boost) ---
print("\n" + "=" * 70)
print("PASS 1: cold (no session, no previous location)")
print("=" * 70)
results_cold = []
for label, cap in TEST_CAPTIONS:
    results_cold.append((label, run_one(label, cap)))


# --- Set up a session with a known previous location, run again ---
SESSION_ID = "smoke_session"
app.SESSIONS[SESSION_ID] = {
    "current_location": "poi01_entrance_glass_door",  # pretend user was at entrance
    "location_history": [{"location": "poi01_entrance_glass_door", "confidence": 0.8}],
    "orientation_history": [],
    "confidence_history": [0.8],
    "last_update_time": "smoke",
}

print("\n" + "=" * 70)
print("PASS 2: with session (prev_location = poi01_entrance_glass_door)")
print("  → expect topology prior boost on entrance-neighbors;")
print("  → expect consistency boost if top1 == poi01...")
print("=" * 70)
results_warm = []
for label, cap in TEST_CAPTIONS:
    results_warm.append((label, run_one(label, cap, session_id=SESSION_ID)))


# --- Summary table ---
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"{'Caption':38s}  {'cold conf/margin':22s}  {'warm conf/margin':22s}")
print("-" * 88)
for (label, cold), (_, warm) in zip(results_cold, results_warm):
    cold_str = f"{cold[1]:.3f} / {cold[2]:.3f}" if cold else "n/a"
    warm_str = f"{warm[1]:.3f} / {warm[2]:.3f}" if warm else "n/a"
    print(f"{label[:38]:38s}  {cold_str:22s}  {warm_str:22s}")

print("\nDone.")
