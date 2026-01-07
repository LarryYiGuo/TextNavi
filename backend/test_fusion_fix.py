#!/usr/bin/env python3
"""
测试weighted fusion修复的简单脚本
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_detail_alignment():
    """测试detail数据对齐"""
    print("🔍 测试detail数据对齐...")
    
    # 测试SCENE_A_MS
    scene_filter = "SCENE_A_MS"
    detail_file = os.path.join("data", "Sense_A_MS.jsonl")
    
    if not os.path.exists(detail_file):
        print("❌ Detail文件不存在")
        return
    
    # 读取所有detail项
    detail_items = []
    with open(detail_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    detail_item = json.loads(line)
                    detail_items.append(detail_item)
                except json.JSONDecodeError:
                    continue
    
    print(f"📊 总共有 {len(detail_items)} 个detail项")
    
    # 统计node_hint分布
    node_hint_counts = {}
    for item in detail_items:
        node_hint = item.get("node_hint", "")
        if node_hint:
            node_hint_counts[node_hint] = node_hint_counts.get(node_hint, 0) + 1
    
    print(f"📊 涉及 {len(node_hint_counts)} 个不同的节点")
    print("📋 Node hint分布:")
    for node_id, count in sorted(node_hint_counts.items()):
        print(f"   {node_id}: {count} 项")
    
    # 检查是否有重复的node_hint
    print("\n🔍 检查数据对齐问题...")
    for node_id, count in node_hint_counts.items():
        if count > 1:
            print(f"   ⚠️ {node_id} 有 {count} 个detail项（可能重复）")
        else:
            print(f"   ✅ {node_id} 有 {count} 个detail项")

def test_structure_nodes():
    """测试structure节点"""
    print("\n🔍 测试structure节点...")
    
    # 读取SCENE_A_MS的structure文件
    struct_file = os.path.join("data", "Sense_A_Finetuned.fixed.jsonl")
    
    if not os.path.exists(struct_file):
        print("❌ Structure文件不存在")
        return
    
    try:
        with open(struct_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取节点信息
        nodes = []
        if "input" in data and "topology" in data["input"]:
            nodes = data["input"]["topology"].get("nodes", [])
            print(f"📊 从input.topology中读取到 {len(nodes)} 个节点")
        elif "topology" in data:
            nodes = data["topology"].get("nodes", [])
            print(f"📊 从顶级topology中读取到 {len(nodes)} 个节点")
        
        print("📋 Structure节点列表:")
        for node in nodes:
            node_id = node.get("id", "unknown")
            node_name = node.get("name", "unnamed")
            print(f"   {node_id}: {node_name}")
            
    except Exception as e:
        print(f"❌ 读取structure文件失败: {e}")

if __name__ == "__main__":
    print("🧪 Weighted Fusion 修复测试")
    print("=" * 50)
    
    test_detail_alignment()
    test_structure_nodes()
    
    print("\n✅ 测试完成!")
