# VLN4VI RQ3 数据收集系统 - 信任与错误处理

这个系统实现了完整的 RQ3 (信任与错误处理) 数据自动收集，包括误信率、澄清对话效果和错误恢复能力，为你的信任研究提供数据支持。

## 🎯 RQ3 核心指标

### 1. 误信率 (Misbelief Rate)
- **定义**: 参与者在系统给出错误的定位和指令后，没有提出质疑并直接遵循错误指令的次数
- **测量**: 自动检测预测错误 + 未触发澄清对话的情况
- **数据**: 记录在 `locate_log.csv` 的 `misbelief` 字段

### 2. 澄清轮次与成功率 (Clarification Rounds & Success)
- **澄清轮次**: 当低置信度澄清对话被触发时，平均需要几轮问答才能解决问题
- **成功率**: 澄清对话成功帮助用户确定位置的比例
- **数据**: 记录在 `clarification_log.csv`

### 3. 错误恢复时长 (Error Recovery Time)
- **定义**: 从参与者意识到走错路开始，到他成功回到正确路径上花费的时间
- **测量**: 自动检测错误路径进入和正确路径恢复的时间点
- **数据**: 记录在 `recovery_log.csv`

## 🏗️ 系统架构

### 后端数据记录
- **自动检测**: 系统自动识别预测错误、低置信度和路径偏离
- **会话管理**: 为每个澄清对话分配唯一 ID，追踪完整对话流程
- **时间追踪**: 精确记录错误恢复的开始和结束时间
- **多文件存储**: 不同类型的数据分别存储，便于分析

### 前端埋点
- **澄清会话**: 自动追踪澄清对话的每一轮问答
- **错误恢复**: 检测用户路径偏离和恢复
- **状态管理**: 维护澄清会话和错误恢复的状态

### 分析工具
- **RQ3 评估脚本**: 专门分析信任和错误处理指标
- **会话分析**: 按实验会话分组分析性能
- **结果导出**: 生成 JSON 格式的评估报告

## 🚀 快速开始

### 1. 系统配置
```bash
# 设置低置信度阈值（触发澄清对话）
export LOWCONF_SCORE_TH=0.40
export LOWCONF_MARGIN_TH=0.07

# 启动系统
cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

### 2. 进行 RQ3 实验
1. 设置唯一的 `session_id`（如 "RQ3_Trust_Test"）
2. 输入 Ground Truth 节点 ID
3. 拍照定位，观察系统行为：
   - **基线条件**: 系统可能给出错误预测
   - **增强条件**: 低置信度时触发澄清对话
4. 如果走错路，记录错误恢复过程

### 3. 分析 RQ3 结果
```bash
# 运行 RQ3 评估
python tools/rq3_evaluation.py

# 或指定自定义日志文件
python tools/rq3_evaluation.py logs/locate_log.csv logs/clarification_log.csv logs/recovery_log.csv
```

## 📊 数据格式

### 定位日志 (locate_log.csv) - 新增 RQ3 字段
| 字段 | 描述 | 示例 |
|------|------|------|
| `misbelief` | 是否发生误信 | true/false |
| `clarification_triggered` | 是否触发澄清对话 | true/false |

### 澄清对话日志 (clarification_log.csv)
| 字段 | 描述 | 示例 |
|------|------|------|
| `clarification_id` | 澄清会话唯一 ID | a1b2c3d4e5f6 |
| `session_id` | 实验会话 ID | RQ3_Trust_Test |
| `round_count` | 当前轮次 | 1, 2, 3... |
| `user_question` | 用户问题 | "Where am I?" |
| `system_answer` | 系统回答 | "You are near the entrance" |
| `predicted_node` | 当前预测节点 | dp_ms_entrance |
| `gt_node_id` | 真实节点 | dp_ms_boxes |
| `clarification_success` | 澄清是否成功 | 1/0 |
| `total_rounds` | 总轮次 | 3 |

### 错误恢复日志 (recovery_log.csv)
| 字段 | 描述 | 示例 |
|------|------|------|
| `recovery_id` | 恢复会话唯一 ID | r1b2c3d4e5f6 |
| `session_id` | 实验会话 ID | RQ3_Trust_Test |
| `error_start_time` | 错误开始时间 | 1701432622123 |
| `error_end_time` | 错误结束时间 | 1701432625123 |
| `recovery_duration_ms` | 恢复时长(毫秒) | 3000 |
| `error_node` | 错误节点 | dp_ms_entrance |
| `correct_node` | 正确节点 | dp_ms_boxes |
| `recovery_path` | 恢复路径描述 | "Returned to correct path" |

## 🔧 实验设计

### 基线条件 (Baseline A)
- **目标**: 观察用户的过度信任行为
- **设置**: 系统可能给出错误预测，不主动触发澄清
- **测量**: 误信率 - 用户是否直接遵循错误指令

### 增强条件 (Enhanced B)
- **目标**: 测试澄清对话的有效性
- **设置**: 低置信度时自动触发澄清对话
- **测量**: 澄清轮次、成功率、错误恢复时长

### 实验流程
1. **准备阶段**: 设置实验参数，准备测试场景
2. **执行阶段**: 用户在不同位置拍照定位
3. **观察阶段**: 记录用户行为、系统响应、澄清对话
4. **分析阶段**: 运行 RQ3 评估脚本，分析结果

## 📈 指标解读

### 误信率评估
- **< 10%**: 优秀的信任管理
- **10-25%**: 良好的信任管理
- **> 25%**: 需要改进信任管理

### 澄清对话评估
- **成功率 ≥ 80%**: 优秀的澄清效果
- **成功率 60-80%**: 良好的澄清效果
- **成功率 < 60%**: 需要改进澄清策略

### 错误恢复评估
- **平均时间 < 5s**: 快速错误恢复
- **平均时间 5-15s**: 可接受的恢复时间
- **平均时间 > 15s**: 需要优化恢复流程

## 🔍 高级分析

### 会话级别分析
```bash
# 查看特定会话的 RQ3 指标
python tools/rq3_evaluation.py logs/locate_log.csv logs/clarification_log.csv logs/recovery_log.csv
```

### 自定义分析
```python
# 在 Python 中分析 RQ3 数据
import pandas as pd

# 读取澄清对话日志
clar_df = pd.read_csv("logs/clarification_log.csv")

# 分析澄清成功率
success_rate = clar_df[clar_df["clarification_success"] == 1].shape[0] / clar_df.shape[0]
print(f"Clarification success rate: {success_rate:.2%}")

# 分析澄清轮次分布
round_dist = clar_df.groupby("total_rounds").size()
print("Round distribution:", round_dist.to_dict())
```

### 对比分析
```bash
# 比较不同实验条件的 RQ3 表现
python tools/rq3_evaluation.py baseline_logs/locate_log.csv baseline_logs/clarification_log.csv baseline_logs/recovery_log.csv
python tools/rq3_evaluation.py enhanced_logs/locate_log.csv enhanced_logs/clarification_log.csv enhanced_logs/recovery_log.csv
```

## 🚨 故障排除

### 常见问题

#### 1. 澄清对话未记录
- 确认 `currentClarificationId` 状态正确设置
- 检查前端是否正确调用 `/api/metrics/clarification_round`
- 验证后端日志文件权限

#### 2. 错误恢复时间不准确
- 确认错误恢复的开始和结束时间点正确识别
- 检查 `startErrorRecovery` 和 `endErrorRecovery` 调用
- 验证时间戳格式和计算逻辑

#### 3. 误信率计算错误
- 确认 `gt_node_id` 正确设置
- 检查 `misbelief` 和 `clarification_triggered` 字段逻辑
- 验证预测错误检测逻辑

### 调试技巧
1. **检查前端状态**: 在浏览器控制台查看 RQ3 相关状态
2. **验证 API 调用**: 检查网络请求是否正确发送
3. **查看后端日志**: 确认数据记录函数的执行情况
4. **手动测试 API**: 使用 Postman 测试各个端点

## 📚 实验最佳实践

### 实验设计
1. **明确假设**: 定义信任和错误处理的研究假设
2. **控制变量**: 保持其他条件不变，只改变澄清策略
3. **随机化**: 随机化实验顺序和条件分配
4. **样本量**: 确保足够的样本量进行统计分析

### 数据收集
1. **一致性**: 保持实验流程的一致性
2. **完整性**: 确保所有必要的数据都被记录
3. **准确性**: 验证 Ground Truth 标签的准确性
4. **实时性**: 及时检查数据记录是否正常

### 结果分析
1. **多维度**: 从多个角度分析 RQ3 指标
2. **对比分析**: 比较不同实验条件的结果
3. **统计检验**: 使用适当的统计方法验证结果
4. **解释性**: 深入理解结果背后的原因

## 🚀 未来扩展

### 功能增强
- **实时监控**: Web 界面的实时 RQ3 指标显示
- **自动告警**: 异常信任行为时自动通知
- **趋势分析**: 长期信任行为趋势分析
- **个性化**: 基于用户特征的信任管理策略

### 集成选项
- **眼动追踪**: 结合眼动数据分析注意力模式
- **生理信号**: 集成心率、皮电等生理指标
- **行为分析**: 分析用户的操作序列和模式
- **机器学习**: 自动识别信任行为模式

---

**提示**: 这个 RQ3 系统为你的信任研究提供了完整的数据收集和分析能力。通过自动记录用户行为、系统响应和交互过程，你可以深入分析信任建立、维持和修复的机制，为设计更可信的 AI 系统提供数据支持。
