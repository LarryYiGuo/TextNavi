# Confidence & Top-1 Accuracy Tracking System

This system implements confidence scoring and Top-1 accuracy tracking for VLN localization, enabling data-driven optimization of retrieval parameters.

## 🎯 Features

### Backend (FastAPI)
- **Confidence Calculation**: Automatic confidence scoring based on fusion scores and margins
- **CSV Logging**: Detailed logs of all localization attempts in `logs/locate_log.csv`
- **Ground Truth Support**: Optional `gt_node_id` parameter for accuracy tracking
- **Provider Tracking**: Records which model (ft/base) was used for each attempt

### Frontend (React)
- **Ground Truth Input**: Optional input field for ground truth node ID
- **Confidence Display**: Shows Top1 prediction, confidence score, and margin
- **Candidate Debugging**: Displays top 3 candidates with scores
- **Development Mode**: Toggle to show/hide detailed development information

### Analysis Tools
- **Top-1 Accuracy Statistics**: Comprehensive accuracy metrics by provider, site, confidence level, and margin
- **CSV Analysis**: Easy to import into Excel/Python for further analysis

## 🚀 Quick Start

### 1. Build Dual-Channel Index
```bash
cd backend
python build_index.py
```

### 2. Start Backend
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test with Ground Truth
- In the frontend, enter a known node ID in the "GT Node ID" field
- Take a photo and observe the confidence metrics
- Check the console for detailed candidate information

### 4. Analyze Results
```bash
# View Top-1 accuracy statistics
python tools/metrics_top1.py

# Or specify a custom log file
python tools/metrics_top1.py logs/locate_log.csv
```

## 📊 Understanding the Metrics

### Confidence Score
- **High (>0.7)**: Very confident prediction
- **Medium (0.4-0.7)**: Moderately confident
- **Low (<0.4)**: Low confidence, consider manual verification

### Margin (Top1 - Second)
- **Large (>0.15)**: Clear winner, high confidence
- **Medium (0.07-0.15)**: Good separation
- **Small (<0.07)**: Close competition, low confidence

### Top-1 Accuracy
- **Overall**: Percentage of correct predictions across all attempts
- **By Provider**: Compare ft vs base model performance
- **By Site**: Analyze performance in different environments
- **By Confidence**: Understand accuracy vs confidence relationship

## 🔧 Configuration

### Environment Variables
```bash
# Core parameters
RANK_ALPHA_FT=0.7          # Weight for ft models
RANK_ALPHA_4O=0.0          # Weight for base/4o models
RANK_BETA=0.05              # Keyword bonus weight
RANK_GAMMA=0.03             # Bearing bonus weight

# Logging
LOG_DIR=logs                # Directory for log files
```

### Confidence Thresholds
```python
# In app.py, adjust these thresholds:
low_conf = top1_score < 0.4 or margin < 0.07
```

## 📈 CSV Log Format

The `logs/locate_log.csv` contains:

| Column | Description |
|--------|-------------|
| `ts_iso` | Timestamp (ISO format) |
| `session_id` | User session identifier |
| `site_id` | Scene identifier |
| `provider` | Model type (ft/base) |
| `caption` | BLIP-generated caption |
| `top1_id` | Predicted node ID |
| `top1_score` | Confidence score |
| `second_score` | Second-best score |
| `margin` | Score difference |
| `gt_node_id` | Ground truth (if provided) |
| `correct` | Whether prediction was correct |
| `candidates_json` | Full candidate list (JSON) |

## 🎯 Use Cases

### Development & Testing
1. **Parameter Tuning**: Adjust α, β, γ values and observe accuracy changes
2. **Model Comparison**: Compare ft vs base model performance
3. **Error Analysis**: Identify patterns in incorrect predictions

### Production Monitoring
1. **Performance Tracking**: Monitor accuracy over time
2. **Quality Assurance**: Flag low-confidence predictions for review
3. **User Experience**: Provide confidence feedback to users

### Research & Analysis
1. **Data Collection**: Build datasets for model improvement
2. **Performance Analysis**: Understand retrieval system behavior
3. **Benchmarking**: Compare against other approaches

## 🔍 Example Workflow

### 1. Collect Ground Truth Data
```
GT Node ID: dp_ms_entrance
Take photo → Get prediction → Check if correct
```

### 2. Analyze Performance
```bash
python tools/metrics_top1.py
# Output:
# 🎯 Overall Top-1 Accuracy: 8/10 = 80.00%
# 📊 By Provider:
#   ft: 6/7 = 85.71%
#   base: 2/3 = 66.67%
```

### 3. Optimize Parameters
- Adjust `RANK_ALPHA_FT` based on ft model performance
- Tune confidence thresholds based on accuracy vs confidence trade-off
- Modify bonus weights based on keyword/bearing effectiveness

## 🚨 Troubleshooting

### Common Issues

1. **No logs generated**
   - Check `LOG_DIR` environment variable
   - Ensure backend has write permissions

2. **Low accuracy**
   - Verify ground truth labels are correct
   - Check if confidence thresholds are appropriate
   - Consider adjusting fusion weights

3. **High confidence, low accuracy**
   - Review ground truth data quality
   - Check for systematic errors in node mapping
   - Consider adding more training data

### Debug Mode

Enable detailed logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## 🔮 Future Enhancements

1. **Real-time Monitoring**: Web dashboard for live performance tracking
2. **Automated Tuning**: Machine learning for parameter optimization
3. **User Feedback**: Allow users to correct predictions
4. **Performance Alerts**: Notify when accuracy drops below thresholds

---

**Note**: This system is designed to work alongside your existing VLN infrastructure. It provides comprehensive insights into retrieval performance while maintaining full backward compatibility.
