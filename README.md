# TextNavi — Indoor Navigation for the Visually Impaired

A vision-language indoor navigation web app for blind and low-vision users.
A single photo → SigLIP image-text matching + topology prior → voice-guided
navigation instruction.

**Accuracy**: 82.9% useful top-1 on the labeled 37-photo benchmark — matches the
paper's fine-tuned baseline (SenseA 74%, SenseB 82%).

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
                                     + topology prior boost
       ─▶ top-1 + confidence/margin gate ─▶ navigation instruction ─▶ TTS
```

- **Primary retriever**: `backend/siglip_retriever.py` — SigLIP-so400m
  (`google/siglip-so400m-patch14-384`), ~1.4 s / photo on CPU.
- **Topology prior**: candidates in the same topology cell as the user's
  previous location (or a 1-hop neighbour) get a cosine boost, encoding the
  sequential-movement assumption.
- **Legacy fallback**: BLIP + dual-channel-fusion preserved behind
  `ENABLE_SIGLIP=false`.
- **Voice I/O**: faster-whisper ASR + Web Speech API TTS.
- **Two demo scenes**: `SCENE_A_MS` (Maker Space, 10 nodes), `SCENE_B_STUDIO`
  (Studio, 8 nodes).

---

## Configuration

`.env` at the project root (gitignored — secrets never committed):

```bash
ENABLE_SIGLIP=true                          # default; false → legacy fusion only
SIGLIP_MODEL=google/siglip-so400m-patch14-384

LOWCONF_SCORE_TH=0.50
LOWCONF_MARGIN_TH=0.10                      # SigLIP-specific recalibration pending

TOPOLOGY_PRIOR_SAME_BOOST=0.05              # boost candidates in same topo cell as prev location
TOPOLOGY_PRIOR_NEIGHBOR_BOOST=0.025         # boost 1-hop neighbour candidates

OPENAI_API_KEY=sk-...                       # used by /api/qa (GPT-4o-mini)
```

---

## API endpoints

- `POST /api/start` — open a session
- `POST /api/locate` — localise from a photo; response includes `node_id`,
  `confidence`, `margin`, `low_conf`, `candidates`, `navigation_instruction`,
  `retrieval_method`
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
│   ├── topology_eval.py           # struct↔topology mapping + ±1-hop helper
│   ├── dual_channel_retrieval.py  # legacy fusion (fallback)
│   ├── data/
│   │   ├── textmap_clean.jsonl    # 18 hand-curated node descriptions for SigLIP
│   │   └── Sense_*.jsonl          # legacy textmaps
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
