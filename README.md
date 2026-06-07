# TextNavi (VLN4VI) — Indoor Navigation for the Visually Impaired

TextNavi is a vision–language indoor navigation web app for blind and low-vision
users. The user photographs their surroundings; the system localizes them inside a
known indoor scene, then generates natural-language, voice-guided navigation
instructions (e.g. *"walk forward about six steps to the 3D-printer table, then turn
left"*) and answers spoken questions about the environment.

> Documentation policy: this repository keeps **only two** Markdown docs —
> this `README.md` (current state) and [`CHANGELOG.md`](CHANGELOG.md) (history of
> changes). The many per-feature `README_*.md` / `*_SUMMARY.md` files that used to
> live under `backend/` have been consolidated into these two and removed; their
> full content remains recoverable from git history.

---

## 1. What it does

- **Photo-based localization** — a single photo is captioned locally (BLIP) and
  matched against a textual topological map of the scene.
- **Dual-channel retrieval** — a *structure* channel (topology, used for scoring /
  positioning) is fused with a *detail* channel (rich landmark descriptions, used
  mainly to enrich the spoken reply).
- **Confidence & margin gating** — every localization reports a calibrated
  confidence and a top1−top2 margin; low-confidence results trigger a re-photo or a
  clarification dialogue instead of guessing.
- **Dynamic navigation** — step-by-step instructions are generated per node, with a
  two-phase (warm-up → trial) flow that tracks the user across successive photos.
- **Voice I/O** — faster-whisper ASR for questions, Web Speech API TTS for replies.
- **Bilingual** — `ft` (fine-tuned) provider replies in Chinese; `base`/`4o`
  provider replies in English; language is auto-detected from the caption + provider.

Two demo scenes ship with the system: **`SCENE_A_MS`** (Maker Space) and
**`SCENE_B_STUDIO`** (Studio).

---

## 2. Tech stack

| Layer        | Technology |
|--------------|------------|
| Backend      | FastAPI (`backend/app.py`), served by **uvicorn on port 8001** |
| Image caption| Local **BLIP** (`transformers` `BlipForConditionalGeneration` + `BlipProcessor`, PIL), CPU by default |
| ASR          | **faster-whisper** (local cache) |
| Retrieval    | Dual-channel retriever (`dual_channel_retrieval.py`) + FAISS index (`build_index.py`), `all-MiniLM-L6-v2` embeddings |
| Frontend     | **React 19 + Vite 7** (`frontend/`), HTTPS dev server on **port 5173** via `vite-plugin-mkcert` |
| Storage/logs | SQLite (metrics/evaluation) + CSV logs under `backend/logs/` |
| Runtime      | Python 3.8+ (tested on 3.12), Node 18+ |

---

## 3. Directory layout

```
TextNavi/
├── backend/
│   ├── app.py                        # FastAPI app: all endpoints + retrieval/nav logic
│   ├── dual_channel_retrieval.py     # structure + detail channel retriever
│   ├── build_index.py                # FAISS index builder
│   ├── topology.json                 # scene topology (used for ±1-hop accuracy & priors)
│   ├── dg_evaluation_enhancement.py  # DG1–DG6 evaluators (ENABLED)
│   ├── accessibility_checker.py      # WCAG 2.2 / VoiceOver checks (ENABLED)
│   ├── indoor_gml_generator.py       # IndoorGML export (ENABLED)
│   ├── user_needs_validator.py       # N1–N6 validation (NOT wired — see §8)
│   ├── enhanced_metrics_collector.py # metrics sink (NOT wired — see §8)
│   ├── database_optimization.py
│   ├── comprehensive_testing.py
│   ├── data/                         # textmap JSONL files (see §6)
│   ├── models/  logs/  metrics_data/
│   └── tools/                        # metrics_top1.py, metrics_eval.py, rq3_evaluation.py, ...
├── frontend/
│   ├── src/  (App.jsx, frontend_optimization.jsx)
│   ├── vite.config.js                # HTTPS + mkcert + /api proxy → backend
│   ├── vite.config.http.js           # plain-HTTP variant
│   └── package.json
├── start_webapp.sh                   # canonical launcher (port 8001 + npm run dev)
├── start_system.py                   # one-click launcher — STALE (see §4 note)
├── README.md                         # this file
└── CHANGELOG.md
```

---

## 4. Quick start

```bash
# 1. Install deps
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Run backend (port 8001)
cd ../backend
uvicorn app:app --reload --host 0.0.0.0 --port 8001

# 3. Run frontend (HTTPS, port 5173) in a second terminal
cd ../frontend
npm run dev          # or: npm run dev:http  (plain HTTP)
```

Access:

- Frontend UI: `https://localhost:5173/` (self-signed cert via mkcert — accept it)
- Backend API: `http://localhost:8001`
- Health check: `http://localhost:8001/health` and `/health/enhanced`
- Interactive API docs: `http://localhost:8001/docs`

> **Note on `start_system.py`** — the one-click launcher is currently **stale**: it
> hardcodes backend port `8000`, frontend port `3000`, and shells out to `npm start`
> (which does not exist — the frontend script is `npm run dev`). Prefer the manual
> commands above or `start_webapp.sh` until it is fixed.

### Network / mobile access

The frontend dev server binds `0.0.0.0` so phones on the same LAN can reach it. The
Vite proxy forwards `/api` to the backend at a **hardcoded IP** in
`frontend/vite.config.js` (`target: 'http://<IP>:8001'`). When your network changes,
update that line (and any display URLs in `start_webapp.sh`).

---

## 5. Request flow

```
photo ─▶ BLIP caption ─▶ dual-channel retrieval ─▶ fusion ─▶ confidence/margin gate ─▶ navigation reply ─▶ TTS
                          (structure + detail)     (§6)        (§7)                     (§5b)
```

### 5a. Two-phase localization (per session)

Each session tracks a `photo_count`. The **1st photo is a warm-up** that returns a
preset scene description (no retrieval). **From the 2nd photo on** the system runs the
full BLIP → retrieval → navigation pipeline. Enhanced FT retrieval auto-activates when
`provider="ft"` and `site_id="SCENE_A_MS"`.

### 5b. Navigation instructions

`generate_dynamic_navigation_response(...)` walks a fixed per-scene node sequence and
emits a turn + step-count instruction for the matched node, returning
`navigation_instruction`, `current_location`, `next_action`, and `retrieval_method`.
Instructions are bilingual; low-confidence localizations prompt a re-photo instead.

### 5c. Session state

`SESSIONS[session_id]` holds: `site_id`, `opening_provider`, `lang`,
`current_location`, `location_history`, `orientation_history`, `confidence_history`,
`last_update_time`, `photo_count`. Continuity is validated across photos
(`validate_location_continuity`, `track_orientation`).

---

## 6. Retrieval & fusion (current parameters)

Two channels are combined in `_enhanced_fusion` (inside the retriever in `app.py`):

- **Structure channel** — topology / node backbone. Source:
  `data/Sense_A_Finetuned.fixed.jsonl` (and `Sense_B_Finetuned.fixed.jsonl`).
- **Detail channel** — fine-grained landmark descriptions. Source:
  `data/Sense_A_MS.jsonl` / `data/Sense_B_Studio.jsonl`. Detail records align to
  structure nodes via the **`node_hint`** field.
- **Base/4o mode** uses `Sence_A_4o.fixed.jsonl` / `Sense_B_4o.fixed.jsonl`.
- **Discrimination data**: `Sense_A_Finetuned_enhanced.jsonl` adds per-node
  `cnl_index`, `index_terms`, and `negative` discriminators.

Fusion pipeline and **current** values:

| Mechanism | Current value | Purpose |
|-----------|---------------|---------|
| Channel weights | `α=0.35` (structure), `β=0.65` (detail), `γ=0.15` (continuity boost) | log-odds fusion |
| Fusion softmax temperature | `FUSION_TEMPERATURE=0.25` | sharpen final distribution (paper §3.4 Eq.3) |
| Negative-evidence penalty | `0.15` per hit (`apply_negatives`) | demote candidates whose `negative` terms appear in the query |
| `stable_query` filter | removes `MOVABLE` words, ×0.5 down-weights `LOW_TRUST` words | keep the structure channel on fixed landmarks, not movable junk (fixes the old `0.488/0.488` tie) |
| Conflict gating | logit-diff threshold `0.5` | when channels disagree strongly, re-weight / flag for clarification |
| Topology prior | +0.25 (1-hop neighbour), +0.10 (2-hop) | continuity across frames (needs `session_id`) |

> The fusion formula and channel weights were tuned across many iterations; see
> `CHANGELOG.md` for the full progression (linear → additive → multiplicative →
> log-odds; weights 0.45/0.55 → 0.40/0.60 → **0.35/0.65**).

---

## 7. Confidence, margin & metrics

- **Low-confidence rule (live)**: `low_conf = top1_score < 0.50 or margin < 0.10`
  (`LOWCONF_SCORE_TH=0.50`, `LOWCONF_MARGIN_TH=0.10`, aligned with paper §3.4).
  `margin = top1_score − top2_score`.
- **Softmax confidence calibration is currently OFF** (`ENABLE_SOFTMAX_CALIBRATION =
  False`; `SOFTMAX_TEMPERATURE=0.06` is retained but unused).
- **Metrics logged** under `backend/logs/`: `locate_log.csv` (top1/top2/margin,
  optional `gt_node_id`, `hit_top1/top2/hop1`, low-conf flags, timing),
  `latency_log.csv` (end-to-end photo→TTS), `clarification_log.csv`, `recovery_log.csv`,
  `similarity_distribution.csv`. Analysis helpers live in `backend/tools/`.
- **Discrimination metrics (new)**: every fusion records a discrimination event
  (top1/top2/margin/channel-agreement/neg-hits). Pull them via
  `GET /api/dg/metrics/discrimination/{session_id}` (`?include_events=true`, or
  `session_id=all` to aggregate). This feeds DG2 (see §8).

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

**Current wiring status (important):**

| Module | Status |
|--------|--------|
| `dg_evaluation_enhancement.py` (`DGEvaluationManager`, DG1–DG6 evaluators) | **Enabled** (imported with try/except fallback) |
| `accessibility_checker.py` (`AccessibilityChecker`) | **Enabled** |
| `indoor_gml_generator.py` (`IndoorGMLGenerator`) | **Enabled** |
| `enhanced_metrics_collector.py` | **Not wired** — `app.py` has a no-op stub; `/api/dg/metrics/*` collect/export endpoints will not persist data |
| `user_needs_validator.py` | **Not wired** — placeholder `None`; `/api/dg/user_needs/*` endpoints are inert |

`DGEvaluationManager.dg2_evaluator` now also records **retrieval discrimination** as an
objective DG2 signal (avg margin, tie rate, channel-agreement rate). `_analyze_dg2`
folds a `discrimination_score` into the DG2 report.

---

## 9. API endpoints

**Core**
- `GET  /health` · `GET /health/enhanced` — service + DG module status
- `POST /api/start` — open a session (`session_id`, `site_id`, `opening_provider`, `lang`)
- `POST /api/locate` — localize from an uploaded photo (multipart: `site_id`, `image`, `session_id`, `provider`, …)
- `POST /api/asr` — speech-to-text
- `POST /api/qa` — answer a spoken/typed question about the environment
- `GET  /api/session/location/{session_id}` · `GET /api/session/status/{session_id}`

**Metrics / experiment instrumentation**
- `POST /api/metrics/tts_start` — TTS-start timestamp (end-to-end latency)
- `POST /api/metrics/clarification_round` · `/clarification_end`
- `POST /api/metrics/error_recovery_start` · `/error_recovery_end`
- `POST /api/logging/set` · `GET /api/logging/status`

**DG optimization** (subject to §8 wiring status)
- `POST /api/dg/metrics/collect` · `GET /api/dg/metrics/export/{session_id}` · `/analytics/{session_id}` · `/stats` · `POST /api/dg/metrics/session/{session_id}/close`
- `GET  /api/dg/metrics/discrimination/{session_id}` — **discrimination stats (live)**
- `POST /api/dg/evaluation/record` · `GET /api/dg/evaluation/report/{session_id}`
- `POST /api/dg/accessibility/check` · `/voiceover`
- `POST /api/dg/indoor_gml/generate` · `/validate`
- `GET  /api/dg/user_needs/validation/{session_id}` · `POST /api/dg/user_needs/record` · `GET /api/dg/user_needs/matrix`

Full interactive list at `/docs`.

---

## 10. Configuration

Backend reads `backend/../.env`. Common variables (with current defaults):

```bash
ENABLE_DG_EVALUATION=true
ENABLE_ACCESSIBILITY_CHECKING=true
ENABLE_INDOOR_GML=true
LOWCONF_SCORE_TH=0.50
LOWCONF_MARGIN_TH=0.10
FUSION_TEMPERATURE=0.25
SOFTMAX_TEMPERATURE=0.06        # softmax calibration is force-disabled in code
LLM_MODEL=gpt-4o-mini           # OPENAI_API_KEY optional; reasoning falls back to presets
BLIP_MODEL_PATH=Salesforce/blip-image-captioning-large
BLIP_DEVICE=cpu
```

---

## 11. Testing

```bash
cd backend
python comprehensive_testing.py        # full suite
```

Tools under `backend/tools/` compute Top-1/Top-2/±1-hop accuracy, latency, and RQ3
(trust / clarification / recovery) metrics from the CSV logs.

### Experiment manager

`backend/tools/experiment_manager.py` is a small CLI that groups localization runs into
named sessions and auto-captures confidence/margin/Top-1 (and accuracy when a ground
truth is given) from every `/api/locate` call. Typical workflow:

```bash
# create a session, then paste the printed session ID into the frontend "Session" field
python tools/experiment_manager.py create --name alpha_tuning --description "tune alpha"
python tools/experiment_manager.py params  --session <id> --parameters '{"RANK_ALPHA_FT":0.7}'
python tools/experiment_manager.py note    --session <id> --note "margin up at 0.7"
python tools/experiment_manager.py show    --session <id>          # summary
python tools/experiment_manager.py export  --session <id> --output results.csv
python tools/metrics_top1.py                                       # accuracy stats
```

Sessions are stored as `backend/logs/session_*.json`; per-locate rows land in
`backend/logs/locate_log.csv`. Collect ≥10–20 samples per parameter setting and provide
ground-truth labels where possible.

---

## 12. Voice control (frontend)

- Navigation replies and answers are spoken via the Web Speech API.
- Pressing **Ask** cancels any in-progress speech (`speechSynthesis.cancel()`) before
  recording starts, avoiding TTS/recording overlap.
- Audio is captured with `MediaRecorder` (`getUserMedia({audio:true})`); works on
  Chrome/Edge/Safari/Firefox, desktop and mobile.

---

## License & contact

MIT License. Maintainer: **LarryYiGuo** · ucbqwg7@ucl.ac.uk
