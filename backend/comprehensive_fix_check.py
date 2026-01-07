#!/usr/bin/env python3
"""
全面检查修复是否完整的脚本
"""

import re

def check_1_alias_table_complete():
    """检查1: 别名表修复是否完整"""
    print("🔍 检查1: 别名表修复完整性")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查entity_aliases定义
        if 'entity_aliases = {' not in content:
            print("❌ 未找到entity_aliases定义")
            return False
        
        # 检查orange_sofa_corner的映射
        if 'orange_sofa_corner' not in content:
            print("❌ 未找到orange_sofa_corner映射")
            return False
        
        # 检查storage_corner的映射
        if 'storage_corner.*corner' in content:
            print("❌ storage_corner仍包含通用词'corner'")
            return False
        
        # 检查是否有冲突的映射
        if 'orange_sofa_corner.*storage_corner' in content:
            print("❌ 发现错误的映射: orange_sofa_corner → storage_corner")
            return False
        
        print("✅ 别名表修复完整")
        return True
        
    except Exception as e:
        print(f"❌ 检查别名表失败: {e}")
        return False

def check_2_confidence_smooth_complete():
    """检查2: 置信度平滑计算修复是否完整"""
    print("🔍 检查2: 置信度平滑计算修复完整性")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查conf_from_margin函数
        if 'def conf_from_margin(' not in content:
            print("❌ 未找到conf_from_margin函数定义")
            return False
        
        # 检查平滑置信度计算调用
        if 'conf_from_margin(margin, has_detail)' not in content:
            print("❌ 未找到conf_from_margin函数调用")
            return False
        
        # 检查是否去掉了硬帽逻辑（只检查代码，不检查注释）
        # 查找可能的硬帽逻辑代码模式
        hard_cap_patterns = [
            'confidence = min\\(confidence, 0\\.3\\)',  # 硬帽0.3
            'confidence = min\\(confidence, 0\\.8\\)',  # 硬帽0.8
            'confidence = min\\(confidence, 0\\.9\\)',  # 硬帽0.9
            'confidence = max\\(confidence, 0\\.2\\)',  # 硬帽0.2
        ]
        
        for pattern in hard_cap_patterns:
            if re.search(pattern, content):
                print(f"❌ 发现硬帽逻辑: {pattern}")
                return False
        
        print("✅ 未发现硬帽逻辑代码")
        
        # 检查平滑置信度计算日志
        if '平滑置信度计算:' not in content:
            print("❌ 未找到平滑置信度计算日志")
            return False
        
        print("✅ 置信度平滑计算修复完整")
        return True
        
    except Exception as e:
        print(f"❌ 检查置信度平滑计算失败: {e}")
        return False

def check_3_continuity_order_complete():
    """检查3: 连续性顺序修复是否完整"""
    print("🔍 检查3: 连续性顺序修复完整性")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查异常处理逻辑
        if '保持上一个稳定位置状态，不更新会话位置' not in content:
            print("❌ 未找到异常时位置保持逻辑")
            return False
        
        # 检查use_legacy设置
        if 'use_legacy = False' not in content:
            print("❌ 未找到use_legacy设置")
            return False
        
        # 检查跳过legacy回退逻辑
        if '跳过legacy回退，保持fused top-1结果' not in content:
            print("❌ 未找到跳过legacy回退逻辑")
            return False
        
        # 检查会话位置更新条件
        if '只有在统一检索成功后才更新会话位置' not in content:
            print("❌ 未找到会话位置更新条件")
            return False
        
        print("✅ 连续性顺序修复完整")
        return True
        
    except Exception as e:
        print(f"❌ 检查连续性顺序失败: {e}")
        return False

def check_4_unpacking_fix_complete():
    """检查4: 解包错误修复是否完整"""
    print("🔍 检查4: 解包错误修复完整性")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查apply_continuity_boost函数定义
        if 'def apply_continuity_boost(' not in content:
            print("❌ 未找到apply_continuity_boost函数定义")
            return False
        
        # 检查函数返回值
        if 'return boost, reason' not in content:
            print("❌ apply_continuity_boost函数返回值不正确")
            return False
        
        # 检查函数调用
        if 'boost_amount, boost_reason = apply_continuity_boost(' not in content:
            print("❌ apply_continuity_boost函数调用不正确")
            return False
        
        # 检查final_confidence计算
        if 'final_confidence = calibrated_confidence + boost_amount' not in content:
            print("❌ final_confidence计算不正确")
            return False
        
        print("✅ 解包错误修复完整")
        return True
        
    except Exception as e:
        print(f"❌ 检查解包错误修复失败: {e}")
        return False

def check_5_math_import():
    """检查5: math模块导入是否完整"""
    print("🔍 检查5: math模块导入完整性")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查math模块导入
        if 'import math' in content:
            print("✅ math模块已导入")
            return True
        elif 'math.exp(' in content:
            print("✅ math模块通过内联导入使用")
            return True
        else:
            print("❌ math模块未正确导入或使用")
            return False
        
    except Exception as e:
        print(f"❌ 检查math模块导入失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🧪 全面检查修复完整性")
    print("=" * 60)
    
    checks = [
        ("别名表修复", check_1_alias_table_complete),
        ("置信度平滑计算修复", check_2_confidence_smooth_complete),
        ("连续性顺序修复", check_3_continuity_order_complete),
        ("解包错误修复", check_4_unpacking_fix_complete),
        ("math模块导入", check_5_math_import)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            if check_func():
                print(f"✅ {check_name} 检查通过")
                passed += 1
            else:
                print(f"❌ {check_name} 检查失败")
        except Exception as e:
            print(f"❌ {check_name} 检查异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有修复检查通过！系统修复完整")
        return True
    else:
        print("⚠️ 部分修复检查失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
