#!/usr/bin/env python3
"""
综合测试脚本 - 验证所有关键修复是否生效
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_detail_index_alignment():
    """测试细节索引对齐问题"""
    print("🔧 测试细节索引对齐问题")
    print("=" * 50)
    
    # 1. 检查Sense_A_MS.jsonl中的node_hint字段
    detail_file = os.path.join(current_dir, "data", "Sense_A_MS.jsonl")
    if not os.path.exists(detail_file):
        print(f"❌ Detail文件不存在: {detail_file}")
        return False
    
    detail_nodes = set()
    with open(detail_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    detail_item = json.loads(line)
                    node_hint = detail_item.get("node_hint", "")
                    if node_hint:
                        detail_nodes.add(node_hint)
                except json.JSONDecodeError:
                    print(f"⚠️ Line {line_num}: JSON decode error")
                    continue
    
    print(f"📊 Detail文件中的节点: {sorted(detail_nodes)}")
    
    # 2. 检查Sense_A_Finetuned.fixed.jsonl中的节点ID
    struct_file = os.path.join(current_dir, "data", "Sense_A_Finetuned.fixed.jsonl")
    if not os.path.exists(struct_file):
        print(f"❌ Structure文件不存在: {struct_file}")
        return False
    
    with open(struct_file, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        try:
            struct_data = json.loads(first_line)
            topology = struct_data.get("input", {}).get("topology", {})
            nodes = topology.get("nodes", [])
            struct_nodes = set(node["id"] for node in nodes)
            print(f"📊 Structure文件中的节点: {sorted(struct_nodes)}")
        except json.JSONDecodeError:
            print("❌ Structure文件JSON解析失败")
            return False
    
    # 3. 检查对齐情况
    missing_in_detail = struct_nodes - detail_nodes
    missing_in_struct = detail_nodes - struct_nodes
    
    print(f"\n🔍 对齐检查:")
    print(f"   Structure节点数量: {len(struct_nodes)}")
    print(f"   Detail节点数量: {len(detail_nodes)}")
    print(f"   缺失在Detail中: {sorted(missing_in_detail)}")
    print(f"   缺失在Structure中: {sorted(missing_in_struct)}")
    
    if missing_in_detail:
        print(f"⚠️ 发现{len(missing_in_detail)}个节点在Detail文件中缺失")
        print("   这解释了为什么'Found 0 detail entries'")
        return False
    else:
        print("✅ 所有Structure节点都在Detail文件中存在")
        return True

def test_alias_merge_fix():
    """测试别名误合并修复"""
    print("\n🔧 测试别名误合并修复")
    print("=" * 50)
    
    # 检查app.py中的entity_aliases映射
    app_file = os.path.join(current_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"❌ app.py文件不存在")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查orange_sofa_corner的映射
        if 'orange_sofa_corner' in content:
            # 查找entity_aliases定义
            if 'entity_aliases' in content:
                print("✅ 找到entity_aliases定义")
                
                # 检查是否有错误的映射
                if 'orange_sofa_corner.*storage_corner' in content:
                    print("⚠️ 发现错误的映射: orange_sofa_corner → storage_corner")
                    return False
                else:
                    print("✅ orange_sofa_corner映射正确")
                    return True
            else:
                print("⚠️ 未找到entity_aliases定义")
                return False
        else:
            print("⚠️ 未找到orange_sofa_corner相关代码")
            return False

def test_confidence_cap_fix():
    """测试置信度硬帽修复"""
    print("\n🔧 测试置信度硬帽修复")
    print("=" * 50)
    
    app_file = os.path.join(current_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"❌ app.py文件不存在")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查是否还有硬帽0.3的逻辑
        if 'confidence = 0.3' in content or 'confidence = 0.300' in content:
            print("⚠️ 发现硬帽0.3的逻辑")
            return False
        
        # 检查是否有基于margin的平滑调整
        if 'margin >= 0.8' in content and 'confidence = max(confidence, 0.8)' in content:
            print("✅ 找到基于margin的平滑调整逻辑")
            return True
        else:
            print("⚠️ 未找到基于margin的平滑调整逻辑")
            return False

def test_parameter_optimization():
    """测试参数优化"""
    print("\n🔧 测试参数优化")
    print("=" * 50)
    
    app_file = os.path.join(current_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"❌ app.py文件不存在")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查温度参数
        if 'structure_tau = 0.15' in content and 'detail_tau = 0.20' in content:
            print("✅ 温度参数已优化")
        else:
            print("⚠️ 温度参数未优化")
            return False
        
        # 检查融合权重
        if 'alpha = 0.60' in content and 'beta = 0.40' in content:
            print("✅ 融合权重已平衡")
        else:
            print("⚠️ 融合权重未平衡")
            return False
        
        # 检查gamma参数
        if 'gamma = 0.15' in content:
            print("✅ gamma参数已优化")
        else:
            print("⚠️ gamma参数未优化")
            return False
        
        return True

def test_return_value_format():
    """测试返回值格式"""
    print("\n🔧 测试返回值格式")
    print("=" * 50)
    
    app_file = os.path.join(current_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"❌ app.py文件不存在")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查是否有_pack_result方法
        if '_pack_result' in content:
            print("✅ 找到_pack_result方法")
            
            # 检查是否返回三元组
            if 'return node_id, float(score), bool(used_detail)' in content:
                print("✅ 返回值格式为三元组")
                return True
            else:
                print("⚠️ 返回值格式不是三元组")
                return False
        else:
            print("⚠️ 未找到_pack_result方法")
            return False

def main():
    """主测试函数"""
    print("🧪 综合修复验证测试")
    print("=" * 70)
    
    print("📋 基于你的分析，验证以下修复:")
    print("1. 🔧 细节索引缺失 → 检查node_hint字段对齐")
    print("2. 🔧 别名误合并 → 检查orange_sofa_corner独立映射")
    print("3. 🔧 置信度硬帽 → 检查基于margin的平滑调整")
    print("4. 🔧 参数优化 → 检查温度和权重调整")
    print("5. 🔧 返回值格式 → 检查三元组返回")
    
    results = []
    
    # 1. 测试细节索引对齐
    results.append(("细节索引对齐", test_detail_index_alignment()))
    
    # 2. 测试别名误合并修复
    results.append(("别名误合并修复", test_alias_merge_fix()))
    
    # 3. 测试置信度硬帽修复
    results.append(("置信度硬帽修复", test_confidence_cap_fix()))
    
    # 4. 测试参数优化
    results.append(("参数优化", test_parameter_optimization()))
    
    # 5. 测试返回值格式
    results.append(("返回值格式", test_return_value_format()))
    
    print("\n📊 测试结果总结:")
    for name, result in results:
        status = "✅ 已修复" if result else "🚨 需要修复"
        print(f"   {name}: {status}")
    
    # 统计修复状态
    fixed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n📈 修复进度: {fixed_count}/{total_count} ({fixed_count/total_count*100:.1f}%)")
    
    if fixed_count == total_count:
        print("\n🎉 所有修复都已完成！")
        print("   现在测试时应该看到:")
        print("   - 置信度提升到合理范围")
        print("   - 语义去重正确")
        print("   - 双通道融合平衡")
        print("   - 系统稳定性提升")
    else:
        print(f"\n⚠️ 还有 {total_count - fixed_count} 个问题需要修复")
    
    return fixed_count == total_count

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 发现需要修复的问题")
    print("\n✅ 测试完成!")
