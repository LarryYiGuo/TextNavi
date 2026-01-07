import json, os, pathlib, numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss  # type: ignore
    USE_FAISS = True
except Exception:
    USE_FAISS = False

DATA_DIR   = pathlib.Path(__file__).resolve().parent / "data"
MODEL_DIR  = pathlib.Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

ST_MODEL = None

def load_jsonl_records(file_path: pathlib.Path) -> list:
    """Load all records from a JSONL file"""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num} in {file_path}: {e}")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return records

def extract_structured_text_from_finetuned(record: dict) -> str:
    """Extract structured information from finetuned record"""
    input_data = record.get("input", {})
    topo = input_data.get("topology", {})
    retv = input_data.get("retrieval", {})
    
    parts = []
    
    # Extract objects from landmarks and nodes
    objects = set()
    for landmark in topo.get("landmarks", []):
        if "name" in landmark:
            name_parts = landmark["name"].split()
            if name_parts:
                objects.add(name_parts[0].lower())  # First word as object
    
    for node in topo.get("nodes", []):
        if "name" in node:
            name_parts = node["name"].split()
            if name_parts:
                objects.add(name_parts[0].lower())
    
    if objects:
        parts.append(f"objects={' '.join(sorted(objects))}")
    
    # Extract spatial relations from edges
    relations = []
    for edge in topo.get("edges", []):
        if "turn_hint" in edge and "step_count" in edge:
            relations.append(f"{edge['turn_hint']}-{edge['step_count']}-steps")
        if "hazards" in edge:
            for hazard in edge["hazards"]:
                relations.append(f"hazard-{hazard}")
    
    if relations:
        parts.append(f"relations={' '.join(relations)}")
    
    # Extract bearing and distance info
    bearing_info = []
    for edge in topo.get("edges", []):
        if "turn_hint" in edge:
            bearing_info.append(f"bearing-{edge['turn_hint']}")
        if "step_count" in edge:
            bearing_info.append(f"distance-{edge['step_count']}-steps")
    
    if bearing_info:
        parts.append(f"spatial={' '.join(bearing_info)}")
    
    # Add keywords from retrieval hints
    if retv.get("keywords"):
        parts.append(f"keywords={' '.join(retv['keywords'])}")
    
    return "; ".join(parts) if parts else "no_structured_info"

def build_dual_channel_index():
    """Build dual-channel index from all 4 jsonl files"""
    print("🔍 Building dual-channel index from all data files...")
    
    # Define all data files
    data_files = [
        ("Sense_A_4o", "Sence_A_4o.fixed.jsonl"),
        ("Sense_A_FT", "Sense_A_Finetuned.fixed.jsonl"), 
        ("Sense_B_4o", "Sense_B_4o.fixed.jsonl"),
        ("Sense_B_FT", "Sense_B_Finetuned.fixed.jsonl")
    ]
    
    # Load and assemble all records
    records = []  # Each record: {id, scene_id, provider, nl_text, struct_text}
    
    for provider, filename in data_files:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            print(f"⚠ Warning: {filename} not found, skipping...")
            continue
            
        print(f"📖 Loading {filename}...")
        file_records = load_jsonl_records(file_path)
        
        for i, record in enumerate(file_records):
            # Generate unique ID
            record_id = f"{provider}_{i}"
            
            # Extract scene_id
            scene_id = record.get("input", {}).get("site_id", "unknown")
            
            # Extract natural language text
            nl_text = record.get("output", "").strip()
            if not nl_text:
                print(f"⚠ Warning: No output text in {record_id}")
                continue
            
            # Extract structured text (only for finetuned records)
            if "FT" in provider:
                struct_text = extract_structured_text_from_finetuned(record)
            else:
                struct_text = ""  # 4o records have no structured input
            
            # Create record entry
            record_entry = {
                "id": record_id,
                "scene_id": scene_id,
                "provider": "ft" if "FT" in provider else "base",
                "nl_text": nl_text,
                "struct_text": struct_text,
                "source_file": filename
            }
            
            records.append(record_entry)
            print(f"  ✓ {record_id}: {scene_id} ({len(nl_text)} chars, struct: {len(struct_text)} chars)")
    
    print(f"\n📊 Total records loaded: {len(records)}")
    
    # Count by provider and scene
    provider_counts = {}
    scene_counts = {}
    for record in records:
        provider_counts[record["provider"]] = provider_counts.get(record["provider"], 0) + 1
        scene_counts[record["scene_id"]] = scene_counts.get(record["scene_id"], 0) + 1
    
    print("📈 Record distribution:")
    for provider, count in provider_counts.items():
        print(f"  {provider}: {count} records")
    for scene, count in scene_counts.items():
        print(f"  {scene}: {count} records")
    
    # Initialize sentence transformer model
    global ST_MODEL
    if ST_MODEL is None:
        print("\n🤖 Loading SentenceTransformer model...")
        ST_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✓ Model loaded successfully")
    
    # Compute dual-channel vectors
    print("\n🧮 Computing dual-channel embeddings...")
    
    # Natural language vectors
    nl_texts = [r["nl_text"] for r in records]
    nl_vecs = ST_MODEL.encode(nl_texts, normalize_embeddings=True, convert_to_numpy=True)
    print(f"✓ NL vectors: {nl_vecs.shape}")
    
    # Structured vectors (for records without struct_text, use empty string)
    struct_inputs = [r["struct_text"] if r["struct_text"] else "" for r in records]
    struct_vecs = ST_MODEL.encode(struct_inputs, normalize_embeddings=True, convert_to_numpy=True)
    print(f"✓ Struct vectors: {struct_vecs.shape}")
    
    # Save dual-channel index
    output_npz = MODEL_DIR / "index_dual.npz"
    output_meta = MODEL_DIR / "index_meta.json"
    
    print(f"\n💾 Saving dual-channel index...")
    np.savez_compressed(
        output_npz,
        nl_vecs=nl_vecs.astype(np.float32),
        struct_vecs=struct_vecs.astype(np.float32)
    )
    print(f"✓ Vectors saved: {output_npz}")
    
    # Save metadata
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✓ Metadata saved: {output_meta}")
    
    # Create FAISS indices if available
    if USE_FAISS:
        print("\n🔍 Creating FAISS indices...")
        
        # NL index
        nl_index_path = MODEL_DIR / "index_dual.nl.faiss"
        dim = nl_vecs.shape[1]
        nl_index = faiss.IndexFlatIP(dim)
        nl_index.add(nl_vecs.astype(np.float32))
        faiss.write_index(nl_index, str(nl_index_path))
        print(f"✓ NL FAISS index: {nl_index_path}")
        
        # Struct index
        struct_index_path = MODEL_DIR / "index_dual.struct.faiss"
        struct_index = faiss.IndexFlatIP(dim)
        struct_index.add(struct_vecs.astype(np.float32))
        faiss.write_index(struct_index, str(struct_index_path))
        print(f"✓ Struct FAISS index: {struct_index_path}")
    else:
        print("\n⚠ FAISS not available, will use sklearn at runtime")
    
    print(f"\n🎉 Dual-channel index complete!")
    print(f"📁 Output files:")
    print(f"  - {output_npz}")
    print(f"  - {output_meta}")
    if USE_FAISS:
        print(f"  - {MODEL_DIR}/index_dual.nl.faiss")
        print(f"  - {MODEL_DIR}/index_dual.struct.faiss")
    
    return records

def main():
    """Main function to build dual-channel index"""
    print("🚀 Dual-Channel Index Builder")
    print("=" * 50)
    
    try:
        records = build_dual_channel_index()
        print(f"\n✅ Successfully built index with {len(records)} records")
        
        # Print sample records for verification
        print(f"\n📋 Sample records:")
        for i, record in enumerate(records[:3]):
            print(f"  {i+1}. {record['id']}: {record['scene_id']} ({record['provider']})")
            print(f"     NL: {record['nl_text'][:80]}...")
            if record['struct_text']:
                print(f"     Struct: {record['struct_text']}")
            print()
            
    except Exception as e:
        print(f"\n❌ Error building index: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())