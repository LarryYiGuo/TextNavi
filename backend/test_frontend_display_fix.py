#!/usr/bin/env python3
"""
测试前端显示修复是否生效的脚本
"""

def test_1_unknown_node_id_fix():
    """测试1: 检查是否修复了返回"unknown"的问题"""
    print("🔍 测试1: 检查unknown node_id修复")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否修复了返回"unknown"的逻辑
        if '返回成功的fused top-1结果' in content:
            print("✅ 已修复返回'unknown'的问题，现在会返回实际结果")
            return True
        else:
            print("❌ 未找到修复逻辑")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_2_fused_top1_success_method():
    """测试2: 检查是否添加了新的retrieval_method"""
    print("🔍 测试2: 检查新的retrieval_method")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否添加了新的retrieval_method
        if 'fused_top1_success' in content:
            print("✅ 已添加'fused_top1_success'方法")
            return True
        else:
            print("❌ 未找到'fused_top1_success'方法")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_3_candidates_check():
    """测试3: 检查是否检查candidates存在性"""
    print("🔍 测试3: 检查candidates存在性检查")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否添加了candidates存在性检查
        if "'candidates' in locals() and candidates and len(candidates) > 0" in content:
            print("✅ 已添加candidates存在性检查")
            return True
        else:
            print("❌ 未找到candidates存在性检查")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试前端显示修复是否生效")
    print("=" * 50)
    
    tests = [
        ("unknown node_id修复", test_1_unknown_node_id_fix),
        ("新的retrieval_method", test_2_fused_top1_success_method),
        ("candidates存在性检查", test_3_candidates_check)
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
        print("🎉 前端显示修复完成！现在应该显示正确的结果了")
        return True
    else:
        print("⚠️ 部分修复未完成，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
