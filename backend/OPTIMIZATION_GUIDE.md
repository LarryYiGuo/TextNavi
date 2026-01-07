# 🚀 置信度和成功率提升优化指南

## 🎯 目标
将置信度和成功率从当前水平提升到 **70%+**

## 🔧 优化方案

### 1. **Textmap 优化 - 增加区分度高的描述**

#### ✅ 已完成的优化
- **场景A (Maker Space)**: 增加了 `enhanced_keywords` 字段
  - 颜色: `bright_white_overhead_lights`, `black_3d_printers`, `blue_led_lights`
  - 材质: `industrial_metal_ceiling`, `gray_vinyl_flooring`, `wooden_workbenches`
  - 形状: `small_plastic_drawers`, `bright_green_recycling_lid`
  - 位置: `overhead_lights`, `floor_lines`, `wall_of_drawers`

- **场景B (Studio)**: 增加了 `enhanced_keywords` 字段
  - 颜色: `vibrant_orange_sofa`, `teal_green_lounge_chairs`
  - 材质: `floor_to_ceiling_glass`, `exposed_ceiling_pipes`
  - 形状: `glass_partitioned_room`, `white_meeting_table`
  - 位置: `floor_cable_hazard`, `low_table_corner`

#### 📝 优化原则
1. **增加具体形容词**: 用 `bright white` 替代 `bright`，用 `industrial metal` 替代 `industrial`
2. **减少模糊词**: 避免 `some`, `several`, `various` 等不明确的描述
3. **增加数量信息**: `row of 3D printers` 替代 `3D printers`
4. **增加相对位置**: `on the left side`, `near the entrance`, `ahead of you`

### 2. **RAG 融合打分优化 - 调整权重和阈值**

#### 🔧 参数调整
```python
# 基础模型 (4o)
RANK_ALPHA_4O = 0.4      # 从 0.3 提升到 0.4
RANK_BETA_4O = 0.15      # 从 0.10 提升到 0.15
RANK_GAMMA_4O = 0.12     # 从 0.08 提升到 0.12

# 微调模型 (ft)
RANK_ALPHA_FT = 0.85     # 从 0.8 提升到 0.85
RANK_BETA_FT = 0.20      # 从 0.10 提升到 0.20
RANK_GAMMA_FT = 0.15     # 从 0.08 提升到 0.15
```

#### 🆕 新增增强打分
- **颜色匹配奖励**: `COLOR_BONUS = 0.20`
- **形状匹配奖励**: `SHAPE_BONUS = 0.18`
- **位置匹配奖励**: `POSITION_BONUS = 0.15`
- **数量匹配奖励**: `QUANTITY_BONUS = 0.12`
- **增强关键词奖励**: `ENHANCED_KEYWORD_BONUS = 0.25`

### 3. **Low Confidence 阈值调优**

#### 🔧 阈值调整
```python
LOWCONF_SCORE_TH = 0.45      # 从 0.30 提升到 0.45
LOWCONF_MARGIN_TH = 0.08     # 从 0.05 提升到 0.08

# 场景特定阈值
SCENE_A_MS_THRESHOLD = 0.70
SCENE_B_STUDIO_THRESHOLD = 0.75
```

#### 📊 阈值说明
- **Score Threshold**: 提高最低置信度要求，减少误判
- **Margin Threshold**: 提高top1和top2之间的差异要求，确保唯一性

### 4. **BM25 + Embedding 融合优化**

#### 🔧 权重调整
```python
BM25_WEIGHT = 0.60           # BM25 权重
EMBEDDING_WEIGHT = 0.40      # Embedding 权重
```

#### 📊 融合策略
- **BM25**: 擅长精确关键词匹配，权重较高
- **Embedding**: 擅长语义相似性，权重适中
- **动态调整**: 根据场景和提供者动态调整权重

## 🚀 实施步骤

### 步骤 1: 更新配置文件
```bash
# 复制优化后的配置文件
cp config_optimized.py config.py
cp env_optimized.txt .env
```

### 步骤 2: 更新 Textmap 文件
```bash
# 使用优化后的 textmap 文件
cp Sense_A_Finetuned_optimized.jsonl Sense_A_Finetuned.fixed.jsonl
cp Sense_B_Finetuned_optimized.jsonl Sense_B_Finetuned.fixed.jsonl
```

### 步骤 3: 集成增强 RAG 打分
```python
# 在 app.py 中导入
from enhanced_rag_scoring import create_enhanced_rag_scorer

# 创建增强打分器
enhanced_scorer = create_enhanced_rag_scorer()

# 使用增强打分
ranked_candidates = enhanced_scorer.rank_candidates(
    caption, candidates, provider, site_id
)
```

### 步骤 4: 测试和验证
```bash
# 运行测试脚本
python test_optimization.py

# 检查日志中的置信度指标
tail -f logs/locate_log.csv
```

## 📊 预期效果

### 置信度提升
- **当前**: ~50-60%
- **目标**: 70%+
- **提升**: 15-20%

### 成功率提升
- **当前**: ~60-70%
- **目标**: 80%+
- **提升**: 10-15%

### 误判率降低
- **场景混淆**: 从 ~15% 降低到 ~5%
- **低置信度**: 从 ~25% 降低到 ~15%

## 🔍 监控指标

### 关键指标
1. **Top1 置信度**: 目标 > 0.70
2. **置信度边际**: 目标 > 0.08
3. **场景识别准确率**: 目标 > 95%
4. **低置信度触发率**: 目标 < 15%

### 日志分析
```bash
# 分析置信度分布
grep "confidence" logs/locate_log.csv | awk -F',' '{print $12}' | sort -n

# 分析场景识别准确率
grep "SCENE_A_MS" logs/locate_log.csv | wc -l
grep "SCENE_B_STUDIO" logs/locate_log.csv | wc -l
```

## ⚠️ 注意事项

### 1. **参数调优**
- 不要一次性调整所有参数
- 逐步调整并观察效果
- 记录每次调整的影响

### 2. **数据质量**
- 确保 textmap 文件格式正确
- 验证增强关键词的准确性
- 定期更新和优化描述

### 3. **性能监控**
- 监控响应时间变化
- 观察内存使用情况
- 确保优化不引入性能问题

## 🎯 下一步计划

### 短期 (1-2周)
1. 部署优化后的配置文件
2. 测试增强 RAG 打分
3. 收集性能数据

### 中期 (1个月)
1. 根据数据调整参数
2. 优化 textmap 描述
3. 实现动态阈值调整

### 长期 (3个月)
1. 集成机器学习优化
2. 实现自适应参数调整
3. 扩展到更多场景

## 📞 技术支持

如有问题，请检查：
1. 配置文件是否正确加载
2. 环境变量是否设置
3. 日志中的错误信息
4. 性能监控数据
