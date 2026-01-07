# 分层融合架构：Structure Anchor + Detail Overlay

## 🎯 设计理念

### 核心思想
"先靠结构保证定位正确，再靠细节提升用户理解"

### 架构特点
- **Structure Anchor**: 结构通道主导匹配，保证定位稳定性
- **Detail Overlay**: 细节通道作为语义增强，不参与初次匹配
- **分层置信度**: `C_total = C_structure × (1 + α·C_detail)`

## 🏗️ 系统架构

### 1. 分层检索流程
```
Phase 1: Structure Anchor (Primary)
├── 结构节点检索 (node-level matching)
├── 保证定位稳定性
└── 生成基础置信度

Phase 2: Detail Overlay (Enhancement)
├── 局部语义增强 (local semantic overlay)
├── 仅对Top-3候选进行增强
└── 不参与初次匹配决策
```

### 2. 置信度计算
```python
# 分层置信度公式
C_total = C_structure × (1 + α·C_detail)

# 其中：
# - C_structure: 结构通道的基础置信度 (0.6-0.9)
# - C_detail: 细节通道的增强分数 (0.0-1.0)
# - α: 增强权重系数 (0.3)
# - 最大增强: 20% (避免detail稀释structure)
```

## 🔧 技术实现

### 1. 核心函数
```python
def enhanced_ft_retrieval(caption, retriever, site_id, detailed_data):
    """分层融合检索主函数"""
    
    # Phase 1: Structure Anchor
    structure_candidates = retriever.retrieve(caption, top_k=10)
    
    # Phase 2: Detail Overlay (仅Top-3)
    for candidate in structure_candidates[:3]:
        node_details = find_node_details(candidate["id"], detailed_data)
        detail_score = calculate_detail_enhancement(caption, node_details)
        
        # 分层置信度计算
        enhanced_score = structure_score * (1 + 0.3 * detail_score)
        enhanced_score = min(enhanced_score, structure_score * 1.2)  # 最大20%提升
```

### 2. 细节增强计算
```python
def calculate_detail_enhancement(caption, node_details):
    """计算细节增强分数"""
    
    # 语义相似度 (使用SentenceTransformer)
    semantic_score = cosine_similarity(embeddings) * 0.4
    
    # 结构化文本匹配
    struct_score = parse_structured_text(caption, struct_text) * 0.3
    
    # 取最佳匹配
    return max(semantic_score, struct_score)
```

### 3. 冲突检测机制
```python
# 检测structure-detail不一致
if detail_score < structure_score * 0.3:
    structure_detail_conflict = True
    
# 触发澄清对话
if structure_detail_conflict:
    clarification_triggered = True
    # 生成特定澄清："前方有一个带紫色椅子的办公桌，是这样吗？"
```

## 📊 数据流

### 1. 输入数据
- **Structure Channel**: `Sense_A_Finetuned.fixed.jsonl` (拓扑语义)
- **Detail Channel**: `SCENE_A_MS_detailed.jsonl` (视觉细节)

### 2. 输出格式
```json
{
  "id": "poi_3d_printer_table",
  "score": 0.78,  // 增强后的总分
  "structure_score": 0.75,  // 结构分数
  "detail_score": 0.32,  // 细节分数
  "enhancement_ratio": 0.32,  // 增强比例
  "retrieval_method": "hierarchical_fusion"
}
```

## 🎯 优势分析

### 1. 定位稳定性
- **Structure主导**: 保证节点级定位的准确性
- **Detail不干扰**: 避免语义噪声影响全局一致性
- **置信度保护**: Structure分数作为底线，不被Detail稀释

### 2. 用户体验提升
- **语义增强**: 通过Detail提供更丰富的环境描述
- **冲突检测**: 自动识别不一致，触发澄清对话
- **渐进式理解**: 先定位，再理解细节

### 3. 系统鲁棒性
- **降级机制**: Detail不可用时，仍能提供基础定位
- **冲突处理**: 智能检测和处理不一致情况
- **性能优化**: 仅对Top候选进行Detail增强

## 🔍 监控指标

### 1. 性能指标
- Structure置信度分布
- Detail增强效果
- 冲突检测率
- 澄清触发率

### 2. 质量指标
- 定位准确率
- 用户满意度
- 系统响应时间
- 错误恢复能力

## 🚀 使用场景

### 1. 标准检索
- 用户拍照 → Structure定位 → Detail增强 → 导航指导

### 2. 冲突处理
- Structure定位正确但Detail模糊 → 触发澄清 → 用户确认

### 3. 降级模式
- Detail不可用 → 仅使用Structure → 基础定位服务

## 📝 配置参数

### 1. 增强权重
```python
alpha = 0.3  # Detail增强权重
max_boost = 1.2  # 最大增强倍数
conflict_threshold = 0.3  # 冲突检测阈值
```

### 2. 候选数量
```python
structure_top_k = 10  # 结构检索候选数
detail_enhance_top_k = 3  # 细节增强候选数
```

## 🔮 未来扩展

### 1. 自适应权重
- 根据用户行为动态调整α值
- 学习最优的增强策略

### 2. 多模态融合
- 集成视觉特征
- 音频信息增强

### 3. 个性化增强
- 用户偏好学习
- 定制化Detail权重

## 📚 相关文档

- `README_CONFIDENCE_IMPROVEMENT.md` - 置信度改进说明
- `README_DUAL_CHANNEL.md` - 双通道检索说明
- `README_DYNAMIC_NAVIGATION.md` - 动态导航说明

## 🎉 总结

分层融合架构通过"Structure Anchor + Detail Overlay"的设计，成功解决了传统混合模式的置信度稀释问题，实现了：

1. **高置信度定位** - Structure保证基础准确性
2. **丰富语义理解** - Detail提供环境细节
3. **智能冲突处理** - 自动检测和澄清不一致
4. **渐进式用户体验** - 先定位，再理解，最后指导

这种架构既保持了单通道的高置信度优势，又通过语义增强提升了用户理解，是一个平衡准确性和用户体验的优秀解决方案。
