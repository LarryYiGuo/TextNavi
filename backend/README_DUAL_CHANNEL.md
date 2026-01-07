# Dual-Channel Retrieval System for VLN

This system implements a sophisticated dual-channel retrieval approach that combines natural language and structured text representations for improved indoor navigation accuracy.

## 🏗️ Architecture Overview

### Dual Channels
1. **Natural Language Channel**: Uses BLIP image captions and natural language descriptions
2. **Structured Channel**: Uses canonicalized structured information (objects, relations, spatial info)

### Fusion Scoring
```
Final Score = α × s_struct + (1-α) × s_nl + β × bonus_keywords + γ × bonus_bearing
```

Where:
- `α`: Weight for structured channel (0.0 = NL only, 1.0 = structured only)
- `β`: Weight for keyword overlap bonus
- `γ`: Weight for bearing consistency bonus

## 🚀 Quick Start

### 1. Build Dual-Channel Index
```bash
cd backend
python build_index.py
```

This will create:
- `SCENE_A_MS.npz` - Dual-channel embeddings
- `SCENE_A_MS.ids.json` - Metadata with channel types
- `SCENE_A_MS.faiss.nl` - FAISS index for natural language
- `SCENE_A_MS.faiss.struct` - FAISS index for structured text

### 2. Configure Parameters
Set environment variables in your `.env` file:

```bash
# Core parameters
RANK_ALPHA=0.7          # Weight for structured channel
RANK_BETA=0.05          # Weight for keyword bonus  
RANK_GAMMA=0.03         # Weight for bearing bonus
CONFIDENCE_THRESHOLD=0.07  # High confidence threshold

# Provider-specific (recommended)
RANK_ALPHA_4O=0.0       # For base/4o models (no structured input)
RANK_ALPHA_FT=0.7       # For finetuned models (with structured input)
```

### 3. Test the System
```bash
# Start the backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Run evaluation (optional)
python evaluate_dual_channel.py
```

## 📊 How It Works

### Index Building
1. **Extract Natural Language**: From node names, retrieval hints, keywords
2. **Extract Structured Info**: Objects, spatial relations, bearings, distances
3. **Generate Canonical Text**: Convert structured data to standardized format
4. **Dual Embedding**: Create separate embeddings for each channel

### Retrieval Process
1. **BLIP Caption**: Generate image description
2. **Canonicalization**: Convert caption to structured format
3. **Dual Similarity**: Compute similarity in both channels
4. **Fusion Scoring**: Combine scores with configurable weights
5. **Confidence Analysis**: Determine if result is high-confidence

### Example Canonicalization
```
Input: "I see a window ahead with boxes on the floor"
Output: "objects=window boxes; spatial=bearing-ahead"
```

## 🎯 Provider-Specific Configuration

### For 4o/Base Models
- **α = 0.0**: Pure natural language retrieval
- **Use case**: When you only have natural language descriptions
- **Performance**: Baseline accuracy, no structured boost

### For Finetuned Models  
- **α = 0.7**: Balanced dual-channel approach
- **Use case**: When you have both NL and structured input
- **Performance**: Significantly improved accuracy through fusion

## 🔧 Configuration Tuning

### Alpha Sensitivity
- **α = 0.0**: Natural language only
- **α = 0.3-0.5**: Balanced approach
- **α = 0.7-0.8**: Structured-focused (recommended for ft)
- **α = 1.0**: Structured only

### Bonus Weights
- **β (keywords)**: 0.05-0.15 for object matching
- **γ (bearing)**: 0.03-0.08 for spatial consistency

### Confidence Threshold
- **0.05-0.07**: Strict (fewer false positives)
- **0.07-0.12**: Balanced (recommended)
- **0.12-0.15**: Lenient (more matches)

## 📈 Evaluation

Run the evaluation script to find optimal parameters:

```bash
python evaluate_dual_channel.py
```

This will:
- Test different alpha values
- Generate performance plots
- Recommend optimal configuration
- Save results to `evaluation_results/`

## 🔍 API Response Format

The `/api/locate` endpoint now returns detailed scoring information:

```json
{
  "caption": "I see a window ahead with boxes",
  "node_id": "dp_ms_entrance",
  "candidates": [
    {
      "id": "dp_ms_entrance",
      "type": "node", 
      "text": "Maker Space entrance central line",
      "score": 0.823,
      "score_nl": 0.756,
      "score_struct": 0.891,
      "bonus_keywords": 0.12,
      "bonus_bearing": 0.8,
      "channel": "nl"
    }
  ],
  "bearing": "ahead",
  "low_conf": false,
  "confidence": "high",
  "confidence_reason": "clear_winner (diff=0.089)",
  "suggestion": "High confidence match",
  "retrieval_method": "dual_channel_fusion"
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Index not found**
   ```bash
   # Rebuild index
   python build_index.py
   ```

2. **Import errors**
   ```bash
   # Install dependencies
   pip install sentence-transformers faiss-cpu matplotlib
   ```

3. **Low accuracy**
   - Check alpha value for your provider type
   - Verify structured data quality
   - Adjust bonus weights

### Fallback Behavior
If dual-channel retrieval fails, the system automatically falls back to legacy retrieval, ensuring backward compatibility.

## 🔮 Future Enhancements

1. **Few-shot LLM Canonicalization**: Replace rule-based with learned extraction
2. **Dynamic Alpha Tuning**: Automatically adjust based on data quality
3. **Multi-modal Fusion**: Combine visual features with text
4. **Hierarchical Retrieval**: Multi-level matching for complex scenes

## 📚 References

- **Sentence Transformers**: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **FAISS**: [Facebook AI Similarity Search](https://github.com/facebookresearch/faiss)
- **BLIP**: [Bootstrapping Language-Image Pre-training](https://github.com/salesforce/BLIP)

## 🤝 Contributing

To improve the system:
1. Test with different alpha values
2. Enhance canonicalization rules
3. Add new bonus scoring methods
4. Optimize for specific use cases

---

**Note**: This system is designed to work alongside your existing VLN infrastructure. It provides significant accuracy improvements while maintaining full backward compatibility.
