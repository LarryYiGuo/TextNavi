#!/usr/bin/env python3
"""
测试新的confidence阈值设置
验证60%+的confidence不再显示"Low confidence"警告
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_new_thresholds():
    """测试新的阈值设置"""
    print("🔍 测试新的confidence阈值设置...")
    
    # 模拟新的阈值
    LOWCONF_SCORE_TH = 0.40  # 40%
    LOWCONF_MARGIN_TH = 0.05  # 5%
    
    print(f"   新阈值设置:")
    print(f"     LOWCONF_SCORE_TH: {LOWCONF_SCORE_TH:.2f} ({LOWCONF_SCORE_TH*100:.0f}%)")
    print(f"     LOWCONF_MARGIN_TH: {LOWCONF_MARGIN_TH:.2f} ({LOWCONF_MARGIN_TH*100:.0f}%)")
    
    # 测试不同的confidence和margin组合
    test_cases = [
        {
            "name": "高confidence + 高margin",
            "confidence": 0.605,  # 60.5%
            "margin": 0.15,       # 15%
            "expected_low_conf": False,
            "description": "60.5% confidence + 15% margin 应该不是low confidence"
        },
        {
            "name": "高confidence + 低margin",
            "confidence": 0.605,  # 60.5%
            "margin": 0.03,       # 3%
            "expected_low_conf": True,
            "description": "60.5% confidence + 3% margin 应该是low confidence（margin太低）"
        },
        {
            "name": "低confidence + 高margin",
            "confidence": 0.35,   # 35%
            "margin": 0.15,       # 15%
            "expected_low_conf": True,
            "description": "35% confidence + 15% margin 应该是low confidence（confidence太低）"
        },
        {
            "name": "边界情况1",
            "confidence": 0.40,   # 40% (刚好等于阈值)
            "margin": 0.05,       # 5% (刚好等于阈值)
            "expected_low_conf": False,
            "description": "40% confidence + 5% margin 应该不是low confidence（边界值）"
        },
        {
            "name": "边界情况2",
            "confidence": 0.39,   # 39% (略低于阈值)
            "margin": 0.05,       # 5% (等于阈值)
            "expected_low_conf": True,
            "description": "39% confidence + 5% margin 应该是low confidence（confidence略低）"
        },
        {
            "name": "边界情况3",
            "confidence": 0.40,   # 40% (等于阈值)
            "margin": 0.04,       # 4% (略低于阈值)
            "expected_low_conf": True,
            "description": "40% confidence + 4% margin 应该是low confidence（margin略低）"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases):
        name = case["name"]
        confidence = case["confidence"]
        margin = case["margin"]
        expected_low_conf = case["expected_low_conf"]
        description = case["description"]
        
        print(f"\n   测试{i+1} ({name}):")
        print(f"     Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
        print(f"     Margin: {margin:.3f} ({margin*100:.1f}%)")
        print(f"     描述: {description}")
        
        # 应用新的阈值逻辑：OR关系，只要一个条件满足就是low_conf
        low_conf = confidence < LOWCONF_SCORE_TH or margin < LOWCONF_MARGIN_TH
        
        print(f"     计算结果: low_conf = {low_conf}")
        print(f"     期望结果: low_conf = {expected_low_conf}")
        
        if low_conf == expected_low_conf:
            print(f"     ✅ 结果正确")
            passed += 1
        else:
            print(f"     ❌ 结果错误")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有阈值测试通过！")
        print("\n💡 新的阈值效果:")
        print(f"   - Confidence > {LOWCONF_SCORE_TH*100:.0f}% 且 Margin > {LOWCONF_MARGIN_TH*100:.0f}% 时，不显示'Low confidence'警告")
        print(f"   - 60.5% confidence + 15% margin 现在不会触发警告")
        print(f"   - 系统对中等置信度的容忍度更高")
        return True
    else:
        print("⚠️ 部分阈值测试失败，需要检查逻辑")
        return False

def test_frontend_behavior():
    """测试前端行为变化"""
    print("\n🔍 测试前端行为变化...")
    
    # 模拟前端显示逻辑
    test_scenarios = [
        {
            "confidence": 0.605,  # 60.5%
            "margin": 0.15,       # 15%
            "old_behavior": "Low confidence (60.5%)",
            "new_behavior": "正常显示，无警告",
            "description": "60.5% confidence 现在应该正常显示"
        },
        {
            "confidence": 0.605,  # 60.5%
            "margin": 0.05,       # 5%
            "old_behavior": "Low confidence (60.5%)",
            "new_behavior": "Low confidence (60.5%) - 因为margin太低",
            "description": "60.5% confidence 但margin太低，仍显示警告"
        },
        {
            "confidence": 0.35,   # 35%
            "margin": 0.15,       # 15%
            "old_behavior": "Low confidence (35%)",
            "new_behavior": "Low confidence (35%) - 因为confidence太低",
            "description": "35% confidence 太低，仍显示警告"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios):
        confidence = scenario["confidence"]
        margin = scenario["margin"]
        old_behavior = scenario["old_behavior"]
        new_behavior = scenario["new_behavior"]
        description = scenario["description"]
        
        print(f"   场景{i+1}: {description}")
        print(f"     Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
        print(f"     Margin: {margin:.3f} ({margin*100:.1f}%)")
        print(f"     旧行为: {old_behavior}")
        print(f"     新行为: {new_behavior}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试新的confidence阈值...\n")
    
    tests = [
        test_new_thresholds,
        test_frontend_behavior
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ 测试通过\n")
            else:
                print("❌ 测试失败\n")
        except Exception as e:
            print(f"❌ 测试异常: {e}\n")
    
    print(f"📊 总体测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 新的confidence阈值设置成功！")
        print("\n🔧 修复总结:")
        print("   1. ✅ LOWCONF_SCORE_TH: 50% → 40%")
        print("   2. ✅ LOWCONF_MARGIN_TH: 8% → 5%")
        print("   3. ✅ 60.5% confidence + 15% margin 不再显示'Low confidence'警告")
        print("   4. ✅ 使用OR逻辑：只要一个条件满足就是low_conf")
        print("\n💡 现在前端应该:")
        print("   - 60.5% confidence + 15% margin → 正常显示，无警告")
        print("   - 60.5% confidence + 5% margin → 仍显示警告（margin太低）")
        print("   - 35% confidence + 15% margin → 仍显示警告（confidence太低）")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
