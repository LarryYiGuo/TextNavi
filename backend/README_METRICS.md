# VLN4VI 综合指标自动记录系统

这个系统实现了完整的 VLN 性能指标自动记录，包括定位成功率、端到端时延和低置信度触发率，为你的实验提供产品级的数据支持。

## 🎯 核心指标

### 1. 定位成功率 (Localization Success Rate)
- **Top-1 准确率**: 系统返回的置信度最高的节点，是否就是用户的实际所在节点？
- **Top-2 准确率**: 用户的实际位置，是否在系统返回的前两个候选节点之中？
- **±1-Hop 准确率**: 系统定位的节点，是否与用户的实际节点在拓扑图上直接相连？

### 2. 端到端时延 (End-to-End Latency)
- 从用户点击拍照按钮，到系统开始播报第一句指令，总共耗时多少秒？
- 这个数据直接关系到 DG1（轻量化）目标

### 3. 低置信度触发率 (Low-Confidence Trigger Rate)
- 在所有定位请求中，有多少次系统的置信度低于设定的阈值？
- 这个数据是 RQ3 的重要输入

## 🏗️ 系统架构

### 后端改造 (FastAPI)
- **拓扑加载**: 自动加载场景拓扑图，支持 ±1-Hop 计算
- **请求追踪**: 每个请求分配唯一 ID，支持端到端时延计算
- **综合日志**: 记录所有关键指标到 CSV 文件
- **阈值配置**: 通过环境变量配置低置信度阈值

### 前端改造 (React)
- **请求 ID 生成**: 使用 `crypto.randomUUID()` 生成唯一标识
- **时间戳记录**: 记录拍照开始时间和 TTS 开始时间
- **自动埋点**: 无需手动干预，自动记录所有指标

### 分析工具
- **综合评估脚本**: 一次性计算所有关键指标
- **会话分析**: 按实验会话分组分析性能
- **结果导出**: 自动生成 JSON 格式的评估报告

## 🚀 快速开始

### 1. 配置环境变量
```bash
# 低置信度阈值配置
LOWCONF_SCORE_TH=0.40          # 置信度分数阈值
LOWCONF_MARGIN_TH=0.07         # 分数差距阈值

# 日志配置
LOG_DIR=logs                    # 日志目录
```

### 2. 启动系统
```bash
# 启动后端
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm run dev
```

### 3. 进行实验
1. 在前端设置唯一的 `session_id`（如 "U01_Run1"）
2. 在 "GT Node ID" 字段输入真实节点 ID
3. 点击 "Local" 拍照定位
4. 观察置信度指标和预测结果

### 4. 分析结果
```bash
# 运行综合评估
python tools/metrics_eval.py

# 或指定自定义日志文件
python tools/metrics_eval.py logs/locate_log.csv logs/latency_log.csv
```

## 📊 日志格式

### 定位日志 (locate_log.csv)
| 字段 | 描述 | 示例 |
|------|------|------|
| `ts_iso` | 时间戳 | 2024-12-01T14:30:22.123456 |
| `req_id` | 请求 ID | a1b2c3d4e5f6 |
| `session_id` | 会话 ID | U01_Run1 |
| `site_id` | 场景 ID | SCENE_A_MS |
| `provider` | 模型类型 | ft |
| `caption` | BLIP 描述 | "a person standing in front of a door" |
| `top1_id` | Top1 节点 | dp_ms_entrance |
| `top1_score` | Top1 分数 | 0.823 |
| `top2_id` | Top2 节点 | dp_ms_boxes |
| `top2_score` | Top2 分数 | 0.456 |
| `margin` | 分数差距 | 0.367 |
| `gt_node_id` | 真实标签 | dp_ms_entrance |
| `hit_top1` | 是否命中 Top1 | true |
| `hit_top2` | 是否命中 Top2 | true |
| `hit_hop1` | 是否在 ±1-Hop 内 | true |
| `low_conf` | 是否低置信度 | false |
| `low_conf_rule` | 低置信度原因 | score<0.40 |
| `client_start_ms` | 客户端开始时间 | 1701432622123 |
| `server_recv_ms` | 服务器接收时间 | 1701432622150 |
| `server_resp_ms` | 服务器响应时间 | 1701432622200 |

### 时延日志 (latency_log.csv)
| 字段 | 描述 | 示例 |
|------|------|------|
| `ts_iso` | 时间戳 | 2024-12-01T14:30:22.123456 |
| `req_id` | 请求 ID | a1b2c3d4e5f6 |
| `session_id` | 会话 ID | U01_Run1 |
| `site_id` | 场景 ID | SCENE_A_MS |
| `client_start_ms` | 客户端开始时间 | 1701432622123 |
| `client_tts_start_ms` | TTS 开始时间 | 1701432622250 |
| `e2e_latency_ms` | 端到端时延 | 127 |

## 🔧 配置选项

### 低置信度阈值
```bash
# 环境变量配置
export LOWCONF_SCORE_TH=0.45    # 提高置信度要求
export LOWCONF_MARGIN_TH=0.10   # 提高分数差距要求

# 或在 .env 文件中
LOWCONF_SCORE_TH=0.45
LOWCONF_MARGIN_TH=0.10
```

### 拓扑配置
编辑 `backend/topology.json` 文件，定义场景中节点的连接关系：
```json
{
  "SCENE_A_MS": {
    "dp_ms_entrance": ["dp_ms_boxes", "dp_ms_shelf"],
    "dp_ms_boxes": ["dp_ms_entrance", "dp_ms_atrium"],
    "dp_ms_shelf": ["dp_ms_entrance"],
    "dp_ms_atrium": ["dp_ms_boxes"]
  }
}
```

## 📈 实验工作流

### 1. 实验设计
```bash
# 创建实验会话
python tools/experiment_manager.py create --name "alpha_tuning" --description "测试不同alpha值的效果"

# 设置实验参数
python tools/experiment_manager.py params --session "alpha_tuning_xxx" --parameters '{"RANK_ALPHA_FT": 0.7}'
```

### 2. 数据收集
1. 在前端使用生成的会话 ID
2. 在不同位置拍照定位
3. 输入 Ground Truth 标签
4. 观察置信度指标

### 3. 结果分析
```bash
# 运行综合评估
python tools/metrics_eval.py

# 查看特定会话的性能
python tools/experiment_manager.py show --session "alpha_tuning_xxx"

# 导出会话数据
python tools/experiment_manager.py export --session "alpha_tuning_xxx"
```

## 🎯 指标解读

### 定位成功率
- **Top-1 准确率 ≥ 80%**: 优秀
- **Top-1 准确率 60-80%**: 良好
- **Top-1 准确率 < 60%**: 需要改进

### 端到端时延
- **平均时延 < 1s**: 快速响应
- **平均时延 1-3s**: 可接受
- **平均时延 > 3s**: 需要优化

### 低置信度触发率
- **触发率 < 20%**: 置信度管理良好
- **触发率 20-40%**: 置信度管理适中
- **触发率 > 40%**: 需要调整阈值

## 🔍 故障排除

### 常见问题

#### 1. 拓扑文件加载失败
```bash
# 检查文件路径
ls -la backend/topology.json

# 检查 JSON 格式
python -m json.tool backend/topology.json
```

#### 2. 日志文件未生成
- 确认 `LOG_DIR` 环境变量设置正确
- 检查后端写入权限
- 验证 `/api/locate` 调用成功

#### 3. 时延数据缺失
- 确认前端正确调用 `/api/metrics/tts_start`
- 检查网络连接
- 验证请求 ID 匹配

### 调试技巧
1. **检查后端日志**: 查看控制台输出
2. **验证前端埋点**: 检查浏览器网络请求
3. **手动测试 API**: 使用 Postman 或 curl 测试端点
4. **检查文件权限**: 确保脚本有读写权限

## 📚 高级用法

### 自定义分析
```python
# 在 Python 中分析数据
import pandas as pd

# 读取定位日志
df = pd.read_csv("logs/locate_log.csv")

# 按会话分组分析
session_metrics = df.groupby("session_id").agg({
    "hit_top1": lambda x: (x == "true").sum(),
    "gt_node_id": lambda x: (x != "").sum()
})

# 计算准确率
session_metrics["accuracy"] = session_metrics["hit_top1"] / session_metrics["gt_node_id"] * 100
```

### 批量实验
```bash
#!/bin/bash
# 自动化实验脚本

# 创建实验会话
session_id=$(python tools/experiment_manager.py create --name "batch_test" --description "批量测试")

# 设置参数
python tools/experiment_manager.py params --session "$session_id" --parameters '{"RANK_ALPHA_FT": 0.8}'

echo "Experiment setup complete. Use session ID: $session_id"
```

### 性能监控
```bash
# 实时监控日志
tail -f logs/locate_log.csv

# 定期运行评估
watch -n 60 "python tools/metrics_eval.py"
```

## 🚀 未来扩展

### 功能增强
- **实时仪表板**: Web 界面的实时性能监控
- **自动告警**: 性能指标异常时自动通知
- **趋势分析**: 长期性能趋势分析
- **A/B 测试**: 支持多组参数对比测试

### 集成选项
- **Prometheus**: 指标数据导出到监控系统
- **Grafana**: 可视化仪表板
- **ELK Stack**: 日志分析和可视化
- **机器学习**: 自动参数优化

---

**提示**: 这个系统为你的 VLN 研究提供了产品级的性能监控能力，每次实验都会自动记录完整的指标数据，帮助你进行数据驱动的系统优化。
