# VLN4VI - Indoor Navigation System

## 项目概述 (Project Overview)

VLN4VI是一个基于视觉的室内导航系统，专为视障人士设计。该系统集成了先进的计算机视觉技术、语义理解和可访问性功能，提供准确、可靠的室内导航体验。

## 系统架构 (System Architecture)

```
VLN4VI/
├── backend/                 # 后端服务
│   ├── app.py              # 主应用文件
│   ├── database_optimization.py    # 数据库优化
│   ├── dg_evaluation_enhancement.py # DG评估增强
│   ├── user_needs_validator.py     # 用户需求验证
│   ├── accessibility_checker.py    # 可访问性检查
│   ├── indoor_gml_generator.py     # IndoorGML生成
│   ├── enhanced_metrics_collector.py # 增强指标收集
│   └── comprehensive_testing.py    # 综合测试
├── frontend/               # 前端界面
│   ├── src/
│   │   ├── App.jsx        # 主应用组件
│   │   └── frontend_optimization.jsx # 前端优化
│   └── package.json
├── start_system.py         # 系统启动脚本
└── README.md              # 项目说明文档
```

## 设计目标 (Design Goals)

系统基于六个核心设计目标 (DG1-DG6) 构建：

- **DG1**: 硬件依赖性最小化
- **DG2**: 语义地图构建
- **DG3**: 高精度定位
- **DG4**: 高质量指令生成
- **DG5**: 不确定性/信任管理
- **DG6**: 可访问性和可测试性

## 用户需求 (User Needs)

系统直接满足六个主要用户需求 (N1-N6)：

- **N1**: 拓扑地图需求
- **N2**: 定位精度需求
- **N3**: 分离指令需求
- **N4**: 低置信度处理需求
- **N5**: 可访问性需求
- **N6**: 标准化需求

## 快速开始 (Quick Start)

### 1. 环境要求 (Requirements)

- Python 3.8+
- Node.js 16+
- SQLite 3
- 现代浏览器支持

### 2. 安装依赖 (Install Dependencies)

#### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 3. 启动系统 (Start System)

使用一键启动脚本：
```bash
python start_system.py
```

或者手动启动：

#### 启动后端
```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### 启动前端
```bash
cd frontend
npm start
```

### 4. 访问系统 (Access System)

- 后端API: http://localhost:8000
- 前端界面: http://localhost:3000
- 健康检查: http://localhost:8000/health/enhanced
- API文档: http://localhost:8000/docs

## 核心功能 (Core Features)

### 1. 视觉定位 (Visual Localization)
- 基于照片的室内定位
- 置信度评估
- 多模态信息融合

### 2. 导航指令 (Navigation Instructions)
- 自然语言指令生成
- 语音合成支持
- 多语言支持

### 3. 可访问性 (Accessibility)
- WCAG 2.2 合规性
- VoiceOver 支持
- 高对比度模式
- 大字体模式

### 4. 指标收集 (Metrics Collection)
- 实时性能监控
- 用户行为分析
- 系统健康检查

### 5. 评估系统 (Evaluation System)
- DG目标评估
- 用户需求验证
- 性能指标分析

## API端点 (API Endpoints)

### 核心功能
- `POST /api/locate` - 位置识别
- `POST /api/qa` - 问答交互

### DG优化功能
- `POST /api/dg/metrics/collect` - 指标收集
- `POST /api/dg/evaluation/record` - 评估记录
- `POST /api/dg/accessibility/check` - 可访问性检查
- `POST /api/dg/indoor_gml/generate` - IndoorGML生成
- `POST /api/dg/user_needs/record` - 用户需求记录

### 数据管理
- `GET /api/dg/metrics/export/{session_id}` - 指标导出
- `GET /api/dg/metrics/analytics/{session_id}` - 分析报告
- `GET /api/dg/user_needs/matrix` - 需求矩阵

## 数据库结构 (Database Structure)

系统使用两个主要数据库：

### 主数据库 (Main Database)
- `dg_evaluations` - DG评估数据
- `user_needs_validation` - 用户需求验证
- `accessibility_tests` - 可访问性测试
- `indoor_gml_maps` - IndoorGML地图

### 指标数据库 (Metrics Database)
- `metrics` - 指标数据
- `sessions` - 会话管理
- `evaluation_metrics` - 评估指标
- `user_feedback` - 用户反馈

## 测试和验证 (Testing and Validation)

### 运行综合测试
```bash
cd backend
python comprehensive_testing.py
```

### 测试覆盖范围
- 基础连接性测试
- 数据库功能测试
- DG评估功能测试
- 用户需求验证测试
- 可访问性测试
- IndoorGML功能测试
- 性能测试
- 集成测试

## 配置选项 (Configuration)

### 环境变量
```bash
ENABLE_DG_EVALUATION=true
ENABLE_ACCESSIBILITY_CHECKING=true
ENABLE_INDOOR_GML=true
METRICS_STORAGE_PATH=./metrics_data
```

### 数据库配置
- 自动创建表结构
- 索引优化
- 性能监控

## 开发指南 (Development Guide)

### 代码结构
- 模块化设计
- 清晰的接口定义
- 完整的错误处理
- 详细的文档注释

### 添加新功能
1. 在相应模块中实现功能
2. 添加API端点
3. 更新数据库结构
4. 编写测试用例
5. 更新文档

### 代码规范
- 遵循PEP 8
- 使用类型提示
- 编写文档字符串
- 错误处理最佳实践

## 部署指南 (Deployment Guide)

### 生产环境
- 使用生产级Web服务器
- 配置反向代理
- 启用HTTPS
- 设置监控和日志

### Docker部署
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 故障排除 (Troubleshooting)

### 常见问题
1. **端口冲突**: 检查8000和3000端口是否被占用
2. **依赖缺失**: 确保所有Python包和Node模块已安装
3. **数据库错误**: 检查SQLite权限和文件路径
4. **前端启动失败**: 检查Node.js版本和npm配置

### 日志查看
- 后端日志: 控制台输出
- 前端日志: 浏览器开发者工具
- 数据库日志: SQLite日志文件

## 贡献指南 (Contributing)

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证 (License)

本项目采用MIT许可证。

## 联系方式 (Contact)

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [GitHub Repository URL]

## 更新日志 (Changelog)

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 完整的DG优化功能
- 综合测试套件
- 一键启动脚本

---

**注意**: 这是一个开发中的项目，某些功能可能仍在开发中。请查看最新的提交记录了解最新状态。
