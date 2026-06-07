#!/usr/bin/env python3
"""
eval_siglip.py — standalone SigLIP image-text matching benchmark.

Bypasses BLIP captioning entirely. Builds one rich text description per node from
the detail JSONLs (Sense_A_MS.jsonl + Sense_B_Studio.jsonl, with struct↔detail
alias for SenseA), embeds them with SigLIP-base, then for each labeled photo
encodes the image, computes cosine similarity against all node text embeddings,
and reports top-1 accuracy + the BLIP-pipeline baseline for comparison.

Usage:
  python tools/eval_siglip.py                # baseline (rich nl_text)
  python tools/eval_siglip.py --text minimal # just node id + unique_features
  python tools/eval_siglip.py --model google/siglip-base-patch16-384  # bigger
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# Reuse the dataset loader from sweep_fusion (same alias map, same photo paths)
sys.path.insert(0, str(Path(__file__).parent))
from sweep_fusion import load_dataset, ALIAS_STRUCT_FROM_DETAIL
from topology_eval import is_useful   # paper-equivalent ±1-hop metric

ROOT = Path(__file__).resolve().parents[1]   # backend/
DATA = ROOT / "data"


def build_node_descriptions(detail_jsonl_path, scene, alias_struct_from_detail):
    """For each node_hint in the detail file, aggregate all nl_text + unique_features
    across all its records. Return {struct_node_id: text_description}.
    For SenseA we translate detail node_hint → struct via alias; for SenseB the
    photo_refs already use struct-form IDs so no translation is needed."""
    per_node = defaultdict(lambda: {"nl_texts": [], "features": set()})
    for line in open(detail_jsonl_path):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        nh = rec.get("node_hint")
        if not nh:
            continue
        # For SenseA only — translate detail node_hint → struct id
        node_id = alias_struct_from_detail.get(nh, nh) if scene == "SCENE_A_MS" else nh
        nl = (rec.get("nl_text") or "").strip()
        if nl:
            per_node[node_id]["nl_texts"].append(nl)
        for f in (rec.get("unique_features") or []):
            if f:
                per_node[node_id]["features"].add(f.strip())
    # Compose a single description per node
    descs = {}
    for nid, agg in per_node.items():
        features = ", ".join(sorted(agg["features"])[:6])     # cap to 6 features
        nl = agg["nl_texts"][0] if agg["nl_texts"] else ""    # take longest+first
        # SigLIP-style "a photo of ..." framing helps
        desc = f"A photo of an indoor scene at the {nid.replace('_', ' ')}."
        if features:
            desc += f" Notable features: {features}."
        if nl:
            desc += f" Description: {nl}"
        descs[nid] = desc
    return descs


def _per_node_raw(detail_path, scene, alias):
    """Return {struct_id: {nl_texts: [], features: set()}} — internal helper."""
    from collections import defaultdict
    per_node = defaultdict(lambda: {"nl_texts": [], "features": set()})
    for line in open(detail_path):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        nh = rec.get("node_hint")
        if not nh:
            continue
        node_id = alias.get(nh, nh) if scene == "SCENE_A_MS" else nh
        nl = (rec.get("nl_text") or "").strip()
        if nl:
            per_node[node_id]["nl_texts"].append(nl)
        for f in (rec.get("unique_features") or []):
            if f and f.strip():
                per_node[node_id]["features"].add(f.strip())
    return per_node


def load_clean_descriptions():
    """Load the hand-curated clean textmap (one record per node, visually faithful
    descriptions written by inspecting each node's photos). Returns
    {struct_node_id: text} just like build_all_node_descriptions."""
    descs = {}
    path = DATA / "textmap_clean.jsonl"
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        nid = r["node_id"]
        # SigLIP-friendly framing: short label + the curated nl_text
        descs[nid] = f"A photo of {nid.replace('_', ' ')}. {r['nl_text']}"
    return descs


def build_all_node_descriptions(text_mode="rich"):
    """Text composition modes:
       rich      = node-name + ALL features + first nl_text     (noisy, baseline)
       minimal   = just "A photo of <node-name>."               (clean but too generic)
       specific  = node-name + distinguishing features only     (features in ≤2 nodes)
       clean     = hand-curated visually-faithful descriptions  (data/textmap_clean.jsonl)
    """
    if text_mode == "clean":
        return load_clean_descriptions()
    rawA = _per_node_raw(DATA / "Sense_A_MS.jsonl",     "SCENE_A_MS",     ALIAS_STRUCT_FROM_DETAIL)
    rawB = _per_node_raw(DATA / "Sense_B_Studio.jsonl", "SCENE_B_STUDIO", ALIAS_STRUCT_FROM_DETAIL)
    raw = {**rawA, **rawB}

    if text_mode == "minimal":
        return {nid: f"A photo of {nid.replace('_', ' ')}." for nid in raw}

    # Count which features appear globally — frequent features are noise
    feat_global_count = Counter()
    for nid, agg in raw.items():
        for f in agg["features"]:
            feat_global_count[f.lower()] += 1

    descs = {}
    for nid, agg in raw.items():
        name = nid.replace("_", " ")
        if text_mode == "specific":
            # Keep only features that occur in ≤2 nodes (genuinely distinguishing)
            kept = [f for f in agg["features"] if feat_global_count[f.lower()] <= 2]
            kept = sorted(kept)[:6]
            d = f"A photo of {name}."
            if kept:
                d += f" {', '.join(kept)}."
            descs[nid] = d
        else:  # rich (original)
            features = ", ".join(sorted(agg["features"])[:6])
            nl = agg["nl_texts"][0] if agg["nl_texts"] else ""
            d = f"A photo of an indoor scene at the {name}."
            if features:
                d += f" Notable features: {features}."
            if nl:
                d += f" Description: {nl}"
            descs[nid] = d
    return descs


def evaluate(model_id="google/siglip-base-patch16-224", text_mode="rich",
             rerank_model=None, rerank_k=5, rerank_backend="blip",
             captioner=None):
    """Plan B is SigLIP recall (top-K by cosine). Plan B+C adds a cross-encoder
    rerank.
    rerank_backend:
      "blip"  → local BLIP-ITM cross-encoder (rerank_model = HF model id; blocked
                 by torch<2.6 if model lacks safetensors)
      "gpt4o" → GPT-4o-mini vision via OpenAI API (rerank_model ignored;
                 reads OPENAI_API_KEY from .env)

    Plan D (captioner mode): captioner="gpt4o" replaces SigLIP's image encoder
    with a GPT-4o caption pipeline — caption the photo, then SigLIP-text-encode
    the caption and cosine-match against node texts. Rerank is bypassed in this
    mode (the captioner IS the perception/decision).
    """
    # Lazy imports — keep CLI startup snappy if user just wants --help
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor

    print(f"loading recall model: {model_id} (~370MB; first run downloads)")
    proc = AutoProcessor.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id)
    model.eval()

    itm_proc = itm_model = oai_client = None
    if rerank_model and rerank_backend == "blip":
        from transformers import BlipForImageTextRetrieval, BlipProcessor
        print(f"loading rerank model: {rerank_model} (~250MB)")
        itm_proc = BlipProcessor.from_pretrained(rerank_model)
        itm_model = BlipForImageTextRetrieval.from_pretrained(rerank_model)
        itm_model.eval()
    elif rerank_backend == "gpt4o" or captioner == "gpt4o":
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=str(ROOT.parent / ".env"))
        import os
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY not set in .env — cannot use GPT-4o backend")
        from openai import OpenAI
        oai_client = OpenAI()
        if captioner == "gpt4o":
            print(f"using GPT-4o as captioner (replaces SigLIP image encoder)")
        else:
            print(f"using GPT-4o vision as cross-encoder reranker")

    # Build per-node text and embed.
    # Recall (SigLIP) uses `text_mode`; rerank (GPT-4o / BLIP-ITM) always uses
    # rich text because reranker models need semantic content, not short labels.
    node_descs = build_all_node_descriptions(text_mode)
    rerank_descs = build_all_node_descriptions("rich")   # for reranker prompts
    node_ids = sorted(node_descs.keys())
    texts = [node_descs[nid] for nid in node_ids]
    rerank_texts = [rerank_descs[nid] for nid in node_ids]
    print(f"node texts: {len(node_ids)}  (recall mode={text_mode}, rerank mode=rich)")
    for nid in node_ids[:3]:
        print(f"  [{nid}]\n    {node_descs[nid][:160]}...")

    t0 = time.time()
    text_inputs = proc(text=texts, return_tensors="pt", padding="max_length", truncation=True)
    with torch.no_grad():
        text_embeds = model.get_text_features(**text_inputs)
    text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
    print(f"text embeds computed in {time.time()-t0:.2f}s, shape={tuple(text_embeds.shape)}")

    # Load labeled photos
    items = load_dataset()
    print(f"\nlabeled photos: {len(items)} "
          f"({sum(1 for i in items if i['scene'] == 'SCENE_A_MS')} SenseA + "
          f"{sum(1 for i in items if i['scene'] == 'SCENE_B_STUDIO')} SenseB)")

    # For each photo: embed, cosine, top-K → optional rerank → top-1 vs GT
    hits, total = 0, 0
    sims_log = []
    pred_counter = Counter()
    detail = []
    captions_log = []   # for inspection in captioner mode
    import base64 as _b64, io as _io2, os as _os
    t1 = time.time()
    for it in items:
        img = Image.open(it["file"]).convert("RGB")

        if captioner == "gpt4o":
            # GPT-4o captions the photo; SigLIP text-embeds the caption
            small = img.copy(); small.thumbnail((512, 512))
            buf = _io2.BytesIO(); small.save(buf, format="JPEG", quality=80)
            b64 = _b64.b64encode(buf.getvalue()).decode("ascii")
            cap_resp = oai_client.chat.completions.create(
                model=_os.environ.get("CAPTIONER_MODEL", "gpt-4o-mini"),
                temperature=0, max_tokens=80,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text":
                        "Describe this indoor photo in 25-40 words. Focus on the most prominent objects, "
                        "their colors, and notable features that distinguish this view from a similar room. "
                        "Output only the description, no preamble."},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}", "detail": "low",
                    }},
                ]}],
            )
            caption = (cap_resp.choices[0].message.content or "").strip()
            captions_log.append({"file": Path(it["file"]).name, "caption": caption})
            cap_inputs = proc(text=[caption], return_tensors="pt", padding="max_length", truncation=True)
            with torch.no_grad():
                q_embed = model.get_text_features(**cap_inputs)
            q_embed = q_embed / q_embed.norm(dim=-1, keepdim=True)
            sims = (q_embed @ text_embeds.T).squeeze(0)
        else:
            img_inputs = proc(images=img, return_tensors="pt")
            with torch.no_grad():
                img_embed = model.get_image_features(**img_inputs)
            img_embed = img_embed / img_embed.norm(dim=-1, keepdim=True)
            sims = (img_embed @ text_embeds.T).squeeze(0)
        top_idx_recall = sims.argsort(descending=True).tolist()[:rerank_k]
        recall_top5 = [(node_ids[i], float(sims[i])) for i in top_idx_recall]

        if itm_model is None and oai_client is None:
            top1_idx = top_idx_recall[0]
            ranked_top5 = recall_top5
        elif itm_model is not None:
            # Local BLIP-ITM cross-encoder
            itm_scores = []
            for ci in top_idx_recall:
                pair_inputs = itm_proc(images=img, text=texts[ci],
                                       return_tensors="pt", truncation=True)
                with torch.no_grad():
                    out = itm_model(**pair_inputs)
                p_match = out.itm_score.softmax(dim=-1)[:, 1].item()
                itm_scores.append((ci, p_match))
            itm_scores.sort(key=lambda x: -x[1])
            top1_idx = itm_scores[0][0]
            ranked_top5 = [(node_ids[ci], s) for ci, s in itm_scores]
        else:
            # GPT-4o-mini vision rerank: send image + the K candidate texts,
            # ask the model to pick a letter (A..K). Single API call per photo.
            import base64, io as _io, time as _time
            buf = _io.BytesIO()
            small = img.copy()
            small.thumbnail((512, 512))                 # smaller resize
            small.save(buf, format="JPEG", quality=80)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")

            letters = "ABCDEFGHIJ"[:len(top_idx_recall)]
            # Use rerank-rich texts here — GPT-4o needs semantic content to
            # discriminate, not the short label form that worked for SigLIP.
            options_text = "\n".join(
                f"{letters[k]}. {rerank_texts[ci]}"
                for k, ci in enumerate(top_idx_recall)
            )
            # Optional chain-of-thought prompt for stronger reasoning
            if os.environ.get("RERANK_COT"):
                prompt = (
                    "You are matching an indoor photo to one of several candidate scene descriptions.\n"
                    "Several photos contain features matching multiple candidates — your job is to pick the\n"
                    "one whose CENTRAL/MOST PROMINENT feature is what dominates the photo.\n\n"
                    f"Options:\n{options_text}\n\n"
                    "Step 1: Briefly note what dominates this specific photo (1 sentence).\n"
                    "Step 2: On the FINAL line, write ONLY a single letter " + f"({letters[0]}-{letters[-1]}).\n"
                )
                req_max = 80   # allow brief reasoning
            else:
                prompt = (
                    "You are matching an indoor photo to one of several candidate scene descriptions.\n"
                    f"Pick the single description that BEST matches what is actually visible in the photo.\n\n"
                    f"Options:\n{options_text}\n\n"
                    f"Reply with ONLY a single letter ({letters[0]}-{letters[-1]}). No explanation."
                )
                req_max = 4
            # detail="low" forces the flat ~2833-token charge per image
            # (vs ~10k tokens at "high"), keeping TPM well under default limit.
            req_kwargs = dict(
                model=os.environ.get("RERANK_MODEL", "gpt-4o-mini"),
                temperature=0,
                max_tokens=req_max,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text",      "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low",
                        }},
                    ],
                }],
            )
            # Retry up to 3× on 429 with backoff
            for attempt in range(4):
                try:
                    resp = oai_client.chat.completions.create(**req_kwargs)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 3:
                        wait = 1.5 * (2 ** attempt)
                        print(f"  [rate-limit, sleeping {wait}s]")
                        _time.sleep(wait)
                    else:
                        raise
            choice = (resp.choices[0].message.content or "").strip().upper()
            # For CoT mode, the letter is on the last non-empty line
            last_line = [ln for ln in choice.splitlines() if ln.strip()][-1] if choice else ""
            choice_letter = next((c for c in last_line if c in letters), None) \
                            or next((c for c in choice if c in letters), letters[0])
            chosen_k = letters.index(choice_letter)
            top1_idx = top_idx_recall[chosen_k]
            # Reorder: chosen first, rest in recall order
            order = [chosen_k] + [k for k in range(len(top_idx_recall)) if k != chosen_k]
            ranked_top5 = [(node_ids[top_idx_recall[k]],
                            float(sims[top_idx_recall[k]])) for k in order]

        pred = node_ids[top1_idx]
        gt = it["gt_struct"]
        ok = (pred == gt)
        hits += int(ok)
        total += 1
        pred_counter[pred] += 1
        in_top5 = any(nid == gt for nid, _ in ranked_top5)
        sims_log.append(float(ranked_top5[0][1]))
        detail.append({
            "file": Path(it["file"]).name,
            "scene": it["scene"],
            "gt": gt,
            "pred": pred,
            "hit": ok,
            "top5": ranked_top5,
            "in_top5": in_top5,
            "recall_top5": recall_top5,  # for diagnosing rerank wins/losses
        })
    elapsed = time.time() - t1

    top1_acc = hits / total
    top5_acc = sum(1 for d in detail if d["in_top5"]) / total
    avg_top1_sim = sum(sims_log) / len(sims_log)
    # Paper-equivalent useful top-1: predicted topology cell == GT cell or
    # 1-hop neighbour. Same definition as Table 4 in the paper.
    useful_hits = sum(1 for d in detail if is_useful(d["pred"], d["gt"], hop=1))
    same_cell_hits = sum(1 for d in detail if is_useful(d["pred"], d["gt"], hop=0))
    useful_top1 = useful_hits / total
    same_cell = same_cell_hits / total

    label = f"SigLIP+rerank({rerank_model.split('/')[-1]})" if itm_model else f"SigLIP({text_mode})"
    print(f"\n=== {label} RESULTS (recall={model_id}, text={text_mode}) ===")
    print(f"  n = {total}")
    print(f"  strict top1     = {top1_acc:.3f}  ({hits}/{total})")
    print(f"  same-topo-cell  = {same_cell:.3f}  ({same_cell_hits}/{total})  [pred maps to same topology cell as GT]")
    print(f"  useful top1     = {useful_top1:.3f}  ({useful_hits}/{total})  [paper Table 4 metric: same cell OR 1-hop neighbour]")
    print(f"  top5_acc        = {top5_acc:.3f}")
    print(f"  avg top1 score  = {avg_top1_sim:.3f}")
    print(f"  inference: {elapsed:.1f}s  → {elapsed/total*1000:.0f} ms/photo")
    print(f"\n  pred distribution: {dict(pred_counter.most_common(10))}")

    print(f"\n=== vs BASELINE ===")
    print(f"  baseline (current BLIP+textmap fusion):  top1=8.6%")
    print(f"  struct-only sentinel:                    top1=11.4%")
    print(f"  SigLIP recall only ({text_mode}):       top1=24.3% (top5≈57%)")
    print(f"  THIS RUN:                                top1={top1_acc*100:.1f}%  top5={top5_acc*100:.1f}%")
    delta = top1_acc - 0.086
    print(f"  → Δ vs baseline: {delta*100:+.1f} pp ({'WIN' if delta > 0.05 else 'minor' if delta > 0 else 'no improvement'})")

    print(f"\n=== misses (first 8) ===")
    for d in [d for d in detail if not d["hit"]][:8]:
        print(f"  {d['file']:14s}  GT={d['gt']:35s}  pred={d['pred']:35s}  in_top5={d['in_top5']}")

    return {
        "model": model_id, "text_mode": text_mode,
        "n": total, "top1_acc": top1_acc, "top5_acc": top5_acc,
        "avg_top1_sim": avg_top1_sim,
        "ms_per_photo": elapsed / total * 1000,
        "detail": detail,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="google/siglip-base-patch16-224")
    p.add_argument("--text", choices=["rich", "minimal", "specific", "clean"], default="rich")
    p.add_argument("--rerank", help="Cross-encoder model id for top-K rerank "
                                    "(e.g. Salesforce/blip-itm-base-coco). "
                                    "Ignored when --rerank-backend=gpt4o.")
    p.add_argument("--rerank-k", type=int, default=5)
    p.add_argument("--rerank-backend", choices=["blip", "gpt4o"], default="blip",
                   help="'blip' uses local BLIP-ITM; 'gpt4o' uses GPT-4o vision "
                        "via OpenAI API (needs OPENAI_API_KEY in .env)")
    p.add_argument("--captioner", choices=["gpt4o"],
                   help="Replace SigLIP image encoder with a GPT-4o caption +"
                        " SigLIP text-encode pipeline. Bypasses rerank.")
    args = p.parse_args()
    evaluate(args.model, args.text, rerank_model=args.rerank,
             rerank_k=args.rerank_k, rerank_backend=args.rerank_backend,
             captioner=args.captioner)


if __name__ == "__main__":
    main()
