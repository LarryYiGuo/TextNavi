# TextNavi (VLN4VI) — Indoor Navigation for the Visually Impaired

TextNavi is a vision–language indoor navigation web app for blind and low-vision
users. The user photographs their surroundings; the system localizes them inside a
known indoor scene, then generates natural-language, voice-guided navigation
instructions (e.g. *"walk forward about six steps to the 3D-printer table, then turn
left"*) and answers spoken questions about the environment.

> Documentation policy: this repository keeps **only two** Markdown docs —
> this `README.md` (current state) and [`CHANGELOG.md`](CHANGELOG.md) (history of
> changes). Per-feature `README_*.md` files that used to live under `backend/` were
> consolidated and removed; recoverable from git history.

---

## 1. What it does

- **Photo → location, directly via SigLIP.** A single photo is encoded by
  SigLIP-so400m and matched (cosine) against pre-embedded text descriptions of
  the 18 scene nodes — no captioning bottleneck.
- **Paper-parity accuracy.** 73.0% useful top-1 on the labeled 37-photo
  benchmark (paper Table 4 metric: predicted node = GT or 1-hop neighbour in
  the topology graph). Matches the paper's fine-tuned baseline (SenseA 74%,
  SenseB 82%).
- **Dynamic navigation.** Step-by-step instructions per matched node, with a
  two-phase (warm-up → trial) flow tracking the user across successive photos.
- **Confidence & margin gating.** Low-confidence localisations trigger a
  re-photo prompt instead of guessing.
- **Voice I/O.** faster-whisper ASR for spoken questions, Web Speech API TTS
  for replies.
- **Bilingual.** `ft` (fine-tuned) provider replies in Chinese; `base`/`4o` in
  English; auto-detected from BLIP caption + provider.

Two demo scenes ship with the system: **`SCENE_A_MS`** (Maker Space, 10 nodes)
and **`SCENE_B_STUDIO`** (Studio, 8 nodes).

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (`backend/app.py`), served by **uvicorn on port 8001** |
| **Retrieval (primary)** | **SigLIP-so400m** (`google/siglip-so400m-patch14-384`) image→text matching against `data/textmap_clean.jsonl`. ~6 s cold load, ~1.4 s/photo on CPU. |
| Retrieval (legacy fallback) | BLIP caption + dual-channel-fusion in `app.py`. Kept behind `ENABLE_SIGLIP=false`. |
| Caption | Local **BLIP** (`Salesforce/blip-image-captioning-large`, CPU) — used for `caption` log field + bearing detection regardless of retrieval path |
| ASR | **faster-whisper** (local cache) |
| QA | OpenAI GPT-4o-mini via `OPENAI_API_KEY` in `.env` — only for `/api/qa` |
| Frontend | **React 19 + Vite 7** (`frontend/`), HTTPS dev server on **port 5173** via `vite-plugin-mkcert` |
| Logs | CSV logs under `backend/logs/` |
| Runtime | Python 3.8+ (tested on 3.12), Node 18+, torch 2.5+, transformers ≥ 4.45 |

---

## 3. Directory layout

```
TextNavi/
├── backend/
│   ├── app.py                        # FastAPI app: endpoints + legacy fusion + nav logic
│   ├── siglip_retriever.py           # ★ SigLIP-so400m image→text-template retriever (primary)
│   ├── dual_channel_retrieval.py     # legacy fusion retriever (fallback only)
│   ├── topology.json                 # scene topology (used for ±1-hop accuracy)
│   ├── dg_evaluation_enhancement.py  # DG1–DG6 evaluators (ENABLED)
│   ├── accessibility_checker.py      # WCAG 2.2 / VoiceOver checks (ENABLED)
│   ├── indoor_gml_generator.py       # IndoorGML export (ENABLED)
│   ├── user_needs_validator.py       # N1–N6 validation (NOT wired — see §8)
│   ├── enhanced_metrics_collector.py # metrics sink (NOT wired — see §8)
│   ├── database_optimization.py
│   ├── comprehensive_testing.py
│   ├── data/
│   │   ├── textmap_clean.jsonl       # ★ hand-curated node text for SigLIP (18 entries)
│   │   ├── Sense_A_Finetuned.fixed.jsonl / Sense_B_Finetuned.fixed.jsonl   # legacy structure
│   │   ├── Sense_A_MS.jsonl          / Sense_B_Studio.jsonl                # legacy detail
│   │   └── Sence_A_4o.fixed.jsonl    / Sense_B_4o.fixed.jsonl              # base/4o mode
│   ├── tools/
│   │   ├── eval_siglip.py            # ★ SigLIP accuracy benchmark (4 text modes, 2 rerank backends)
│   │   ├── eval_image_knn.py         # image-image KNN (Plan E, kept for diagnosis)
│   │   ├── eval_merged.py            # node-merging taxonomy (Plan F)
│   │   ├── topology_eval.py          # struct↔topology mapping + paper Table 4 metric
│   │   ├── sweep_fusion.py           # legacy fusion hyperparam grid driver (Plan A)
│   │   ├── experiment_manager.py     # CLI to group locate runs by session
│   │   └── metrics_eval.py / metrics_top1.py / rq3_evaluation.py
│   └── logs/  models/  metrics_data/
├── frontend/
│   ├── src/ (App.jsx)
│   ├── vite.config.js                # HTTPS + mkcert + /api proxy → backend
│   └── package.json
├── start_webapp.sh                   # canonical launcher (port 8001 + npm run dev)
├── start_system.py                   # one-click launcher — STALE (see §4)
├── README.md                         # this file
├── CHANGELOG.md
└── .env                              # gitignored — OPENAI_API_KEY etc.
```

---

## 4. Quick start

```bash
# 1. Install deps
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Run backend (port 8001). First run downloads SigLIP-so400m (~870 MB to
#    ~/.cache/huggingface/hub) — adds ~6 s to subsequent cold starts.
cd ../backend
uvicorn app:app --reload --host 0.0.0.0 --port 8001

# 3. Run frontend (HTTPS, port 5173) in a second terminal
cd ../frontend
npm run dev          # or: npm run dev:http  (plain HTTP)
```

Access:

- Frontend UI: `https://localhost:5173/` (self-signed cert via mkcert — accept it)
- Backend API: `http://localhost:8001`
- Health: `http://localhost:8001/health` and `/health/enhanced`
- Interactive API docs: `http://localhost:8001/docs`

> **Note on `start_system.py`** — the one-click launcher is currently **stale**:
> hardcoded ports 8000/3000 and shells out to `npm start` (the frontend script
> is `npm run dev`). Prefer the manual commands above or `start_webapp.sh`.

### Network / mobile access

The frontend dev server binds `0.0.0.0` so phones on the same LAN can reach it.
The Vite proxy forwards `/api` to the backend at a **hardcoded IP** in
`frontend/vite.config.js` (`target: 'http://<IP>:8001'`). When your network
changes, update that line (and any display URLs in `start_webapp.sh`).

---

## 5. Request flow

```
photo ─▶ SigLIP image embed ─▶ cosine vs 18 pre-embedded node texts ─▶ top-1
       ─▶ confidence/margin gate ─▶ generate_dynamic_navigation_response ─▶ TTS
```

When `ENABLE_SIGLIP=false` (or SigLIP load fails), the flow falls back to the
legacy BLIP-caption + dual-channel-fusion path inside `app.py`.

### 5a. Two-phase localization (per session)

Each session tracks a `photo_count`. The **1st photo is a warm-up** that returns
a preset scene description (no retrieval). **From the 2nd photo onward** the
system runs the full SigLIP retrieval → navigation pipeline.

### 5b. Navigation instructions

`generate_dynamic_navigation_response(...)` returns
`navigation_instruction`, `current_location`, `next_action`, and
`retrieval_method`. The `retrieval_method` field on the response distinguishes
paths:

- `"siglip_so400m_v1"` — SigLIP (default)
- `"preset_output"` — warm-up first photo
- `"enhanced_dual_channel_fusion"` / `"unified_dual_channel_fusion"` — legacy
  fallback

### 5c. Session state

`SESSIONS[session_id]` holds: `site_id`, `opening_provider`, `lang`,
`current_location`, `location_history`, `orientation_history`,
`confidence_history`, `last_update_time`, `photo_count`. `track_orientation`
maintains orientation across photos.

---

## 6. Retrieval — SigLIP image-text matching (primary)

`backend/siglip_retriever.py` is a module-level singleton that:

1. Loads `google/siglip-so400m-patch14-384` once at startup (~6 s, 870 MB
   model cached in `~/.cache/huggingface/hub`).
2. Pre-embeds all 18 nodes from `data/textmap_clean.jsonl` to 1152-d vectors
   (~5 s, done once).
3. Per request: encodes the query photo (~1.4 s on CPU), computes cosine vs
   all node embeddings, filters by `site_id`, returns top-K.

**Why `textmap_clean.jsonl`?** The original `Sense_A_MS.jsonl` had alias
schema confusion (e.g. `poi07_cardboard_boxes` inherited features from its
position-alias `orange_sofa_corner`). `textmap_clean.jsonl` is a hand-curated
18-entry rewrite where each node's description matches what's actually visible
in its labeled photos. Yields top-5 recall of 73.0% (vs 56.8% with original).

**Confidence mapping**: `sigmoid(12 · (cosine - 0.15))` maps SigLIP cosine
(typical range 0.05–0.30) to a friendly 0–1 confidence. Margins are
top1−top2 *confidence* (not raw cosine).

**Legacy fallback (`ENABLE_SIGLIP=false`)**: the older fusion path
(`_enhanced_fusion` in `app.py`) combines a structure channel + detail channel
via log-odds fusion with `FUSION_*` env-tunable hyperparameters (see
`backend/tools/sweep_fusion.py`). On the same benchmark it produces only ~50%
useful top-1 — kept solely as a fallback.

---

## 7. Confidence, margin & metrics

- **Low-confidence rule**: `low_conf = top1_score < 0.50 or margin < 0.10`
  (`LOWCONF_SCORE_TH`, `LOWCONF_MARGIN_TH`). Aligned with paper §3.4.
- **Known follow-up**: those thresholds were tuned for legacy fusion margin
  distributions (0.5+ typical). SigLIP cosine margins are 0.02–0.15, so the
  same thresholds flag more requests as low_conf — safer default for visually
  impaired users (more re-photo prompts) but worth a SigLIP-specific
  recalibration after collecting production data (see CHANGELOG).
- **Metrics logged** under `backend/logs/`: `locate_log.csv`
  (top1/top2/margin, optional `gt_node_id`, hit flags, timing),
  `latency_log.csv`, `clarification_log.csv`, `recovery_log.csv`,
  `similarity_distribution.csv`.
- **Paper-equivalent useful top-1** (= ±1-hop accuracy in the topology graph):
  `backend/tools/topology_eval.py` provides the struct↔topology mapping and
  `is_useful()` helper used by `eval_siglip.py` to report strict / same-cell /
  useful metrics side-by-side.

---

## 8. DG1–DG6 evaluation framework

Six design goals map to user needs N1–N6:

| Goal | Meaning | Needs |
|------|---------|-------|
| DG1 | No special hardware dependency | N2, N6 |
| DG2 | Semantic textual-topological map | N1 |
| DG3 | Useful precision in localization | N2 |
| DG4 | Segmentable & repeatable instructions | N3 |
| DG5 | Uncertainty handling & faculty trust | N4 |
| DG6 | Accessibility, compliance & testability | N5, N6 |

**Current wiring status:**

| Module | Status |
|---|---|
| `dg_evaluation_enhancement.py` (`DGEvaluationManager`, DG1–DG6 evaluators) | **Enabled** (try/except import with `None` fallback) |
| `accessibility_checker.py` | **Enabled** |
| `indoor_gml_generator.py` | **Enabled** |
| `enhanced_metrics_collector.py` | **Not wired** — placeholder `None`; `/api/dg/metrics/*` endpoints return HTTP 503 |
| `user_needs_validator.py` | **Not wired** — placeholder `None`; `/api/dg/user_needs/*` endpoints return HTTP 503 |

`DGEvaluationManager.dg2_evaluator` records **retrieval discrimination** as an
objective DG2 signal (avg margin, tie rate, channel-agreement rate). Pull stats
via `GET /api/dg/metrics/discrimination/{session_id}` (`?include_events=true`
or `session_id=all` to aggregate).

---

## 9. API endpoints

**Core**
- `GET  /health` · `GET /health/enhanced` — service + DG module status
- `POST /api/start` — open a session (`session_id`, `site_id`, `opening_provider`, `lang`)
- `POST /api/locate` — localize from an uploaded photo (multipart: `site_id`, `image`, `session_id`, `provider`, …). Response contains `retrieval_method` indicating which path served the request.
- `POST /api/asr` — speech-to-text
- `POST /api/qa` — answer a spoken/typed question (needs `OPENAI_API_KEY`)
- `GET  /api/session/location/{session_id}` · `GET /api/session/status/{session_id}`

**Metrics / experiment instrumentation**
- `POST /api/metrics/tts_start`
- `POST /api/metrics/clarification_round` · `/clarification_end`
- `POST /api/metrics/error_recovery_start` · `/error_recovery_end`
- `POST /api/logging/set` · `GET /api/logging/status`

**DG optimization** (503 when underlying module isn't wired — see §8)
- `POST /api/dg/metrics/collect` · `GET /api/dg/metrics/export/{session_id}` · `/analytics/{session_id}` · `/stats` · `POST /api/dg/metrics/session/{session_id}/close`
- `GET  /api/dg/metrics/discrimination/{session_id}` — **wired**, live for DG2
- `POST /api/dg/evaluation/record` · `GET /api/dg/evaluation/report/{session_id}`
- `POST /api/dg/accessibility/check` · `/voiceover`
- `POST /api/dg/indoor_gml/generate` · `/validate`
- `GET  /api/dg/user_needs/validation/{session_id}` · `POST /api/dg/user_needs/record` · `GET /api/dg/user_needs/matrix`

Full interactive list at `/docs`.

---

## 10. Configuration

Backend reads `<repo-root>/.env` (gitignored — secrets never committed).

```bash
# ── Retrieval ───────────────────────────────────────────────
ENABLE_SIGLIP=true                          # primary path; false = legacy fusion
SIGLIP_MODEL=google/siglip-so400m-patch14-384

# ── Confidence thresholds (see §7 re: SigLIP-specific recalibration TODO) ──
LOWCONF_SCORE_TH=0.50
LOWCONF_MARGIN_TH=0.10

# ── Legacy fusion (fallback path only) — env-tunable for diagnostics ──
FUSION_TEMPERATURE=0.25
FUSION_GAMMA=0.15
FUSION_NEG_PENALTY=0.15
FUSION_STRUCT_TAU=0.15
FUSION_DETAIL_TAU=0.20
FUSION_CONFLICT_GAP=0.50
FUSION_ALPHA_FB=0.65
FUSION_BETA_FB=0.35

# ── DG modules ──────────────────────────────────────────────
ENABLE_DG_EVALUATION=true
ENABLE_ACCESSIBILITY_CHECKING=true
ENABLE_INDOOR_GML=true

# ── LLM (used by /api/qa only, optional) ────────────────────
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...                       # required for /api/qa; also used by
                                            # eval_siglip.py --rerank-backend gpt4o

# ── BLIP (caption logging + bearing detection; loaded regardless) ──
BLIP_MODEL_PATH=Salesforce/blip-image-captioning-large
BLIP_DEVICE=cpu
```

The `.env` file lives at the **TextNavi project root** (sibling of `backend/`).
It is in `.gitignore`; secrets never get pushed.

---

## 11. Testing & evaluation

### SigLIP accuracy benchmark (primary)

```bash
cd backend
# default: SigLIP-so400m + clean text, no rerank
python tools/eval_siglip.py --text clean --model google/siglip-so400m-patch14-384

# with GPT-4o-mini cross-encoder rerank on top-5
python tools/eval_siglip.py --text clean --model google/siglip-so400m-patch14-384 \
    --rerank-backend gpt4o --rerank-k 5

# different text modes: rich / minimal / specific / clean
python tools/eval_siglip.py --text minimal
```

Reports `strict top1`, `same-topo-cell`, **`useful top1` (paper Table 4 metric)**,
top-5, average score, latency. Loads 37 labeled SENSE_A/B photos via
`tools/sweep_fusion.py:load_dataset()`.

### Legacy comprehensive suite

```bash
python comprehensive_testing.py
```

### Experiment manager

`backend/tools/experiment_manager.py` groups locate runs into named sessions
and auto-captures confidence/margin/Top-1 from every `/api/locate` call.

```bash
python tools/experiment_manager.py create --name run1 --description "post-deploy"
python tools/experiment_manager.py note   --session <id> --note "..."
python tools/experiment_manager.py show   --session <id>
python tools/experiment_manager.py export --session <id> --output run1.csv
```

Sessions are stored as `backend/logs/session_*.json`; per-locate rows in
`backend/logs/locate_log.csv`.

---

## 12. Voice control (frontend)

- Navigation replies and answers are spoken via the Web Speech API.
- Pressing **Ask** cancels any in-progress speech (`speechSynthesis.cancel()`)
  before recording starts, avoiding TTS/recording overlap.
- Audio is captured with `MediaRecorder` (`getUserMedia({audio:true})`); works
  on Chrome/Edge/Safari/Firefox, desktop and mobile.

---

## License & contact

MIT License. Maintainer: **LarryYiGuo** · ucbqwg7@ucl.ac.uk
