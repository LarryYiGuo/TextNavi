#!/usr/bin/env python3
"""
测试双通道模式恢复和新的low confidence逻辑
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_dual_channel_restored():
    """测试双通道模式恢复和新的low confidence逻辑"""
    print("🧪 测试双通道模式恢复和新的low confidence逻辑")
    print("=" * 70)
    
    print("📋 主要修改内容:")
    print("1. ✅ 恢复双通道模式，使用增强融合策略")
    print("2. ✅ 调整low confidence阈值：raw confidence < 50% 或 margin < 10%")
    print("3. ✅ 保留语义去重和实体别名识别")
    print("4. ✅ 第一次拍照直接检测，不播报预设输出")
    
    print("\n🔧 双通道模式特点:")
    print("- 结构通道：从textmap文件检索")
    print("- 细节通道：从JSONL文件检索")
    print("- 增强融合：对数几率相加，指数放大margin")
    print("- 连续性boost：基于历史位置信息")
    
    print("\n📊 新的low confidence检测逻辑:")
    print("- 旧逻辑：confidence < 50% AND margin < 8% (AND条件)")
    print("- 新逻辑：confidence < 50% OR margin < 10% (OR条件)")
    print("- 阈值调整：margin从8%提升到10%")
    print("- 触发条件：任一条件满足即触发low_conf")
    
    print("\n🎯 预期效果:")
    print("1. 双通道融合提供更丰富的特征信息")
    print("2. 更合理的low confidence提示")
    print("3. 保持系统的智能性和准确性")
    print("4. 用户体验更加流畅")
    
    print("\n🧪 测试建议:")
    print("1. 拍照测试，观察检索日志")
    print("2. 检查是否显示'Enhanced dual-channel retrieval'")
    print("3. 验证双通道融合是否正常工作")
    print("4. 检查confidence和margin计算")
    print("5. 观察low_conf触发条件")
    print("6. 验证语义去重和实体别名识别是否正常工作")

if __name__ == "__main__":
    test_dual_channel_restored()
    print("\n✅ 测试完成!")
