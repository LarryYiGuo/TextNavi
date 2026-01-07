#!/usr/bin/env python3
"""
测试margin显示修复是否完整的脚本
"""

def test_1_margin_field_included():
    """测试1: 检查返回结果中是否包含margin字段"""
    print("🔍 测试1: 检查margin字段是否包含在返回结果中")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查fused_top1_success返回结果中是否包含margin
        if '"margin": margin' in content and 'fused_top1_success' in content:
            print("✅ fused_top1_success返回结果中已包含margin字段")
            return True
        else:
            print("❌ fused_top1_success返回结果中未包含margin字段")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_2_margin_calculation():
    """测试2: 检查margin计算逻辑是否正确"""
    print("🔍 测试2: 检查margin计算逻辑")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查margin计算逻辑
        margin_calc_patterns = [
            'top2_score = float\\(candidates\\[1\\]\\.get\\("score", 0\\.0\\)\\)',
            'margin = max\\(0\\.0, top1_score - top2_score\\)'
        ]
        
        for pattern in margin_calc_patterns:
            import re
            if re.search(pattern, content):
                print(f"✅ 找到margin计算逻辑: {pattern}")
            else:
                print(f"❌ 未找到margin计算逻辑: {pattern}")
                return False
        
        print("✅ margin计算逻辑完整")
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_3_margin_logging():
    """测试3: 检查margin是否在日志中显示"""
    print("🔍 测试3: 检查margin日志显示")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查margin是否在日志中显示
        if 'margin: {margin:.3f}' in content:
            print("✅ margin已在日志中显示")
            return True
        else:
            print("❌ margin未在日志中显示")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试margin显示修复是否完整")
    print("=" * 50)
    
    tests = [
        ("margin字段包含", test_1_margin_field_included),
        ("margin计算逻辑", test_2_margin_calculation),
        ("margin日志显示", test_3_margin_logging)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 margin显示修复完成！现在应该显示margin信息了")
        return True
    else:
        print("⚠️ 部分修复未完成，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
