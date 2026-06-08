#!/usr/bin/env python3
"""
eval_merged.py — Plan F: re-evaluate B and E under merged node taxonomies.

Premise: if multiple struct IDs map to visually-indistinguishable scenes
(7 of 10 SenseA nodes are 3D-printer workshop angles), merging them into
"zones" should lift top-1 accuracy by removing forced confusion. The
trade-off is semantic granularity — what the navigation system can say.

Two taxonomies:
  moderate     18 → 11 zones (merge most-confused printer benches only)
  aggressive   18 → 7  zones (zone-level: entrance / workshop / studio-desks
                              / studio-tv / studio-window / chair-yline / trash-bin)

For each taxonomy, runs both:
  - B: SigLIP-so400m + (merged) clean text templates
  - E: SigLIP-so400m image-image centroid (more photos per zone = better KNN)
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sweep_fusion import load_dataset
from eval_siglip import load_clean_descriptions

ROOT = Path(__file__).resolve().parents[1]

TAXONOMY_MODERATE = {
    # SenseA
    "poi01_entrance_glass_door":     "ms_entrance",
    "poi02_green_trash_bin":         "ms_trash_corner",
    "poi03_black_drawer_cabinet":    "ms_drawer_cabinet",
    "poi04_wall_3d_printers":        "ms_printer_bench",
    "poi05_desk_3d_printer":         "ms_printer_bench",
    "poi06_small_open_3d_printer":   "ms_printer_bench",
    "poi07_cardboard_boxes":         "ms_storage_corner",
    "poi08_to_atrium":               "ms_storage_corner",
    "poi09_chair_on_yline":          "ms_chair_on_yline",  # 🔧 renamed from poi09_qr_bookshelf for visual accuracy
    "poi10_metal_display_cabinet":   "ms_storage_corner",
    # SenseB — keep all (8 distinct enough)
    "poi11_di_hub_glass_box":          "poi11_di_hub_glass_box",
    "poi12_wall_side_workbench":       "poi12_wall_side_workbench",
    "poi14_main_work_table":           "poi14_main_work_table",
    "poi15_floor_to_ceiling_windows":  "poi15_floor_to_ceiling_windows",
    "poi16_green_sofa_side_table":     "poi16_green_sofa_side_table",
    "poi18_large_display_screen":      "poi18_large_display_screen",
    "poi19_purple_chair_filming_table":"poi19_purple_chair_filming_table",
    "poi20_two_tone_sofa_zone":        "poi20_two_tone_sofa_zone",
}

TAXONOMY_AGGRESSIVE = {
    # SenseA — collapse most printer-area nodes
    "poi01_entrance_glass_door":     "ms_entrance",
    "poi02_green_trash_bin":         "ms_entrance",
    "poi03_black_drawer_cabinet":    "ms_workshop",
    "poi04_wall_3d_printers":        "ms_workshop",
    "poi05_desk_3d_printer":         "ms_workshop",
    "poi06_small_open_3d_printer":   "ms_workshop",
    "poi07_cardboard_boxes":         "ms_workshop",
    "poi08_to_atrium":               "ms_workshop",
    "poi09_chair_on_yline":          "ms_chair_on_yline",  # 🔧 renamed from poi09_qr_bookshelf for visual accuracy
    "poi10_metal_display_cabinet":   "ms_workshop",
    # SenseB — group by zone
    "poi11_di_hub_glass_box":          "studio_desks",
    "poi12_wall_side_workbench":       "studio_desks",
    "poi14_main_work_table":           "studio_desks",
    "poi15_floor_to_ceiling_windows":  "studio_window",
    "poi16_green_sofa_side_table":     "studio_window",
    "poi18_large_display_screen":      "studio_tv_lounge",
    "poi19_purple_chair_filming_table":"studio_tv_lounge",
    "poi20_two_tone_sofa_zone":        "studio_tv_lounge",
}

# Generate descriptions per merged zone (concatenate constituent descriptions briefly)
ZONE_DESCRIPTIONS = {
    "ms_entrance":         "Maker Space entrance area. Brown wood-framed double glass doors with floor-to-ceiling glass; reflected 'Global Disability Innovation Hub' lettering; a black bin with bright green ring lid in the adjacent corner alcove; a wooden bookshelf with brochures on the right of the doors; red fire alarm pull station and emergency signs.",
    "ms_trash_corner":     "A black trash bin with a distinctive bright green ring lid in a corner alcove; emergency signs ('Automatic door / Do not pull') and a red fire alarm pull station on the plywood wall above; a blue QR-code Lab Equipment Booking poster on the side wall; glass partition handrail.",
    "ms_drawer_cabinet":   "A workbench with a tall wall-mounted cabinet of dozens of small black labeled drawers for component storage; clear-enclosure 3D printers on the adjacent bench; a yellow flammable-storage cabinet between them.",
    "ms_printer_bench":    "A 3D-printer workbench scene. Multiple clear-acrylic Ultimaker or enclosed printers (dark/black housings) lined up on wooden benches with filament spools and reels; printer banks against beige plywood walls; tools and 3D-printed parts visible on the worktop.",
    "ms_storage_corner":   "A 3D printer workshop area with stacked brown 'Just Hoods' cardboard boxes on the floor; tall black enclosed 3D printer assemblies and smaller white desks with printers and oscilloscopes; clutter of packaging and parts; beige plywood walls.",
    "ms_chair_on_yline":   "A black office chair with five-star wheeled base sits in the middle of the floor on a bright yellow guide line; behind it a wall of small black labeled component drawers; yellow flammable-storage cabinet on left; glass partition handrail with green-lid trash bin on right.",
    "ms_workshop":         "Maker Space workshop interior with 3D printers (clear-enclosure Ultimakers, dark enclosed printer cabinets, filament spools), worktables with tools and 3D-printed test parts, cardboard packing boxes on the floor, component drawer walls, and yellow safety cabinets. Beige plywood walls and exposed ceiling.",
    "studio_desks":        "An open studio with two long parallel work-desks, multiple computer monitors and laptops, people seated at workstations. A tall glass display case labeled 'Global Disability Innovation Hub' with assistive-device prototypes; orange wheeled shelving racks; exposed ceiling ducts and fluorescent strip lights; purple and olive-green chairs visible.",
    "studio_window":       "Studio area in front of floor-to-ceiling sliding glass windows with translucent roller blinds half-drawn; outdoor trees visible through the glass; olive-green and teal bean-shaped sofas with small black side tables on stands; tall grey storage cabinet and metal shelving in background.",
    "studio_tv_lounge":    "Studio TV/lounge area. A large flat TV monitor on a mobile floor stand displaying a landscape image. Olive bean-shaped sofas and a two-tone olive+orange couch nearby; purple high-back chair next to a green armchair with orange arm; black height-adjustable filming/side tables with laptops; cardboard boxes against the back wall.",
    # SenseB unmerged nodes (for moderate taxonomy) reuse clean descriptions
}


def remap_items_to_zones(items, taxonomy):
    """Replace each item's gt_struct with its zone label."""
    out = []
    for it in items:
        zone = taxonomy.get(it["gt_struct"], it["gt_struct"])
        out.append({**it, "gt_zone": zone})
    return out


def build_zone_texts(taxonomy):
    """For each zone, get its description (from ZONE_DESCRIPTIONS if defined,
    else fall back to the underlying node's clean description)."""
    clean = load_clean_descriptions()
    zones = sorted(set(taxonomy.values()))
    texts = {}
    for z in zones:
        if z in ZONE_DESCRIPTIONS:
            texts[z] = f"A photo of {z.replace('_', ' ')}. {ZONE_DESCRIPTIONS[z]}"
        elif z in clean:
            texts[z] = clean[z]
        else:
            texts[z] = f"A photo of {z.replace('_', ' ')}."
    return texts


def eval_text_template(items, taxonomy, model_id, proc, model, torch):
    zone_texts = build_zone_texts(taxonomy)
    zones = sorted(zone_texts.keys())
    texts = [zone_texts[z] for z in zones]
    tin = proc(text=texts, return_tensors="pt", padding="max_length", truncation=True)
    with torch.no_grad():
        text_embeds = model.get_text_features(**tin)
    text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)

    from PIL import Image
    hits = in_top5 = 0
    pred_counter = Counter()
    for it in items:
        img = Image.open(it["file"]).convert("RGB")
        inp = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            ie = model.get_image_features(**inp)
        ie = ie / ie.norm(dim=-1, keepdim=True)
        sims = (ie @ text_embeds.T).squeeze(0)
        ranked = sims.argsort(descending=True).tolist()
        pred = zones[ranked[0]]
        gt = it["gt_zone"]
        hits += int(pred == gt)
        in_top5 += int(any(zones[i] == gt for i in ranked[:5]))
        pred_counter[pred] += 1
    n = len(items)
    return {"top1": hits / n, "top5": in_top5 / n, "hits": hits, "n": n,
            "pred_dist": dict(pred_counter.most_common(8))}


def eval_image_centroid(items, taxonomy, model_id, proc, model, torch):
    """For each query, compute centroid of OTHER zone-photos as template."""
    from PIL import Image
    photo_embeds = []
    for it in items:
        img = Image.open(it["file"]).convert("RGB")
        inp = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            e = model.get_image_features(**inp)
        e = e / e.norm(dim=-1, keepdim=True)
        photo_embeds.append(e.squeeze(0))
    photo_embeds = torch.stack(photo_embeds)
    # zone → photo indices
    zone_to_idx = defaultdict(list)
    for i, it in enumerate(items):
        zone_to_idx[it["gt_zone"]].append(i)
    zones = sorted(zone_to_idx.keys())
    hits = in_top5 = 0
    pred_counter = Counter()
    for q_idx, it in enumerate(items):
        q_emb = photo_embeds[q_idx]
        gt = it["gt_zone"]
        scores = {}
        for z in zones:
            other = [i for i in zone_to_idx[z] if i != q_idx]
            if not other:
                scores[z] = -1
                continue
            cent = photo_embeds[other].mean(dim=0)
            cent = cent / cent.norm()
            scores[z] = float(q_emb @ cent)
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        pred = ranked[0][0]
        hits += int(pred == gt)
        in_top5 += int(any(z == gt for z, _ in ranked[:5]))
        pred_counter[pred] += 1
    n = len(items)
    return {"top1": hits / n, "top5": in_top5 / n, "hits": hits, "n": n,
            "pred_dist": dict(pred_counter.most_common(8))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="google/siglip-so400m-patch14-384")
    args = p.parse_args()

    import torch
    from transformers import AutoModel, AutoProcessor
    print(f"loading model: {args.model}")
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model); model.eval()

    items = load_dataset()
    print(f"loaded {len(items)} photos\n")

    for tname, taxonomy in [("moderate (18→11)", TAXONOMY_MODERATE),
                            ("aggressive (18→7)", TAXONOMY_AGGRESSIVE)]:
        mapped = remap_items_to_zones(items, taxonomy)
        n_zones = len(set(taxonomy.values()))
        photos_per_zone = Counter(it["gt_zone"] for it in mapped)

        print(f"=== TAXONOMY: {tname} ===")
        print(f"  zones: {n_zones}  (random baseline = {100/n_zones:.1f}%)")
        print(f"  photos per zone (top 5): {dict(photos_per_zone.most_common(5))}")
        t = time.time()
        b = eval_text_template(mapped, taxonomy, args.model, proc, model, torch)
        print(f"  B (text template):   top1={b['top1']*100:5.1f}%  top5={b['top5']*100:5.1f}%  ({b['hits']}/{b['n']})  [{time.time()-t:.0f}s]")
        print(f"     pred_dist: {b['pred_dist']}")
        t = time.time()
        e = eval_image_centroid(mapped, taxonomy, args.model, proc, model, torch)
        print(f"  E (image centroid):  top1={e['top1']*100:5.1f}%  top5={e['top5']*100:5.1f}%  ({e['hits']}/{e['n']})  [{time.time()-t:.0f}s]")
        print(f"     pred_dist: {e['pred_dist']}")
        print()


if __name__ == "__main__":
    main()
