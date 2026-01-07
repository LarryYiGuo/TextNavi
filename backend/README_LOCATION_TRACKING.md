# 位置追踪系统 (Location Tracking System)

## 概述

本系统实现了用户位置的连续追踪，解决了后续拍照无法正确识别用户位置和朝向的问题。

## 核心功能

### 1. 会话状态管理
- 每个会话维护完整的位置历史
- 记录用户的位置变化轨迹
- 追踪朝向信息的一致性

### 2. 位置连续性验证
- 验证新位置是否与之前位置连续
- 检查位置变化的合理性
- 提供置信度调整

### 3. 朝向追踪
- 从BLIP描述中提取朝向信息
- 验证朝向变化的一致性
- 记录朝向历史

### 4. 上下文感知检索
- 考虑之前的位置信息
- 调整检索权重和置信度
- 提供更准确的位置预测

### 5. 🆕 二次判定Prompt系统
- 在用户每次提问时进行位置二次判定
- 判断用户最近的node位置和朝向
- 智能检测目的地类型（抽象化）
- 提供抽象的导航指导

### 6. 🆕 智能目的地检测
- 基于关键词分析用户询问的目的地类型
- 使用抽象分类而不是具体地点名称
- 支持多种场景和语言
- 提供通用的导航指导

### 7. 🆕 智能距离计算
- 基于场景拓扑的位置关系映射
- 提供步数、米数和方向信息
- 估算到达时间
- 支持多场景配置

## 技术实现

### 后端增强

#### 会话状态结构
```python
SESSIONS[session_id] = {
    "site_id": site_id,
    "opening_provider": provider,
    "lang": lang,
    "current_location": None,           # 当前预测位置
    "location_history": [],             # 位置历史记录
    "orientation_history": [],          # 朝向历史记录
    "confidence_history": [],           # 置信度历史记录
    "last_update_time": timestamp,     # 最后更新时间
    "photo_count": 0                   # 拍照计数
}
```

#### 位置连续性验证
```python
def validate_location_continuity(session_id, new_location, previous_location):
    """验证新位置是否与之前位置连续"""
    # 检查相同位置
    # 检查相邻位置
    # 检查位置变化的合理性
    return {"valid": True, "reason": "reason", "confidence_boost": 0.0}
```

#### 朝向追踪
```python
def track_orientation(session_id, caption, predicted_location):
    """追踪用户朝向变化"""
    # 提取朝向信息
    # 检查朝向一致性
    # 返回朝向状态
```

#### 🆕 二次判定Prompt系统
```python
def generate_location_context_prompt(session_id, user_question, site_id, lang):
    """生成包含位置二次判定的上下文prompt"""
    # 获取当前位置、朝向、稳定性信息
    # 智能检测目的地类型（抽象化）
    # 分析用户问题的导航需求
    # 生成增强的抽象导航上下文
```

#### 🆕 智能目的地检测
```python
def detect_destination_types(user_question, site_id):
    """智能检测用户询问的目的地类型"""
    # 基于关键词分析目的地类型
    # 使用抽象分类（exit, central_area, work_area等）
    # 避免硬编码具体地点名称
    # 提供通用的导航指导
```

#### 🆕 智能距离计算
```python
def get_location_distance(from_location, to_destination, site_id):
    """计算从当前位置到目的地的距离"""
    # 基于场景拓扑的位置关系
    # 提供步数、米数、方向信息
    # 估算到达时间
```

### 前端增强

#### 位置状态显示
- 当前预测位置
- 位置置信度
- 位置历史数量
- 实时更新

#### 位置查询API
```javascript
// 获取会话位置信息
const getSessionLocation = async () => {
    const data = await fetch(`/api/session/location/${sessionId}`);
    // 更新位置状态
};

// 获取会话状态
const getSessionStatus = async () => {
    const data = await fetch(`/api/session/status/${sessionId}`);
    // 获取综合状态信息
};
```

## API端点

### 1. 位置查询
```
GET /api/session/location/{session_id}
```
返回：
- 当前位置
- 位置历史
- 朝向历史
- 置信度历史

### 2. 状态查询
```
GET /api/session/status/{session_id}
```
返回：
- 综合状态信息
- 置信度趋势
- 位置稳定性
- 朝向一致性

### 3. 🆕 位置验证
```
GET /api/location/verify/{session_id}?destination={destination}
```
返回：
- 位置验证结果
- 位置一致性分析
- 到目的地的距离信息
- 导航就绪状态

### 4. 🆕 导航指导
```
GET /api/location/navigate/{session_id}?destination={destination}
```
返回：
- 详细的导航指令
- 步数和方向信息
- 预计到达时间
- 导航步骤说明

## 使用流程

### 1. 会话启动
- 初始化位置追踪状态
- 重置历史记录
- 准备位置验证

### 2. 拍照定位
- 生成BLIP描述
- 执行位置检索
- 验证位置连续性
- 更新会话状态
- 记录位置历史

### 3. 位置追踪
- 监控位置变化
- 验证移动合理性
- 调整置信度
- 提供位置反馈

### 4. 🆕 二次判定Prompt
- 用户提问时触发位置二次判定
- 分析当前位置和朝向信息
- 智能检测目的地类型（抽象化）
- 生成抽象的导航上下文

### 5. 🆕 抽象导航指导
- 基于目的地类型提供通用导航
- 考虑用户当前位置和朝向
- 使用抽象的方向和距离描述
- 避免具体地点名称，提供通用指导

## 配置参数

### 环境变量
```bash
# 位置验证阈值
LOCATION_CONFIDENCE_THRESHOLD=0.07

# 朝向一致性检查
ORIENTATION_CONSISTENCY_CHECK=true

# 位置历史保留数量
LOCATION_HISTORY_MAX=10
```

### 场景配置
```python
# 抽象目的地类型定义
DESTINATION_TYPES = {
    "SCENE_A_MS": {
        "exit": ["出口", "exit", "出去", "离开", "门", "door"],
        "central_area": ["中间", "中央", "中心", "central", "middle", "center"],
        "work_area": ["工作", "工作台", "工作区", "work", "workbench", "workspace"],
        "storage": ["存储", "储物", "架子", "storage", "shelf", "cabinet"],
        "seating": ["坐", "椅子", "休息", "seating", "chair", "rest"]
    }
}

# 相邻位置定义
ADJACENT_LOCATIONS = {
    "entrance": ["chair", "3d_printer", "glass_door"],
    "chair": ["entrance", "3d_printer", "glass_door"],
    "3d_printer": ["chair", "glass_door", "bookshelf"]
}
```

## 优势

### 1. 解决核心问题
- ✅ 后续拍照能正确追踪位置
- ✅ 识别用户朝向变化
- ✅ 提供位置连续性验证

### 2. 提升用户体验
- 📍 实时位置状态显示
- 🎯 置信度趋势分析
- 📊 位置历史追踪

### 3. 增强系统可靠性
- 🔍 位置变化合理性检查
- 🧭 朝向一致性验证
- 📈 置信度动态调整

### 4. 🆕 智能抽象导航
- 🔍 每次提问时进行位置二次判定
- 🎯 智能检测目的地类型
- 🧭 提供抽象但有用的导航指导
- 📊 避免硬编码具体地点名称

## 测试验证

### 测试场景
1. **位置连续性测试**
   - 从门口移动到椅子
   - 从椅子移动到3D打印机
   - 验证位置变化是否合理

2. **朝向一致性测试**
   - 连续拍照检查朝向
   - 验证朝向变化逻辑
   - 测试朝向冲突检测

3. **置信度追踪测试**
   - 检查置信度变化趋势
   - 验证位置稳定性
   - 测试异常情况处理

4. **🆕 抽象导航测试**
   - 测试目的地类型检测准确性
   - 验证抽象导航指导质量
   - 测试通用导航描述效果

### 预期结果
- 后续拍照能正确识别用户位置
- 系统能追踪用户朝向变化
- 位置连续性得到有效验证
- 抽象导航提供通用但有用的指导
- 用户体验显著提升

## 未来改进

### 1. 高级功能
- 路径规划优化
- 位置预测算法
- 多用户位置管理
- 实时路径更新

### 2. 性能优化
- 位置缓存机制
- 增量更新算法
- 分布式位置服务
- 智能缓存策略

### 3. 智能分析
- 用户行为模式识别
- 位置偏好学习
- 个性化导航建议
- 预测性位置服务

### 4. 🆕 导航增强
- 多路径选择
- 障碍物避让
- 动态路径调整
- 语音导航优化
- 抽象导航模式学习