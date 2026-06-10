"""siglip_retriever.py — production SigLIP image→text-template retriever.

Replaces the legacy BLIP-caption + dual-channel-fusion pipeline with a single
SigLIP forward pass: image encoder → cosine vs pre-computed node text embeddings.

On the labeled 37-photo benchmark with the hand-curated `data/textmap_clean.jsonl`
and the truncation-aware text template below, this achieves **useful top-1 =
91.9%** (paper Table 4 metric: predicted struct node maps to the same topology
cell as GT, or is a 1-hop neighbour; scene-filtered candidate pool, matching
production) — well above the paper's fine-tuned baseline (74% SenseA, 82%
SenseB). Verified identical offline (tools/eval_siglip.py --text clean) and
live (/api/locate production protocol).

Model: `google/siglip-so400m-patch14-384` (~870MB, ~1.4 s/photo CPU). Loaded
once at module import; text embeddings precomputed once.
"""
import json
import os
from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from transformers import AutoModel, AutoProcessor

ROOT = Path(__file__).resolve().parent           # backend/
TEXTMAP_CLEAN = ROOT / "data" / "textmap_clean.jsonl"
MODEL_ID = os.getenv("SIGLIP_MODEL", "google/siglip-so400m-patch14-384")


class SigLipRetriever:
    """Lazy-loading singleton-style retriever. Call `predict(image_bytes)`."""

    def __init__(self, model_id: str = MODEL_ID, textmap_path: Path = TEXTMAP_CLEAN):
        print(f"🔧 Loading SigLIP model: {model_id}")
        self.proc = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id)
        self.model.eval()
        self.model_id = model_id

        # Load clean textmap (one record per struct node)
        records = []
        for line in open(textmap_path):
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
        self.node_ids = [r["node_id"] for r in records]
        # nl_text only — no "A photo of {node_id}." prefix. SigLIP's tokenizer
        # hard-truncates at 64 tokens (model_max_length), and the prefix wasted
        # ~10 of them on a noisy slug ("poi09 chair on yline"), pushing the
        # discriminative tail of every hand-written description out of the
        # window. Dropping it: useful top-1 81.1% -> 91.9% (scene-filtered,
        # 37-photo benchmark, no topology prior).
        self.node_texts = [r["nl_text"] for r in records]
        # Scene assignment per node, for site_id filtering at query time
        self.node_scenes = [r.get("scene", "") for r in records]
        print(f"   nodes loaded: {len(self.node_ids)}")

        # Pre-compute text embeddings ONCE
        with torch.no_grad():
            tin = self.proc(text=self.node_texts, return_tensors="pt",
                            padding="max_length", truncation=True)
            text_embeds = self.model.get_text_features(**tin)
            text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
        self.text_embeds = text_embeds
        print(f"   text embeddings: {tuple(text_embeds.shape)}")

    def predict(self, image_bytes: bytes, top_k: int = 5,
                site_id: Optional[str] = None) -> list:
        """Return [{node_id, score (cosine), confidence (0..1), rank}, …] sorted
        by score descending. `site_id` ("SCENE_A_MS" / "SCENE_B_STUDIO") restricts
        the candidate pool to nodes in that scene."""
        import io
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with torch.no_grad():
            inp = self.proc(images=img, return_tensors="pt")
            ie = self.model.get_image_features(**inp)
            ie = ie / ie.norm(dim=-1, keepdim=True)
            sims = (ie @ self.text_embeds.T).squeeze(0)
        cosines = sims.tolist()

        # Filter to the requested scene if specified
        eligible = [(i, c) for i, c in enumerate(cosines)
                    if not site_id or self.node_scenes[i] == site_id]
        if not eligible:
            # Fail loud: returning [] made the caller's `results[0]` raise an
            # IndexError that was easy to swallow upstream. An unknown site_id
            # is a caller bug, not a retrieval miss.
            raise ValueError(
                f"No textmap nodes match site_id={site_id!r}; "
                f"known scenes: {sorted(set(self.node_scenes))}")
        eligible.sort(key=lambda x: -x[1])
        top = eligible[:top_k]

        # Map cosine ([-1, 1] but typically 0.05-0.30 here) to a friendly
        # 0..1 confidence: sigmoid centered at 0.15 with steep slope.
        # Calibrated against the labeled set: matches with cosine ≥ 0.15 are
        # typically the right topology cell, < 0.10 is uncertain.
        import math
        def to_conf(c):
            return max(0.0, min(1.0, 1.0 / (1.0 + math.exp(-12.0 * (c - 0.15)))))

        return [
            {
                "node_id":    self.node_ids[i],
                "score":      float(c),
                "confidence": to_conf(c),
                "rank":       r,
            }
            for r, (i, c) in enumerate(top)
        ]


# Module-level singleton — loaded eagerly so the cost (~5–10 s) shows in
# startup, not in the first request.
_RETRIEVER: Optional[SigLipRetriever] = None


def get_retriever() -> Optional[SigLipRetriever]:
    """Lazily construct (or return cached) the retriever. Returns None on
    construction failure (e.g. model download offline)."""
    global _RETRIEVER
    if _RETRIEVER is None:
        try:
            _RETRIEVER = SigLipRetriever()
            print("✅ SigLIP retriever initialised")
        except Exception as e:
            print(f"⚠️ SigLIP retriever init failed: {e}")
            _RETRIEVER = False  # sentinel: tried-and-failed, don't retry
    return _RETRIEVER if _RETRIEVER else None
