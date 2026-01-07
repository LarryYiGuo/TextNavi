#!/usr/bin/env python3
"""
测试新的导航询问行为：基于拍照状态智能响应
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_navigation_inquiry_behavior():
    """测试新的导航询问行为"""
    print("🧪 测试新的导航询问行为")
    print("=" * 60)
    
    print("📋 修改内容总结:")
    print("1. ✅ 拍照后不再自动播报位置信息")
    print("2. ✅ 第一次问'where am I?'时播报预设输出")
    print("3. ✅ 第二次问'where am I?'时要求拍照确认")
    print("4. ✅ 新增：智能处理'how should I go'询问")
    print("5. ✅ 基于拍照状态给出不同响应")
    
    print("\n🔍 新增的导航询问检测:")
    print("1. 关键词检测:")
    print("   - 'how should i go'")
    print("   - 'how do i go'")
    print("   - 'how can i go'")
    print("   - 'navigate'")
    print("   - 'direction'")
    print("   - 'way'")
    print("   - 'route'")
    
    print("\n2. 智能响应逻辑:")
    print("   - 有拍照内容 → 基于照片给出具体导航建议")
    print("   - 无拍照内容 → 给出通用导航指导")
    
    print("\n🎯 具体行为:")
    print("1. 问'how should I go'时:")
    print("   - 有拍照: 'Based on your photos, you're at X. From here, you can...'")
    print("   - 无拍照: 'To proceed effectively, focus on moving towards...'")
    
    print("\n2. 场景特定导航建议:")
    print("   - SCENE_A_MS: 3D打印机区域、中庭区域的具体指导")
    print("   - SCENE_B_STUDIO: 工作站区域、玻璃会议室的指导")
    
    print("\n🧪 测试建议:")
    print("1. 不拍照问'how should I go?' → 通用导航指导")
    print("2. 拍照后问'how should I go?' → 基于照片的具体建议")
    print("3. 观察console日志中的导航询问检测信息")

if __name__ == "__main__":
    test_navigation_inquiry_behavior()
    print("\n✅ 测试完成!")
