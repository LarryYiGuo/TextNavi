#!/bin/bash

# 🔧 置信度修复启动脚本
# 这个脚本会设置正确的环境变量并启动后端服务

echo "🚀 启动VLN4VI后端服务（置信度修复版本）"
echo "=================================================="

# 设置环境变量
export SOFTMAX_TEMPERATURE=0.06
export ENABLE_SOFTMAX_CALIBRATION=true
export ENABLE_CONTINUITY_BOOST=true
export LOWCONF_SCORE_TH=0.45
export LOWCONF_MARGIN_TH=0.08

echo "✅ 环境变量已设置:"
echo "   SOFTMAX_TEMPERATURE: $SOFTMAX_TEMPERATURE"
echo "   ENABLE_SOFTMAX_CALIBRATION: $ENABLE_SOFTMAX_CALIBRATION"
echo "   ENABLE_CONTINUITY_BOOST: $ENABLE_CONTINUITY_BOOST"
echo "   LOWCONF_SCORE_TH: $LOWCONF_SCORE_TH"
echo "   LOWCONF_MARGIN_TH: $LOWCONF_MARGIN_TH"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "🔍 检查Python依赖..."
python -c "import sentence_transformers, dual_channel_retrieval" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install sentence-transformers
fi

# 运行测试
echo "🧪 运行置信度修复测试..."
python test_confidence_fix.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 测试通过！现在启动后端服务..."
    echo "=================================================="
    echo "📱 前端访问: https://172.20.10.3:5173"
    echo "🔧 后端API: http://172.20.10.3:8001"
    echo "📊 健康检查: http://172.20.10.3:8001/health"
    echo ""
    echo "💡 拍照测试时，查看控制台输出的校准信息:"
    echo "   🔧 Softmax calibration applied:"
    echo "   🔧 Continuity boost applied:"
    echo ""
    
    # 启动服务
    uvicorn app:app --reload --host 0.0.0.0 --port 8001
else
    echo "❌ 测试失败，请检查错误信息"
    exit 1
fi
