# TextNavi — Indoor Navigation for the Visually Impaired

A vision-language indoor navigation web app for blind and low-vision users.
A single photo → SigLIP image-text matching → goal-aware turn-by-turn voice
instruction routed on the scene graph.

**Accuracy**: 91.9% useful top-1 on the labeled 37-photo benchmark (verified
both offline and via the live API) — above the paper's fine-tuned baseline
(SenseA 74%, SenseB 82%).

---

## Quick start

```bash
# 1. Install
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Backend (port 8001; first run downloads SigLIP-so400m ~870 MB)
cd ../backend && uvicorn app:app --reload --host 0.0.0.0 --port 8001

# 3. Frontend (HTTPS, port 5173) in a second terminal
cd ../frontend && npm run dev
```

Open `https://localhost:5173/` and accept the mkcert self-signed cert.

---

## How it works

```
photo ─▶ SigLIP-so400m image embed ─▶ cosine vs 18 node text embeds
                                       (data/textmap_clean.jsonl)
       ─▶ top-1 + confidence/margin + teleport gate
       ─▶ nav_router: BFS on the struct graph (action hints + step counts)
       ─▶ turn-by-turn instruction ─▶ TTS
```

- **Retriever**: `backend/siglip_retriever.py` — SigLIP-so400m
  (`google/siglip-so400m-patch14-384`), ~1.4 s / photo on CPU. Node texts are
  kept within SigLIP's 64-token window (the discriminative details must fit).
- **Goal-aware navigation**: set a destination via `/api/set_goal` (exact node
  id or free-form text matched with the same SigLIP encoder); `nav_router.py`
  routes on the struct-level scene graph (metric coordinates + directional
  action hints from the paper's structure files) and speaks instructions like
  *"Left of printer bay, desk printer, about 3 steps."* An atrium bridge edge
  makes cross-scene goals routable. English and Chinese output.
- **Safety gates**: low-confidence and "teleport" (physically implausible
  jump between consecutive photos) both ask for a retake instead of routing
  on a suspect position.
- **Legacy fallback**: BLIP + dual-channel-fusion preserved behind
  `ENABLE_SIGLIP=false`.
- **Voice I/O**: faster-whisper ASR + Web Speech API TTS.
- **Two demo scenes**: `SCENE_A_MS` (Maker Space, 10 nodes), `SCENE_B_STUDIO`
  (Studio, 8 nodes).
- **Two graph layers, deliberately decoupled**: the coarse topology-cell graph
  defines the paper's *useful top-1* metric (frozen for comparability); the
  fine struct graph drives navigation.

---

## Configuration

`.env` at the project root (gitignored — secrets never committed):

```bash
ENABLE_SIGLIP=true                          # default; false → legacy fusion only
SIGLIP_MODEL=google/siglip-so400m-patch14-384

LOWCONF_SCORE_TH=0.45                       # recalibrated for SigLIP: old 0.50/0.10
LOWCONF_MARGIN_TH=0.01                      # (legacy-fusion era) flagged 78% of photos
                                            # as low_conf; margin is a weak error
                                            # signal here — teleport detection is the
                                            # primary safety net

TOPOLOGY_PRIOR_SAME_BOOST=0                 # prior OFF by default: raw SigLIP (91.9%)
TOPOLOGY_PRIOR_NEIGHBOR_BOOST=0             # now outperforms prior-assisted (86.5%)

OPENAI_API_KEY=sk-...                       # used by /api/qa (GPT-4o-mini)
```

---

## API endpoints

- `POST /api/start` — open a session (optional `goal_node_id`)
- `POST /api/set_goal` — set/change the destination: exact `goal_node_id` or
  free-form `goal_text` (matched against the 18 node descriptions via SigLIP)
- `POST /api/locate` — localise from a photo; response includes `node_id`,
  `confidence`, `margin`, `low_conf`, `candidates`, `navigation_instruction`,
  `retrieval_method`, and `nav` (route status, path, hops, cross_scene)
- `POST /api/asr` — speech-to-text
- `POST /api/qa` — natural-language Q&A about the scene (needs `OPENAI_API_KEY`)
- `GET /api/session/{location,status}/{session_id}`
- `GET /health` · `GET /health/enhanced`

Full interactive list at `/docs`.

---

## Repository layout

```
TextNavi/
├── backend/
│   ├── app.py                     # FastAPI app + all endpoints
│   ├── siglip_retriever.py        # SigLIP-so400m image→text retriever
│   ├── nav_router.py              # struct-graph routing + turn-by-turn instructions
│   ├── topology_eval.py           # eval layer: struct↔cell mapping + ±1-hop metric
│   ├── dual_channel_retrieval.py  # legacy fusion (fallback)
│   ├── data/
│   │   ├── textmap_clean.jsonl    # 18 hand-curated node descriptions (en+zh labels)
│   │   └── Sense_*_Finetuned.fixed.jsonl  # struct graphs: coords + action hints
│   └── tools/
│       └── eval_siglip.py         # accuracy benchmark (paper Table 4 metric)
├── frontend/                       # React + Vite
├── .env                            # secrets (gitignored)
└── README.md
```

---

## Testing

```bash
cd backend
python tools/eval_siglip.py --text clean --model google/siglip-so400m-patch14-384
```

Reports strict / same-cell / **useful top-1** (paper Table 4 metric) on the 37
labeled SENSE_A/B photos.

---

## License

MIT. Maintainer: **LarryYiGuo** · ucbqwg7@ucl.ac.uk
