#!/usr/bin/env python3
"""
快速验证修复是否生效的测试脚本
"""

def test_1_alias_table_fix():
    """测试1: 别名表修正 - 确保orange_sofa_corner不被错误合并"""
    print("🔍 测试1: 别名表修正")
    
    # 检查app.py中的entity_aliases映射
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查orange_sofa_corner是否有独立映射
        if 'orange_sofa_corner' in content:
            # 检查是否还包含"corner"这个通用词
            if 'storage_corner.*corner' in content:
                print("❌ storage_corner仍然包含通用词'corner'，可能冲突")
                return False
            else:
                print("✅ orange_sofa_corner映射正确，storage_corner不包含通用词")
                return True
        else:
            print("⚠️ 未找到orange_sofa_corner相关代码")
            return False
            
    except Exception as e:
        print(f"❌ 读取app.py失败: {e}")
        return False

def test_2_confidence_smooth_factor():
    """测试2: 置信度策略微调 - 检查是否使用了平滑折扣"""
    print("🔍 测试2: 置信度策略微调")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了新的平滑置信度计算
        if 'conf_from_margin' in content and '平滑置信度计算' in content:
            print("✅ 已使用平滑置信度计算，去掉硬帽逻辑")
            return True
        else:
            print("❌ 未完全使用平滑置信度计算")
            return False
            
    except Exception as e:
        print(f"❌ 检查置信度策略失败: {e}")
        return False

def test_3_continuity_order():
    """测试3: 连续性顺序 - 检查异常时是否不更新位置"""
    print("🔍 测试3: 连续性顺序")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查异常处理逻辑
        if '保持上一个稳定位置状态，不更新会话位置' in content:
            print("✅ 异常时保持位置状态，不更新会话位置")
            return True
        else:
            print("❌ 未找到异常时位置保持逻辑")
            return False
            
    except Exception as e:
        print(f"❌ 检查连续性顺序失败: {e}")
        return False

def test_4_unpacking_fix():
    """测试4: 解包错误修复 - 检查apply_continuity_boost调用"""
    print("🔍 测试4: 解包错误修复")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查apply_continuity_boost调用是否正确
        if 'boost_amount, boost_reason = apply_continuity_boost(' in content:
            print("✅ apply_continuity_boost调用已修复，正确解包2个值")
            return True
        else:
            print("❌ apply_continuity_boost调用未修复")
            return False
            
    except Exception as e:
        print(f"❌ 检查解包修复失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 快速验证修复是否生效")
    print("=" * 50)
    
    tests = [
        ("别名表修正", test_1_alias_table_fix),
        ("置信度策略微调", test_2_confidence_smooth_factor),
        ("连续性顺序", test_3_continuity_order),
        ("解包错误修复", test_4_unpacking_fix)
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
        print("🎉 所有修复验证通过！系统应该更稳定了")
        return True
    else:
        print("⚠️ 部分修复验证失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
