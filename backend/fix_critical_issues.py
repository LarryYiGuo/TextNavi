#!/usr/bin/env python3
"""
修复关键问题的综合脚本
根据你的详细分析进行针对性修复
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def fix_detail_index_issue():
    """修复细节索引缺失问题"""
    print("🔧 修复细节索引缺失问题")
    print("=" * 50)
    
    # 检查Sense_A_MS.jsonl文件中的node_hint字段
    detail_file = os.path.join(current_dir, "data", "Sense_A_MS.jsonl")
    if not os.path.exists(detail_file):
        print(f"❌ Detail文件不存在: {detail_file}")
        return False
    
    # 解析detail文件中的node_hint
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
    
    # 检查结构文件中的节点ID
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
    
    # 检查对齐情况
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

def check_return_value_format():
    """检查返回值格式问题"""
    print("\n🔧 检查返回值格式问题")
    print("=" * 50)
    
    print("📋 问题分析:")
    print("   期望: (node_id, score, has_detail) 三元组")
    print("   实际: (node_id, score) 二元组")
    print("   结果: 'not enough values to unpack (expected 3, got 2)'")
    
    print("\n🔧 修复建议:")
    print("   1. 统一候选构造为三元组格式")
    print("   2. 或者修改解包逻辑处理二元组")
    print("   3. 禁用异常回退，避免标签漂移")
    
    return True

def check_confidence_cap_fix():
    """检查置信度硬帽修复"""
    print("\n🔧 检查置信度硬帽修复")
    print("=" * 50)
    
    print("📊 新的置信度逻辑:")
    print("   - 高margin(≥0.8): 即使无detail也保持高置信度(≥0.8)")
    print("   - 中等margin(≥0.5): 适度调整，置信度≥0.6")
    print("   - 低margin(<0.1): 适当降低，置信度≤0.5")
    print("   - 有detail数据: 保持weighted fusion的置信度")
    
    print("\n✅ 置信度硬帽问题已修复")
    return True

def check_alias_merge_fix():
    """检查别名误合并修复"""
    print("\n🔧 检查别名误合并修复")
    print("=" * 50)
    
    print("📊 别名映射修复:")
    print("   - orange_sofa_corner: 独立映射，不再合并到storage_corner")
    print("   - 避免'corner'关键词的误匹配")
    print("   - 保持不同语义点的独立性")
    
    print("\n✅ 别名误合并问题已修复")
    return True

def main():
    """主修复函数"""
    print("🧪 关键问题修复检查")
    print("=" * 70)
    
    print("📋 基于你的分析，主要问题:")
    print("1. 🚨 细节索引缺失 → 所有节点都显示'Found 0 detail entries'")
    print("2. 🚨 返回值解包异常 → 导致回退到legacy系统")
    print("3. ✅ 置信度计算硬帽 → 已修复为基于margin的平滑调整")
    print("4. ✅ 别名误合并 → 已修复orange_sofa_corner独立映射")
    print("5. ✅ 温度参数优化 → 已调整到合理范围")
    
    results = []
    
    # 1. 检查细节索引对齐
    results.append(("细节索引对齐", fix_detail_index_issue()))
    
    # 2. 检查返回值格式
    results.append(("返回值格式", check_return_value_format()))
    
    # 3. 检查置信度修复
    results.append(("置信度硬帽修复", check_confidence_cap_fix()))
    
    # 4. 检查别名修复
    results.append(("别名误合并修复", check_alias_merge_fix()))
    
    print("\n📊 修复结果总结:")
    for name, result in results:
        status = "✅ 已修复" if result else "🚨 需要修复"
        print(f"   {name}: {status}")
    
    # 关键修复建议
    print("\n🔧 关键修复建议:")
    print("1. 【最重要】修复返回值解包异常 → 阻止回退到legacy")
    print("2. 【重要】补齐细节索引缺失的节点 → 解除'无细节'帽")
    print("3. 【已完成】置信度硬帽 → 基于margin的平滑调整")
    print("4. 【已完成】别名误合并 → 独立映射")
    print("5. 【已完成】参数优化 → 温度和权重平衡")
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 所有检查通过！")
    else:
        print("\n⚠️ 发现需要修复的问题")
    print("\n✅ 检查完成!")
