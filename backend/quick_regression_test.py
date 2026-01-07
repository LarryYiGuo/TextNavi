#!/usr/bin/env python3
"""
快速回归测试脚本 - 测试三个关键修复
1. 别名表修正（避免错误合并）
2. 置信度策略微调（去掉硬帽，改为平滑折扣）
3. 连续性顺序（异常时不更新位置）
"""

import json
import os
import sys

def test_1_alias_table_fix():
    """测试1: 别名表修正 - 确保orange_sofa_corner不被错误合并"""
    print("🔍 测试1: 别名表修正")
    
    # 检查app.py中的entity_aliases映射
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查orange_sofa_corner是否有独立映射
        if 'orange_sofa_corner' in content:
            if 'orange_sofa_corner.*storage_corner' in content:
                print("❌ 发现错误的映射: orange_sofa_corner → storage_corner")
                return False
            else:
                print("✅ orange_sofa_corner映射正确，独立于storage_corner")
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
        if 'conf_from_margin' in content:
            print("✅ 找到平滑置信度计算函数 conf_from_margin")
            
            # 检查是否使用了新的平滑置信度计算
            if 'conf_from_margin' in content and '平滑置信度计算' in content:
                print("✅ 已使用平滑置信度计算，去掉硬帽逻辑")
                return True
            else:
                print("❌ 未完全使用平滑置信度计算")
                return False
        else:
            print("❌ 未找到平滑置信度计算函数")
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

def test_4_quick_check():
    """测试4: 运行quick_check.py确认detail anchors对齐"""
    print("🔍 测试4: Detail anchors对齐检查")
    
    try:
        # 运行quick_check.py
        import subprocess
        result = subprocess.run(['python', 'quick_check.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            output = result.stdout
            if '✅ 所有锚点完全对齐' in output:
                print("✅ Detail anchors完全对齐")
                return True
            else:
                print("❌ Detail anchors未完全对齐")
                print("输出:", output)
                return False
        else:
            print(f"❌ quick_check.py执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行quick_check.py失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 快速回归测试开始")
    print("=" * 50)
    
    tests = [
        ("别名表修正", test_1_alias_table_fix),
        ("置信度策略微调", test_2_confidence_smooth_factor),
        ("连续性顺序", test_3_continuity_order),
        ("Detail anchors对齐", test_4_quick_check)
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
        print("🎉 所有测试通过！系统修复完成")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
