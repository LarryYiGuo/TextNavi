# VLN4VI 实验管理系统

这个系统帮助你组织和跟踪 VLN 定位实验，自动记录置信度指标，并提供完整的实验生命周期管理。

## 🎯 功能特性

### 自动记录
- **每次定位自动记录**: 调用 `/api/locate` 时自动记录所有指标
- **置信度跟踪**: 记录融合分数、margin、Top1 预测等
- **Ground Truth 支持**: 可选的真实标签输入和准确率计算
- **会话管理**: 按实验会话分组管理数据

### 实验管理
- **会话创建**: 为每次实验创建独立的会话
- **参数记录**: 记录实验参数和配置
- **笔记系统**: 添加实验观察和笔记
- **数据导出**: 导出特定会话的数据进行分析

## 🚀 快速开始

### 1. 创建实验会话
```bash
# 创建新的实验会话
python tools/experiment_manager.py create --name "alpha_tuning" --description "测试不同alpha值的效果"

# 输出示例:
# ✅ 创建实验会话: alpha_tuning_20241201_143022
# 📁 会话文件: logs/session_alpha_tuning_20241201_143022.json
# 💡 使用以下会话 ID 进行实验: alpha_tuning_20241201_143022
```

### 2. 在前端使用会话 ID
- 将生成的会话 ID 复制到前端的 "Session" 字段
- 设置其他实验参数 (Provider, Site)
- 开始拍照定位实验

### 3. 添加实验笔记
```bash
# 添加实验观察
python tools/experiment_manager.py note --session "alpha_tuning_20241201_143022" --note "alpha=0.7时置信度明显提升"

# 记录参数变化
python tools/experiment_manager.py params --session "alpha_tuning_20241201_143022" --parameters '{"RANK_ALPHA_FT": 0.7, "RANK_BETA": 0.05}'
```

### 4. 查看实验结果
```bash
# 查看会话摘要
python tools/experiment_manager.py show --session "alpha_tuning_20241201_143022"

# 查看所有实验
python tools/experiment_manager.py list --details

# 导出数据
python tools/experiment_manager.py export --session "alpha_tuning_20241201_143022" --output "alpha_tuning_results.csv"
```

## 📊 置信度自动记录

### 记录内容
每次调用 `/api/locate` 时自动记录：

| 字段 | 描述 | 示例 |
|------|------|------|
| `ts_iso` | 时间戳 | 2024-12-01T14:30:22.123456 |
| `session_id` | 会话 ID | alpha_tuning_20241201_143022 |
| `site_id` | 场景 ID | SCENE_A_MS |
| `provider` | 模型类型 | ft |
| `caption` | BLIP 描述 | "a person standing in front of a door" |
| `top1_id` | 预测节点 | dp_ms_entrance |
| `top1_score` | 置信度分数 | 0.823 |
| `second_score` | 第二名分数 | 0.456 |
| `margin` | 分数差距 | 0.367 |
| `gt_node_id` | 真实标签 | dp_ms_entrance |
| `correct` | 是否正确 | True |
| `candidates_json` | 候选列表 | JSON 格式的完整候选信息 |

### 置信度计算
- **融合分数**: 双通道检索的最终得分 (0-1)
- **Margin**: Top1 与第二名的分数差距
- **置信度级别**: 
  - 高 (>0.7): 非常确信
  - 中 (0.4-0.7): 中等确信
  - 低 (<0.4): 低确信

## 🔧 命令行工具

### 基本语法
```bash
python tools/experiment_manager.py <action> [options]
```

### 可用操作

#### `create` - 创建实验会话
```bash
python tools/experiment_manager.py create --name "experiment_name" --description "实验描述"
```

#### `list` - 列出所有实验
```bash
# 基本列表
python tools/experiment_manager.py list

# 详细信息
python tools/experiment_manager.py list --details
```

#### `show` - 显示会话详情
```bash
python tools/experiment_manager.py show --session "session_id"
```

#### `note` - 添加笔记
```bash
python tools/experiment_manager.py note --session "session_id" --note "笔记内容"
```

#### `params` - 更新参数
```bash
python tools/experiment_manager.py params --session "session_id" --parameters '{"param1": "value1", "param2": "value2"}'
```

#### `export` - 导出数据
```bash
python tools/experiment_manager.py export --session "session_id" --output "output_file.csv"
```

## 📈 实验工作流

### 1. 实验设计
```bash
# 创建实验会话
python tools/experiment_manager.py create --name "alpha_sensitivity" --description "测试alpha参数敏感性"

# 记录初始参数
python tools/experiment_manager.py params --session "alpha_sensitivity_xxx" --parameters '{"RANK_ALPHA_FT": 0.5, "RANK_BETA": 0.05}'
```

### 2. 数据收集
- 在前端使用会话 ID
- 在不同位置拍照
- 输入 Ground Truth 标签
- 观察置信度指标

### 3. 参数调优
```bash
# 记录参数变化
python tools/experiment_manager.py params --session "alpha_sensitivity_xxx" --parameters '{"RANK_ALPHA_FT": 0.7}'

# 添加观察笔记
python tools/experiment_manager.py note --session "alpha_sensitivity_xxx" --note "alpha=0.7时margin增大，置信度提升"
```

### 4. 结果分析
```bash
# 查看会话摘要
python tools/experiment_manager.py show --session "alpha_sensitivity_xxx"

# 导出数据进行分析
python tools/experiment_manager.py export --session "alpha_sensitivity_xxx"

# 运行统计脚本
python tools/metrics_top1.py
```

## 🎯 最佳实践

### 实验组织
1. **命名规范**: 使用描述性的会话名称，如 `alpha_tuning_round1`
2. **参数记录**: 每次参数变化都要记录
3. **笔记详细**: 记录观察到的现象和思考
4. **定期导出**: 定期导出数据备份

### 置信度分析
1. **样本数量**: 每个参数组合至少收集 10-20 个样本
2. **Ground Truth**: 尽可能提供真实标签
3. **异常分析**: 关注低置信度样本，分析原因
4. **参数敏感性**: 系统性地测试参数范围

### 数据管理
1. **会话分离**: 不同实验使用不同会话
2. **版本控制**: 重要参数变化创建新会话
3. **备份策略**: 定期备份日志和会话文件
4. **清理策略**: 删除过期的实验数据

## 🔍 故障排除

### 常见问题

#### 会话不存在
```bash
# 检查会话列表
python tools/experiment_manager.py list

# 确认会话 ID 拼写
python tools/experiment_manager.py show --session "exact_session_id"
```

#### 数据未记录
- 确认前端使用了正确的会话 ID
- 检查后端日志文件权限
- 验证 `/api/locate` 调用成功

#### 参数格式错误
```bash
# 正确的 JSON 格式
python tools/experiment_manager.py params --session "xxx" --parameters '{"key": "value"}'

# 错误的格式 (缺少引号)
python tools/experiment_manager.py params --session "xxx" --parameters "{key: value}"
```

### 调试技巧
1. **检查日志文件**: 查看 `logs/locate_log.csv`
2. **验证会话文件**: 检查 `logs/session_*.json`
3. **使用详细模式**: `--details` 显示更多信息
4. **检查文件权限**: 确保脚本有读写权限

## 📚 高级用法

### 批量操作
```bash
# 为多个会话添加相同笔记
for session in session1 session2 session3; do
    python tools/experiment_manager.py note --session "$session" --note "批量添加的笔记"
done
```

### 数据分析集成
```bash
# 导出数据到 Python 分析脚本
python tools/experiment_manager.py export --session "xxx" --output "data.csv"

# 在 Python 中分析
import pandas as pd
df = pd.read_csv("data.csv")
# 进行数据分析...
```

### 自动化脚本
```bash
#!/bin/bash
# 自动化实验脚本示例
session_id=$(python tools/experiment_manager.py create --name "auto_experiment" --description "自动化实验")
echo "Created session: $session_id"

# 设置参数
python tools/experiment_manager.py params --session "$session_id" --parameters '{"RANK_ALPHA_FT": 0.8}'

echo "Experiment setup complete. Use session ID: $session_id"
```

---

**提示**: 这个实验管理系统与置信度跟踪完全集成，每次定位都会自动记录详细的指标，帮助你进行数据驱动的系统优化。
