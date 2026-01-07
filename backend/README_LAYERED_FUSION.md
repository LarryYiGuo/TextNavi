# 分层架构 (Layered Fusion) 实现说明

## 🏗️ 架构概述

分层架构 (Layered Fusion) 是一种新的数据融合方法，将定位和对话增强分离，确保定位准确性的同时提供丰富的用户体验。

### 核心设计原则

1. **定位阶段**：单通道，只用Structure文件
2. **交互阶段**：分层调用，Structure+Detail融合

## 📁 数据文件分工

### Structure Map (单通道 backbone)
- **功能**：定位 (localization) + 路径推理
- **特点**：IndoorGML/OSM风格，节点-边抽象，保证拓扑一致性
- **优势**：定位稳定，Top-1准确率高，不会因为语言模糊而偏移
- **文件**：
  - `Sense_A_Finetuned.fixed.jsonl` → SCENE_A_MS
  - `Sense_B_Finetuned.fixed.jsonl` → SCENE_B_STUDIO

### Detail Map (辅助层)
- **功能**：在定位完成后，进入对话澄清与自然语言增强
- **特点**：高颗粒度、自然语言化，来自BLIP caption + 人工标注
- **优势**：提升用户可理解性，提供landmark context，降低cognitive load
- **缺点**：如果直接用于匹配，embedding空间噪声大，降低置信度
- **文件**：
  - `Sense_A_MS.jsonl` → SCENE_A_MS
  - `Sense_B_Studio.jsonl` → SCENE_B_STUDIO

## 🔄 执行流程

### Phase 1: 定位阶段 (单通道)
```
用户拍照 → BLIP caption → Structure检索 → 纯Structure评分 → 位置确定
    ↓           ↓           ↓              ↓              ↓
  图像描述   语义理解   只用Structure文件   机器逻辑匹配     位置锁定
```

**关键**：Detail文件完全不参与，避免噪声影响置信度

### Phase 2: 交互阶段 (分层调用)
```
位置确定后 → Structure提供拓扑信息 → Detail提供环境描述 → 融合对话输出
    ↓              ↓              ↓              ↓
  位置已知     机器逻辑信息     人类对话信息     最终用户响应
```

## 🛠️ 代码实现

### 1. 分层融合检索函数

```python
def enhanced_ft_retrieval(caption: str, retriever, site_id: str, detailed_data: list) -> list:
    """Layered Fusion: Structure-only localization + Detail for post-localization enhancement"""
    
    # Phase 1: Structure-only localization (single channel)
    structure_candidates = retriever.retrieve(caption, top_k=10, scene_filter=site_id)
    
    # Phase 2: Add detail metadata for post-localization enhancement
    # Detail files are NOT used for scoring, only attached for later use
    enhanced_candidates = []
    
    for candidate in structure_candidates:
        node_id = candidate["id"]
        structure_score = candidate["score"]
        
        # Find associated detail descriptions for post-localization use
        node_details = find_node_details_by_hint(node_id, detailed_data)
        
        # Create enhanced candidate with detail metadata
        enhanced_candidate = {
            **candidate,
            "score": structure_score,  # Keep original structure score unchanged
            "structure_score": structure_score,
            "detail_score": 0.0,  # Detail does not contribute to scoring
            "detail_metadata": node_details,  # Attach for conversation enhancement
            "retrieval_method": "layered_fusion_structure_only"
        }
        
        enhanced_candidates.append(enhanced_candidate)
    
    # Sort by structure score only (detail does not affect ranking)
    enhanced_candidates.sort(key=lambda x: x["score"], reverse=True)
    return enhanced_candidates[:10]
```

### 2. 分层对话生成函数

```python
def generate_dynamic_navigation_response(site_id: str, node_id: str, confidence: float, low_conf: bool, matching_data: dict, lang: str = "en", candidate_info: dict = None) -> str:
    """Generate layered fusion navigation: Structure for location + Detail for conversation enhancement"""
    
    # Phase 1: Structure-based location information
    structure_response = get_structure_based_location_info(site_id, node_id, lang)
    
    # Phase 2: Detail-based conversation enhancement
    detail_response = get_detail_based_conversation_enhancement(node_id, detail_metadata, lang)
    
    # Combine both responses for rich user experience
    if detail_response:
        final_response = f"{structure_response} {detail_response}"
    else:
        final_response = structure_response
    
    return final_response
```

### 3. Structure信息生成

```python
def get_structure_based_location_info(site_id: str, node_id: str, lang: str = "en") -> str:
    """Get location information from Structure files"""
    if site_id == "SCENE_A_MS":
        return generate_scene_a_structure_info(node_id, lang)
    elif site_id == "SCENE_B_STUDIO":
        return generate_scene_b_structure_info(node_id, lang)
```

### 4. Detail对话增强

```python
def get_detail_based_conversation_enhancement(node_id: str, detail_metadata: list, lang: str = "en") -> str:
    """Get conversation enhancement from Detail files"""
    if not detail_metadata:
        return ""
    
    detail_item = detail_metadata[0]
    spatial_relations = detail_item.get("spatial_relations", {})
    unique_features = detail_item.get("unique_features", [])
    
    # Generate rich environment description
    enhancement_parts = []
    
    # Add spatial context
    if spatial_relations:
        if "front" in spatial_relations and spatial_relations["front"] != "n/a":
            enhancement_parts.append(f"前方：{spatial_relations['front']}")
        # ... more spatial relations
    
    # Add unique features
    if unique_features:
        features = [f for f in unique_features if f and f != ""]
        if features:
            enhancement_parts.append(f"特色：{', '.join(features)}")
    
    if enhancement_parts:
        return f"环境描述：{'；'.join(enhancement_parts)}。"
    
    return ""
```

## 🔍 数据对齐机制

### 关键字段：`node_hint`

在Detail文件中：
```json
{
  "id": "SCENE_A_MS_IMG_0107",
  "node_hint": "dp_ms_entrance",  // 指向Structure文件中的节点
  "nl_text": "View near dp ms entrance...",
  "spatial_relations": {...},
  "unique_features": [...]
}
```

### 对齐过程：
1. Structure检索得到候选节点ID (如`dp_ms_entrance`)
2. 在Detail文件中查找`node_hint`匹配该ID的记录
3. 使用匹配的Detail记录进行对话增强

## 📊 实际应用示例

### SCENE_A_MS场景：
```
用户拍照 → Structure: Sense_A_Finetuned.fixed.jsonl → 定位到"dp_ms_entrance"
         → Detail: Sense_A_MS.jsonl → 找到node_hint="dp_ms_entrance"的记录
         → 融合: Structure提供基础定位 + Detail提供环境描述
```

### 输出示例：
```
Structure: "您在Maker Space入口。直行约6步到达3D打印机桌，然后左转继续前进进入中庭。"
Detail: "环境描述：前方：黄色引导线；左侧：QR书架和衣帽架；右侧：抽屉墙/3D打印机。"
最终: "您在Maker Space入口。直行约6步到达3D打印机桌，然后左转继续前进进入中庭。环境描述：前方：黄色引导线；左侧：QR书架和衣帽架；右侧：抽屉墙/3D打印机。"
```

## ✅ 优势总结

### 1. 定位稳定性
- Structure文件保证拓扑一致性
- 避免Detail的语义噪声
- 置信度计算纯净可靠

### 2. 交互丰富性
- Detail文件提供landmark context
- 降低用户认知负荷
- 提升导航体验

### 3. 职责清晰
- Structure：机器逻辑，负责"在哪里"
- Detail：人类对话，负责"怎么描述"

## 🎯 关键特性

1. **单通道定位**：只用Structure文件，保证高置信度
2. **分层对话**：定位成功后，Detail文件参与对话生成
3. **数据对齐**：通过`node_hint`字段正确关联两个数据源
4. **职责分离**：定位准确性 vs 交互丰富性

这种架构既保证了定位的准确性，又提供了丰富的用户体验，是一个平衡稳定性和增强效果的优秀解决方案！
