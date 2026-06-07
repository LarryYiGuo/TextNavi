#!/usr/bin/env python3
"""
eval_image_knn.py — Plan E: image-image template matching with leave-one-out.

For each query photo, score it against EVERY OTHER labeled photo via SigLIP image
embedding cosine, then aggregate per node. Three modes:

  1nn      — predict the GT node of the single nearest other photo
  centroid — average all OTHER photos of each node into a centroid; predict the
             node whose centroid is closest to the query
  hybrid   — centroid when node has ≥1 other photo, else fall back to text
             template (clean textmap) for singletons

Usage:
  python tools/eval_image_knn.py 1nn
  python tools/eval_image_knn.py centroid
  python tools/eval_image_knn.py hybrid                  # default
"""
import argparse
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sweep_fusion import load_dataset
from eval_siglip import load_clean_descriptions

ROOT = Path(__file__).resolve().parents[1]


def evaluate(mode="hybrid", model_id="google/siglip-so400m-patch14-384"):
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor

    print(f"loading model: {model_id}")
    proc = AutoProcessor.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id)
    model.eval()

    items = load_dataset()
    print(f"loaded {len(items)} photos")

    # Compute image embeddings for ALL photos
    print("computing image embeddings for all photos...")
    t0 = time.time()
    photo_embeds = []
    for it in items:
        img = Image.open(it["file"]).convert("RGB")
        inp = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            e = model.get_image_features(**inp)
        e = e / e.norm(dim=-1, keepdim=True)
        photo_embeds.append(e.squeeze(0))
    photo_embeds = torch.stack(photo_embeds)
    print(f"  done in {time.time()-t0:.1f}s, shape={tuple(photo_embeds.shape)}")

    # Pre-compute text-template embeddings for hybrid fallback
    text_embeds = node_ids_list = None
    if mode == "hybrid":
        clean_descs = load_clean_descriptions()
        node_ids_list = sorted(clean_descs.keys())
        texts = [clean_descs[nid] for nid in node_ids_list]
        tin = proc(text=texts, return_tensors="pt", padding="max_length", truncation=True)
        with torch.no_grad():
            text_embeds = model.get_text_features(**tin)
        text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)

    # Index: node → list of photo indices
    node_to_idx = defaultdict(list)
    for i, it in enumerate(items):
        node_to_idx[it["gt_struct"]].append(i)
    all_nodes = sorted(node_to_idx.keys())

    # Leave-one-out evaluation
    hits = 0
    pred_counter = Counter()
    in_top5 = 0
    fallback_count = 0
    detail = []
    for q_idx, q in enumerate(items):
        q_emb = photo_embeds[q_idx]
        gt = q["gt_struct"]

        node_scores = {}
        for nid in all_nodes:
            other_idx = [i for i in node_to_idx[nid] if i != q_idx]
            if other_idx:
                if mode == "1nn":
                    other_emb = photo_embeds[other_idx]
                    sims = (q_emb @ other_emb.T)
                    node_scores[nid] = float(sims.max())
                else:
                    centroid = photo_embeds[other_idx].mean(dim=0)
                    centroid = centroid / centroid.norm()
                    node_scores[nid] = float(q_emb @ centroid)
            else:
                if mode == "hybrid":
                    ni = node_ids_list.index(nid) if nid in node_ids_list else None
                    if ni is not None:
                        node_scores[nid] = float(q_emb @ text_embeds[ni])
                    else:
                        node_scores[nid] = -1.0
                    fallback_count += 1
                else:
                    node_scores[nid] = -1.0

        ranked = sorted(node_scores.items(), key=lambda x: -x[1])
        pred = ranked[0][0]
        ok = (pred == gt)
        hits += int(ok)
        in_top5 += int(any(nid == gt for nid, _ in ranked[:5]))
        pred_counter[pred] += 1
        detail.append({
            "file": Path(q["file"]).name, "gt": gt, "pred": pred,
            "hit": ok, "top5": ranked[:5],
        })

    n = len(items)
    print(f"\n=== IMAGE-IMAGE KNN (mode={mode}, model={model_id}) ===")
    print(f"  n = {n}")
    print(f"  top1_acc = {hits/n:.3f}  ({hits}/{n})")
    print(f"  top5_acc = {in_top5/n:.3f}")
    if mode == "hybrid":
        print(f"  (text-template fallback used {fallback_count} times for singleton nodes)")

    print(f"\n  pred distribution: {dict(pred_counter.most_common(10))}")

    print(f"\n=== vs PRIOR WORK ===")
    print(f"  baseline (BLIP+fusion):                  top1=8.6%")
    print(f"  B (SigLIP-so400m + minimal text):        top1=37.8%   top5=56.8%")
    print(f"  B (SigLIP-so400m + clean text):          top1=35.1%   top5=73.0%")
    print(f"  E ({mode} image-template):              top1={hits/n*100:.1f}%   top5={in_top5/n*100:.1f}%")

    print(f"\n=== misses (first 8) ===")
    for d in [d for d in detail if not d["hit"]][:8]:
        in5 = any(nid == d['gt'] for nid, _ in d['top5'])
        print(f"  {d['file']:14s}  GT={d['gt']:42s}  pred={d['pred']:42s}  in_top5={in5}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", nargs="?", choices=["1nn", "centroid", "hybrid"], default="hybrid")
    p.add_argument("--model", default="google/siglip-so400m-patch14-384")
    args = p.parse_args()
    evaluate(args.mode, args.model)


if __name__ == "__main__":
    main()
