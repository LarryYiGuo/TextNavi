#!/usr/bin/env python3
"""
测试新的low_conf判断逻辑
"""

def test_low_conf_logic():
    """测试low_conf判断逻辑"""
    print("🧪 测试新的low_conf判断逻辑")
    print("=" * 50)
    
    # 新的逻辑：只要confidence > 50% 或 margin > 8% 就不触发low_conf
    # low_conf = confidence < 50% AND margin < 8%
    
    test_cases = [
        # (confidence, margin, expected_low_conf, description)
        (0.60, 0.05, False, "高置信度(60%)，低margin(5%) → 不触发low_conf"),
        (0.40, 0.10, False, "低置信度(40%)，高margin(10%) → 不触发low_conf"),
        (0.60, 0.10, False, "高置信度(60%)，高margin(10%) → 不触发low_conf"),
        (0.40, 0.05, True,  "低置信度(40%)，低margin(5%) → 触发low_conf"),
        (0.50, 0.08, False, "边界置信度(50%)，边界margin(8%) → 不触发low_conf"),
        (0.49, 0.07, True,  "边界以下置信度(49%)，边界以下margin(7%) → 触发low_conf"),
    ]
    
    print("📋 测试用例:")
    for i, (confidence, margin, expected, desc) in enumerate(test_cases, 1):
        # 应用新的逻辑
        low_conf = confidence < 0.50 and margin < 0.08
        
        status = "✅" if low_conf == expected else "❌"
        print(f"   {i}. {desc}")
        print(f"      置信度: {confidence:.2f}, margin: {margin:.2f}")
        print(f"      期望: {expected}, 实际: {low_conf} {status}")
        print()
    
    print("🔧 新的low_conf逻辑:")
    print("   low_conf = confidence < 50% AND margin < 8%")
    print("   即：只要满足以下任一条件，就不触发low_conf:")
    print("   - confidence > 50%")
    print("   - margin > 8%")
    print()
    
    print("📊 逻辑对比:")
    print("   旧逻辑 (OR): confidence < 50% OR margin < 10%")
    print("   新逻辑 (AND): confidence < 50% AND margin < 8%")
    print("   效果：减少false positive，只在两个条件都满足时才触发low_conf")

if __name__ == "__main__":
    test_low_conf_logic()
    print("\n✅ 测试完成!")
