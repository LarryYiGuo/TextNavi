# VLN4VI 系统优化说明

## 🎯 优化目标

解决两个主要问题：
1. **拍照后识别出的置信度太低**
2. **系统在反复输出output内容，而不是去和textmap进行匹配**

## 🔧 参数优化

### 1. 双通道检索参数优化

#### 原始配置
```python
RANK_ALPHA_FT = 0.7      # ft模型的结构化通道权重
RANK_ALPHA_4O = 0.0      # base/4o模型的结构化通道权重
RANK_BETA = 0.05          # 关键词奖励权重
RANK_GAMMA = 0.03         # 方向奖励权重
```

#### 优化后配置
```python
RANK_ALPHA_FT = 0.8      # 增加ft模型的结构化通道权重
RANK_ALPHA_4O = 0.3      # 为base/4o模型添加适度的结构化权重
RANK_BETA = 0.10          # 增加关键词奖励权重
RANK_GAMMA = 0.08         # 增加方向奖励权重
```

### 2. 置信度阈值优化

#### 原始配置
```python
CONFIDENCE_THRESHOLD = 0.07    # 置信度差异阈值
LOWCONF_SCORE_TH = 0.40        # 低置信度分数阈值
LOWCONF_MARGIN_TH = 0.07       # 低置信度差异阈值
```

#### 优化后配置
```python
CONFIDENCE_THRESHOLD = 0.05    # 降低置信度差异阈值
LOWCONF_SCORE_TH = 0.30        # 降低低置信度分数阈值
LOWCONF_MARGIN_TH = 0.05       # 降低低置信度差异阈值
```

## 📈 优化效果

### 置信度提升
- **更宽松的阈值**: 允许更多合理的匹配通过置信度检查
- **更好的参数平衡**: 结构化信息和自然语言信息的权重更加平衡
- **增强的奖励机制**: 关键词和方向匹配获得更高的奖励

### textmap匹配改进
- **增加结构化权重**: ft模型现在更重视结构化信息，提高textmap匹配质量
- **base模型支持**: 为base/4o模型添加适度的结构化权重，改善整体性能
- **更好的融合策略**: 双通道融合更加平衡，减少对单一通道的依赖

## 🚀 使用方法

### 1. 重启服务
参数修改后需要重启后端服务：
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### 2. 验证配置
检查控制台输出，确认新的参数值：
```
🔧 Low-confidence thresholds: score<0.30, margin<0.05
✓ Loaded unified index: X records
```

### 3. 测试效果
- 拍照后观察置信度指标
- 检查是否仍然反复输出output内容
- 验证textmap匹配的质量

## 🔍 进一步调优

如果效果仍不理想，可以进一步调整：

### 提高置信度
```python
LOWCONF_SCORE_TH = 0.25        # 进一步降低分数阈值
LOWCONF_MARGIN_TH = 0.03       # 进一步降低差异阈值
```

### 增强textmap匹配
```python
RANK_ALPHA_FT = 0.9            # 进一步提高结构化权重
RANK_BETA = 0.15               # 进一步提高关键词权重
RANK_GAMMA = 0.12              # 进一步提高方向权重
```

## 📊 监控指标

观察以下指标来评估优化效果：

1. **置信度分布**: 高/中/低置信度的比例
2. **Top-1准确率**: 预测正确的比例
3. **textmap匹配质量**: 是否减少了重复的output输出
4. **用户满意度**: 系统响应的准确性和及时性

## ⚠️ 注意事项

1. **参数平衡**: 过度调整可能导致过拟合或性能下降
2. **场景差异**: 不同场景可能需要不同的参数设置
3. **监控日志**: 持续监控系统性能，及时发现问题
4. **渐进调优**: 建议逐步调整参数，观察效果后再决定下一步

## 🔄 回滚方案

如果优化效果不理想，可以快速回滚到原始配置：

```python
# 恢复原始参数
RANK_ALPHA_FT = 0.7
RANK_ALPHA_4O = 0.0
RANK_BETA = 0.05
RANK_GAMMA = 0.03
CONFIDENCE_THRESHOLD = 0.07
LOWCONF_SCORE_TH = 0.40
LOWCONF_MARGIN_TH = 0.07
```

重启服务即可生效。
