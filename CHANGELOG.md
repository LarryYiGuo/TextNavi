# Changelog

History of changes to TextNavi (VLN4VI). This file consolidates ~33 former
per-feature `README_*.md` / `*_SUMMARY.md` documents into a single timeline. Most of
the original docs were undated; entries are ordered by best-inferred chronology and
cross-references. Where a doc carried an explicit date or version it is shown.

Parameter values reflect what each change introduced **at the time**; for the current
live values see [`README.md`](README.md).

---

## Unreleased — Plan B (SigLIP recall) — 4.4× accuracy lift on ground truth (2026-06-07, branch `feature/siglip-rerank`)

**TL;DR: replacing BLIP-caption + textmap-fusion with a single SigLIP-so400m
image–text matching call moves top-1 accuracy from 8.6% to 37.8% (+29.2 pp) on
the labeled 37-photo benchmark — a 4.4× improvement.** Plan C (cross-encoder
rerank) is blocked locally (BLIP-ITM only ships `pytorch_model.bin`; torch 2.5.1
refuses to load it post-CVE-2025-32434; no `OPENAI_API_KEY` set for GPT-4o
vision rerank). Branch `feature/siglip-rerank`, not merged.

**Tool added:** `backend/tools/eval_siglip.py`
- Loads the same labeled photo set as `sweep_fusion.py` (37 photos, GT from
  `photo_refs` + struct↔detail alias).
- Embeds each node as text (3 modes: rich / minimal / specific), embeds each
  photo, ranks by cosine. Optional `--rerank <model_id>` adds a cross-encoder
  pass over top-K.
- No app.py changes yet — this is an offline diagnostic. Wiring it into
  `/api/locate` happens after the architecture is settled.

**Headline numbers** (top1 / top5 on n=37 labeled photos):

| Approach                                                  | top1  | top5  | ms/photo | Δ vs baseline |
|-----------------------------------------------------------|------:|------:|---------:|--------------:|
| BLIP caption + dual-channel fusion (current production)   |  8.6% |  n/a  |   ~1500  |       —       |
| struct-only sentinel (β=0, no detail channel)             | 11.4% |  n/a  |   ~1500  |    +2.8 pp    |
| **SigLIP-base** + minimal text                            |**24.3%**|56.8%|     334  |   +15.7 pp    |
| SigLIP-base-384 + minimal text                            | 24.3% | 54.1% |     478  |   +15.7 pp    |
| SigLIP-base + rich text (incl. global features)           | 16.2% | 56.8% |     325  |    +7.6 pp    |
| SigLIP-base + specific text (≤2-node features only)       | 16.2% | 51.4% |     336  |    +7.6 pp    |
| **SigLIP-so400m** + minimal text **← best so far**         |**37.8%**|**56.8%**| 1399  |  **+29.2 pp** |
| CLIP-large + minimal text (sanity)                        | 16.2% | 37.8% |    ~600  |    +7.6 pp    |

**Findings:**
- The single largest win is **changing the perception layer**, not tuning anything
  downstream. BLIP-base captions are categorically too lossy (5–10 tokens, often
  hallucinated — IMG_0107's entrance doors → "a television in the corner").
  SigLIP scores the photo against node text *directly*, never collapsing visual
  signal through a captioning bottleneck.
- **Text composition matters but model size matters more.** With base SigLIP,
  minimal text (24.3%) beat rich text (16.2%) — adding noisy "global features"
  (like "brown pad chair on yellow line (temporary)" appearing in many nodes)
  *hurt*. With so400m, the model is robust enough that even minimal text yields
  37.8%; richer specific text might push higher (untested).
- **CLIP-large is a poor fit** for this task (16.2%, severe attractor collapse
  on `poi04_wall_3d_printers`). SigLIP's contrastive sigmoid loss handles small
  retrieval pools better than CLIP's softmax loss.
- **top5 plateaus at ~57%** across all SigLIP variants. The right answer is in
  the top-5 over half the time — exactly where cross-encoder rerank (Plan C)
  would pay off. SigLIP keeps recall, a true cross-encoder picks the winner.
- **Latency is fine:** so400m at 1.4 s/photo on CPU is slower than base SigLIP
  (~330 ms) but comparable to the current BLIP+fusion pipeline (~1.5 s).

**Plan C status — blocked on choice of reranker backend:**
- BLIP-ITM (the natural cross-encoder for this task): all variants only have
  `pytorch_model.bin`, no safetensors. torch 2.5.1's `check_torch_load_is_safe`
  refuses to load them (CVE-2025-32434). Either upgrade torch to ≥ 2.6 (risk to
  other deps) or wait for upstream safetensors conversion.
- GPT-4o-mini vision (`OAI.chat.completions.create` with image input): the
  OpenAI client is already wired (used by `/api/qa`), but `OPENAI_API_KEY` is
  not set in `.env`. Would give a real cross-encoder pass over top-5 at ~$0.001
  per query.
- Local ensemble (SigLIP-so400m + CLIP-large cosine averaging): plausible but
  CLIP-large is so weak that the ensemble unlikely beats so400m alone — untried.

**Update — Plan C tested (GPT-4o-mini vision rerank): regression to 21.6%.**

User provided OPENAI_API_KEY (stored in `.env`, gitignored). Added GPT-4o-mini
vision rerank backend to `eval_siglip.py` (`--rerank-backend gpt4o`). First run
collapsed all predictions onto a single label (top1=13.5%) because the minimal
SigLIP-friendly text "A photo of poi14 main work table" is too generic for the
LLM — it defaults to picking the most generic-sounding label.

Switched to a *dual-text* design (recall uses minimal labels, rerank uses rich
descriptions). Second run: **top1=21.6% — still worse than SigLIP-so400m alone
at 37.8%.** Diagnosis: the reranker is being misled by **textmap data quality**,
not by reranker capability:

- The struct↔detail alias schema makes `poi07_cardboard_boxes` inherit
  `orange_sofa_corner`'s `unique_features` (orange sofa, green armchair). When
  GPT-4o is shown a photo of cardboard boxes plus rich-text options describing
  "orange sofa" for the correct-by-id node, it sensibly picks a different one.
- Strong recall + wrong descriptions = reranker actively destroys correct
  top-1 predictions from SigLIP.

**The bottleneck has shifted.** BLIP captioning was the bottleneck up to 24%;
SigLIP-so400m pushed it to 38% by eliminating that bottleneck; now the next
ceiling is **textmap data quality / alias schema** — both the per-node
descriptions and the struct↔detail mapping have semantic errors that propagate
to any text-based matching.

**Three paths forward:**
1. **Ship B alone** — `SigLIP-so400m + minimal text` at 37.8% / 4.4× baseline.
   Wire into `/api/locate` as a new path, leave fusion code intact behind a
   flag. Lowest-risk win.
2. **Fix textmap first, then C** — un-alias the schema (one ID space, not two),
   rewrite per-node descriptions so they describe what is *visually present*
   not what entity sits at that position. Then redo GPT-4o rerank — should
   push 45–55%.
3. **Different rerank strategy** — instead of "pick a letter from N options",
   have GPT-4o caption the photo first in ~25 words, then match that free-text
   to candidates via SigLIP. The LLM becomes a better-than-BLIP captioner
   without having to also know the textmap. Untested.

## Unreleased — Plan A (hyperparameter sweep) — disproven on ground truth (2026-06-07)

**TL;DR: tuning the fusion hyperparameters cannot fix the system.** Built the
labeled-photo evaluation harness, ran a 27-combo grid + 4 sentinel trials. The
architecture has a hard ceiling of **~10% top-1 accuracy on 20 nodes** (random
baseline = 5%). Dual fusion is making the system *worse* than a single channel.

**What was added (kept):**
- `backend/tools/sweep_fusion.py` — labeled-photo benchmark driver. Maps the 20
  SENSE_A_Photo + 17 SENSE_B_Photo images to ground-truth node IDs via the
  `photo_refs` field in `data/Sense_A_MS.jsonl` / `data/Sense_B_Studio.jsonl`,
  plus the struct↔detail alias table in `enhanced_ft_retrieval`. Runs each
  hyperparameter combo against the full 37-photo set, reports top1_acc, mean
  conf, mean margin, low_conf rate, prediction distribution.
- Six fusion hyperparameters lifted from hardcoded values to env vars
  (`FUSION_GAMMA`, `FUSION_NEG_PENALTY`, `FUSION_STRUCT_TAU`, `FUSION_DETAIL_TAU`,
  `FUSION_CONFLICT_GAP`, `FUSION_ALPHA_FB` / `FUSION_BETA_FB`) so an outer
  driver can sweep them. `FUSION_TEMPERATURE` was already env-tunable.
- Diagnostic force-overrides `FUSION_ALPHA_FORCE` / `FUSION_BETA_FORCE` that
  bypass `_adaptive_weights` entirely — used to run the struct-only / detail-only
  sentinel trials.

**Findings on ground truth (n=35 trials after warmup):**

| Setup                                          | top1_acc | mean_conf | mean_margin |
|------------------------------------------------|---------:|----------:|------------:|
| baseline (current adaptive α/β)                | **8.6%** |     0.845 |       0.664 |
| struct_only (α=1, β=0)                         | **11.4%**|     0.743 |       0.602 |
| detail_only (α=0, β=1)                         | **8.6%** |     0.717 |       0.475 |
| sharp_T (T=0.05, neg_pen=0.30)                 | **8.6%** |     0.947 |       0.919 |
| 27 grid combos (3×3×3 over α/β/T/neg_pen)      | **8.6%** | varies    | varies      |

1. **The dual fusion is hurting the system, not helping.** Struct-only beats
   the fused baseline (11.4% vs 8.6%). The detail channel pollutes the struct
   prediction; β=0.65 (current default) gives it too much weight.
2. **Confidence and margin are decoupled from accuracy.** sharp_T returns 95%
   mean confidence and 92% margin on the same 8.6% accuracy — the system is
   "highly confident and almost always wrong", which is the most dangerous
   failure mode for blind users.
3. **Some env vars only affect the fallback path** that almost never fires —
   `FUSION_ALPHA_FB` / `FUSION_BETA_FB` only kick in when both channel
   entropies are zero, and `self.alpha` / `self.beta` set in the retriever
   `__init__` are *cosmetic* (printed at startup, never read by the math).
   The real per-query α/β come from `_adaptive_weights` (entropy-driven).

**Diagnosis already established (see preceding architecture report):**
- BLIP-base outputs 5–10 token captions like "there is a room with a desk,
  chair, and a trash can" — only 17 distinct captions across 37 photos. For
  IMG_0107 (glass entrance doors) BLIP returned "there is a television sitting
  in the corner of a room". The perception layer is the upstream bottleneck;
  no downstream re-weighting can recover signal that never entered.
- Textmap vocabulary is reasonable (mentions yellow line, glass doors, brown
  chair, 3D printer); the alias schema between struct (`poi09_qr_bookshelf`)
  and detail (`chair_on_yline`) is confused (positional vs entity naming).

**What this means for next steps:**
- Plan A (hyperparameter tuning) is empirically disproven. Do not pursue.
- Short-term mitigation if B+C is delayed: set `FUSION_ALPHA_FORCE=1.0` and
  `FUSION_BETA_FORCE=0.0` (struct-only) for a 1-hit-out-of-35 improvement
  *and* honest confidence values (no longer ~95% confident on wrong answers).
- The B+C work (SigLIP-direct image–text matching to replace BLIP captioning,
  optional cross-encoder rerank) is now empirically necessary, not just
  recommended. Branch `feature/siglip-rerank` is ready to check out.

## Unreleased — backend tier-1 bug fixes + tier-2 dead-code purge (2026-06-04)

Minimal-risk cleanup on `main` before branching off for B+C (SigLIP recall +
cross-encoder rerank). `app.py` shrunk **5125 → 4239 lines (−17%)**; 32 → 30 routes
(removed two endpoints that always returned `"Route not found"`); 20-photo SCENE_A
benchmark **identical** to pre-cleanup baseline (mean conf 0.779, mean margin 0.583,
low_conf rate 21.1%, channels_agree 0/19, same node distribution) — confirming the
deletions and refactors are non-behavior-changing on the retrieval path.

**Tier 1 — real bugs fixed:**
- `get_location_description(top1_id, site_id)` at the `/api/locate` response was
  passing `site_id` (a `str`) where `detail_items=None` was expected; the function
  iterated the string and called `.get(...)` on each char, raising `AttributeError`
  that the broad `try/except` swallowed. **Every** response's `current_location`
  field silently fell back to the templated message. Fixed by passing
  `top1.get('detail_items', [])` — detail enrichment can now actually fire.
- `get_next_action(*args, **kwargs)` was a stub that ignored all arguments and
  emitted the same hardcoded yellow-line phrase on every photo. Replaced with
  `{"say": ""}` so the field stays for FE compatibility but no longer broadcasts
  a misleading instruction (the real per-node turn+step text is already in
  `navigation_instruction`).
- The `/api/locate` warmup path was duplicated as two ~70-line blocks
  (`if first_photo:` and `if photo_count == 0:`), and the second wrote 22 columns
  to `locate_log.csv` against a 20-column schema, drifting timing columns. Merged
  into one branch keyed on `is_warmup = first_photo or photo_count == 0`; column
  drift fixed.
- `get_detail_based_conversation_enhancement` hardcoded Chinese spatial labels
  (`前方/左侧/右侧/后方/特色`) regardless of `lang`, so English users got
  mixed-language output. Labels now switch on `lang`.
- `_calculate_detail_score` was defined twice on the retriever class; Python kept
  the later (richer) override silently. Deleted the dead earlier copy.

**Tier 2 — provably dead code removed:**
- Orphan helpers (no callers anywhere): `match_detailed_descriptions` (the unused
  +0.4 `key_equipment` bonus path), `calculate_detail_enhancement`,
  `combine_retrieval_results`, `guess_bearing_from_caption`, `llm_intent` +
  `INTENTS` + `SYS_PROMPT`, `generate_navigation_context`.
- The `generate_ai_spatial_reasoning` family — 6 self-referential functions
  (~220 lines) producing a hardcoded multi-paragraph string from regex-matching
  scene names. No external caller.
- `apply_softmax_calibration` helper + `SOFTMAX_TEMPERATURE` /
  `ENABLE_SOFTMAX_CALIBRATION` constants — softmax calibration was hardcoded off
  and the helper had no callers. The live softmax sits in the retriever's
  per-channel calibration and the final `FUSION_TEMPERATURE=0.25` softmax.
- `validate_location_continuity` + its `adjacent_locations` table — generic name
  keys never matched real node IDs; output was recorded into history but never
  read. The continuity boost that actually fires lives in `apply_continuity_boost`
  + topology_prior inside the retriever.
- `get_location_distance` + the **two endpoints** `/api/location/verify/{sid}` and
  `/api/location/navigate/{sid}` that depended on it — same generic-name vs real-ID
  key mismatch meant every call returned `{"error": "Route not found"}`. Broken
  endpoints, removed.
- `are_neighbors` stub (TODO `return False`) + its `cons = 1.05` branch in
  `calibrate_confidence` — the elif was dead, simplified to same/diff/missing.
- `content_match` parameter in `calibrate_confidence` — both callers passed
  hardcoded `1.0`, the `max(0.75, content_match)` term collapsed to a no-op.
  Parameter dropped from signature.
- `TH_UP=0.60` / `TH_DOWN=0.35` constants in `apply_continuity_boost` — defined
  but never read.
- A dead content-relevance gate at the `/api/locate` exception fallback (×0.6
  on low word-overlap + ×0.5 on caption containing "desk") that had an
  indentation bug (`content_match_score` referenced outside the scope that
  defined it). Block sat in a near-unreachable branch and contradicted the
  calibration pipeline — removed.

## Unreleased — DG evaluator restore + discrimination instrumentation (2026-05-27)

**Goal:** fix the `dg_evaluator` NameError properly (not a stub patch) and make it
serve retrieval-discrimination accuracy.

- **[A] DG modules re-enabled.** Un-commented and `try/except`-guarded the imports +
  instantiation of `DGEvaluationManager`, `AccessibilityChecker`, and
  `IndoorGMLGenerator` in `app.py` (import failure → `None`, so the `if x:` guards
  scattered through the code actually work). `/health/enhanced` returns 200 again
  (was 500 on `NameError: name 'dg_evaluator' is not defined`). `user_needs_validator`
  kept as an explicit `None` placeholder; `enhanced_metrics_collector` remains a no-op
  stub — both still out of scope.
- **[B] Discrimination metrics added to DG2.**
  - `SemanticMapEvaluator.record_discrimination_event(...)` + `get_discrimination_stats(...)`
    in `dg_evaluation_enhancement.py` (avg/p10/p50/p90 margin, tie-rate < threshold,
    channel-agreement rate, neg-hit rate).
  - `_enhanced_fusion` now exposes per-candidate `neg_hits` + `stable_query_applied`;
    `retrieve()` records a discrimination event after ranking. `enhanced_ft_retrieval`
    threads `session_id` through so events land on the right session (else `anonymous`).
  - New endpoint `GET /api/dg/metrics/discrimination/{session_id}`
    (`?include_events=true&limit=N`, `session_id=all` to aggregate).
  - `_analyze_dg2` folds a `discrimination_score` into the DG2 report.
- **Docs consolidated.** All former `backend/README_*.md`, `backend/*_SUMMARY.md`,
  `PROJECT_SUMMARY.md`, `IP_CONFIG.md`, and the two `frontend/README*.md` were merged
  into `README.md` + this `CHANGELOG.md` and deleted.

---

## v1.0.0 — 2025-01-07

Initial tagged release (maintainer: LarryYiGuo). Bundled the full DG-optimization
feature set, comprehensive test suite, and one-click startup script. *(Note: the
DG-evaluation / IndoorGML / accessibility layer was only partially wired into the live
app — see the 2026-05-27 entry.)*

---

## Localization-quality push (late 2024)

The bulk of the engineering history is a long sequence of retrieval-accuracy and
confidence-calibration changes. Approximate order:

### Layered Fusion architecture v1.0 — 2024-12-19 *(production-ready)*
- Refactored `enhanced_ft_retrieval()` to localize using the **structure channel
  only**, excluding detail from scoring to keep confidence "pure".
- `generate_dynamic_navigation_response()`: structure gives topological position,
  detail enriches with landmark descriptions; channels aligned via `node_hint`.
- Added `generate_scene_a/b_structure_info()` (zh/en) with graceful degradation when
  detail files are missing.

### Critical retrieval/calibration fixes — 2024-12-19 *(5/5 tests passed)*
- Fixed an always-empty detail channel via `_build_detail_index()` +
  `_normalize_node_id()` aligning detail keys to structure node IDs.
- Replaced softmax confidence calibration (which inflated 0.62 → 0.998) with linear
  normalization (`τ_low=0.10`, `τ_high=0.50`; capped at 0.65 when no detail). Added
  `_adaptive_weights()` so detail weight drops to 0 when unavailable.
- Fixed continuity boost (was always −0.05): now 0.0 on position change, +0.05 when
  consistent, clamped `[−0.05, 0.10]`. Added `get_location_description()` /
  `enhanced_metrics_collector()` stubs to stop NameError fallbacks.

### Enhanced Dual-Channel Fusion fixes — v2.0, 2024-08-22
- Fixed 4 runtime bugs: cache-on-method-object (`_cache` → instance `_detail_cache`),
  JSONL line-split parse error in `Sense_A_MS.jsonl` (now 26 valid lines / 10 nodes),
  undefined `conflict_strategy`, and empty detail-data loading (unified
  `_load_detail_once`). Also fixed a secondary-sharpening numpy-bool crash and added
  fail-fast on empty topology.
- Result reported: confidence 0.20–0.40 → 0.84–0.98; margin 0.01–0.20 → 0.69–0.99.

### Fusion-formula evolution (undated, iterative)
The score-fusion formula was reworked several times:
1. **Linear** — `Final = α·s_struct + (1−α)·s_nl + β·kw + γ·bearing`; baseline
   `RANK_ALPHA=0.7`, `RANK_BETA=0.05`, `RANK_GAMMA=0.03`; provider split
   `RANK_ALPHA_FT=0.7`, `RANK_ALPHA_4O=0.0`; `CONFIDENCE_THRESHOLD=0.07`.
2. **Additive overlay** — `C = C_struct + β·C_detail` (`β=0.15`, detail cap 0.4); set
   `LOWCONF_SCORE_TH=0.60`, `LOWCONF_MARGIN_TH=0.20`.
3. **Multiplicative overlay** — `C = C_struct × (1 + α·C_detail)` (`α=0.3`, capped
   +20%); overlay only Top-3; conflict detection (threshold 0.3) → clarification.
4. **Log-odds (current)** — channels combined in logit space, sharpened by a fusion
   softmax (`T=0.25`).

### Channel-weight drift
Structure/detail weights were tuned downward for the structure channel over time:
`0.45 / 0.55` → `0.40 / 0.60` → **`0.35 / 0.65`** (current).

### Enhanced discrimination + negative-evidence penalty
- Problem: structure channel kept tying at `0.488 / 0.488` (over-broad index words).
- Added per-node `cnl_index` / `index_terms` discriminators + `negative` fields with
  `apply_negatives` (penalty `0.15`). New data file
  `Sense_A_Finetuned_enhanced.jsonl`. Margin target `0.000 → 0.350+`.

### `stable_query` movable-object filter
- Same `0.488 / 0.488` tie, root cause = movable junk (suitcase / bins / boxes).
- Structure channel now runs `stable_query()`: deletes `MOVABLE` words
  (suitcase/bag/backpack/person/cup/bottle/laptop/phone/book), ×0.5 down-weights
  `LOW_TRUST` words (bin/box/item/stuff/thing/object). Detail channel keeps the raw
  caption. Applied before `apply_negatives`.

### Enhanced FT retrieval for SCENE_A_MS
- Problem: `ft` mode echoed canned content / mis-identified nodes.
- Added a second detailed-description matcher + result fusion; expanded keyword vocab
  7 → 35; `+0.3` key-equipment bonus (3d printer / ender / ultimaker / oscilloscope /
  workbench).

### Content-relevance & semantic-mismatch checks
- Problem: `chair_on_yline` mis-recognized for unrelated images (bookshelf,
  electronics table) due to over-broad chair keywords + structural dominance.
- Added word-overlap `content_match_score`; structural weight 60→45→**35%**, detail
  40→55→**65%**; match threshold `0.3 → 0.15`; low-match → confidence `×0.6` (−40%);
  semantic-mismatch (e.g. caption says "desk" but node text doesn't) → `×0.5` (−50%);
  effects can stack.

---

## Confidence & metrics instrumentation (undated)

### Confidence scoring & Top-1 tracking
- Added confidence + margin computation and `locate_log.csv` logging, optional
  `gt_node_id`, provider tracking, and `tools/metrics_top1.py`. Initial low-conf rule:
  `top1_score < 0.4 or margin < 0.07`.

### Comprehensive metrics system
- Added Top-2 and ±1-hop accuracy (via `topology.json`), per-request `req_id`,
  end-to-end latency via `/api/metrics/tts_start` + `latency_log.csv`, configurable
  low-conf thresholds, `tools/metrics_eval.py`, `tools/experiment_manager.py`.

### Confidence optimization v1.0 → v1.4
- v1.0 softmax calibration (`τ=0.06`), v1.1 continuity boost, v1.2 raised thresholds
  to `0.45 / 0.08`, v1.3 added `similarity_distribution.csv`, v1.4 config docs.
  *(Softmax calibration was later force-disabled; see 2024-12-19 fixes.)*

### RQ3 — trust & error handling
- Added misbelief detection (`misbelief`, `clarification_triggered`),
  `clarification_log.csv` + `/api/metrics/clarification_round`, `recovery_log.csv`, and
  `tools/rq3_evaluation.py`. Defined Baseline A (no proactive clarification) vs
  Enhanced B (auto-clarify on low confidence).

---

## Navigation, textmap, language (undated)

### AI spatial-reasoning system
- Replaced 4 static preset answers with dynamic generation: photo → BLIP caption →
  textmap analysis → spatial reasoning → personalized guidance (~15 new functions).
  The reasoning step is **simulated** (placeholder for a future GPT-4 / Claude / local
  LLM). Added language auto-detection (`ft`→zh, `base`→en).

### Dynamic navigation system
- Problem: system kept announcing "you are at the entrance" even after the user moved.
- Added the warm-up / trial two-phase response, `generate_dynamic_navigation_response`,
  per-node location/next-action functions, and `navigation_instruction` /
  `current_location` / `next_action` response fields.

### Location-tracking system
- Added per-session location/orientation/confidence history, continuity validation
  (`validate_location_continuity`), second-pass per-question location judgment, abstract
  destination detection, distance/ETA calc, and the
  `/api/session/*` + `/api/location/*` endpoints. Config: `LOCATION_CONFIDENCE_THRESHOLD=0.07`,
  `ORIENTATION_CONSISTENCY_CHECK=true`, `LOCATION_HISTORY_MAX=10`.

### Textmap improvement & optimization
- Problem: returned generic IDs (e.g. `Sense_A_4o_0`) instead of specific nodes; low
  confidence (0.3–0.5).
- Created detailed per-node descriptions with multi-view `photo_refs`,
  `unique_features`, precise `spatial_relations` (with distances),
  `landmark_combinations`; fusion config `{topo_semantic: 0.45, visual_detail: 0.55}`
  + confidence boosts + `spatial_reasoning` fallback.

### Spatial-relationship & navigation-logic fix
- Switched vague relative positions ("behind the desks area") to nearest-landmark
  descriptions ("between the window and the television screen"); replaced
  forced-backtracking routes with multi-option direct paths. Added nodes
  `atrium_desks_hub`, `node_left_to_windows`, `atrium_windows_edge`, `poi_small_table`,
  `poi_orange_green_sofa`.

### Language-handling fix
- Problem: Base/4o mode returned English `output` but dynamic navigation was hardcoded
  Chinese.
- Added `detect_language_from_caption`, made all navigation functions bilingual
  (`lang` param), enforced Base = en / ft = zh consistency.

---

## DG framework build-out (undated)

### DG1–DG6 optimization plan
- 6-week / 3-phase plan aligning evaluators with user needs N1–N6, standardized scales
  (NASA-TLX, SUS), and success criteria. High priority: DG1/DG2/DG4/DG6.

### DG evaluator module implementation
- Implemented 5 standalone modules: `dg_evaluation_enhancement.py`,
  `user_needs_validator.py`, `accessibility_checker.py`, `indoor_gml_generator.py`,
  `enhanced_metrics_collector.py`. At the time these were **not yet wired** into the
  live app (backend integration / frontend rating UI / DB schema pending). Three of
  them were wired up on 2026-05-27 (see top entry).

---

## Frontend

### Voice-control enhancement
- The **Ask** button cancels active TTS before recording to avoid speech/recording
  overlap; added start/stop console logging. Web Speech API TTS + `MediaRecorder`
  capture; works across Chrome/Edge/Safari/Firefox on desktop and mobile.
