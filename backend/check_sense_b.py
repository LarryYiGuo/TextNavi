#!/usr/bin/env python3
"""
检查Sense_B的锚点对齐情况
"""

import os
import json
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_sense_b():
    """检查Sense_B的锚点对齐情况"""
    print("🔍 检查Sense_B的锚点对齐情况")
    print("=" * 50)
    
    # 1. 检查Sense_B_Finetuned.fixed.jsonl中的节点ID
    struct_file = os.path.join(current_dir, "data", "Sense_B_Finetuned.fixed.jsonl")
    if not os.path.exists(struct_file):
        print(f"❌ Structure文件不存在: {struct_file}")
        return
    
    with open(struct_file, 'r', encoding='utf-8') as f:
        try:
            # Sense_B是标准JSON格式，不是JSONL
            struct_data = json.load(f)
            topology = struct_data.get("topology", {})
            nodes = topology.get("nodes", [])
            struct_nodes = set(node["id"] for node in nodes)
            print(f"📊 Structure文件中的节点: {sorted(struct_nodes)}")
        except json.JSONDecodeError:
            print("❌ Structure文件JSON解析失败")
            return
    
    # 2. 检查Sense_B_Studio.jsonl中的node_hint字段
    detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
    if not os.path.exists(detail_file):
        print(f"❌ Detail文件不存在: {detail_file}")
        return
    
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
    
    # 3. 检查对齐情况
    missing_in_detail = struct_nodes - detail_nodes
    missing_in_struct = detail_nodes - struct_nodes
    
    print(f"\n🔍 对齐检查:")
    print(f"   Structure节点数量: {len(struct_nodes)}")
    print(f"   Detail节点数量: {len(detail_nodes)}")
    print(f"   缺失在Detail中: {sorted(missing_in_detail)}")
    print(f"   缺失在Structure中: {sorted(missing_in_struct)}")
    
    if not missing_in_detail and not missing_in_struct:
        print("✅ 所有锚点完全对齐！")
    else:
        if missing_in_detail:
            print(f"⚠️ 发现{len(missing_in_detail)}个节点在Detail文件中缺失")
        if missing_in_struct:
            print(f"⚠️ 发现{len(missing_in_struct)}个多余的Detail锚点")
    
    return struct_nodes, detail_nodes

def test_sense_b_detail_lookup():
    """测试Sense_B的detail查找"""
    print(f"\n🔧 测试Sense_B的detail查找")
    print("=" * 50)
    
    # 加载detail数据
    detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
    detailed_data = []
    
    try:
        with open(detail_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    detailed_data.append(json.loads(line))
        print(f"✅ 加载了 {len(detailed_data)} 条detail数据")
    except Exception as e:
        print(f"❌ 加载detail数据失败: {e}")
        return
    
    # 模拟find_node_details_by_hint函数
    def find_node_details_by_hint(node_id: str, detailed_data: list) -> list:
        """Find detail descriptions from Sense_B_Studio.jsonl using node_hint field"""
        if not detailed_data:
            print(f"⚠️ detailed_data为空！")
            return []
        
        node_details = []
        for item in detailed_data:
            # Use node_hint field to match with structure nodes
            if item.get("node_hint") == node_id:
                node_details.append(item)
        
        print(f"🔍 Found {len(node_details)} detail entries for node {node_id}")
        return node_details
    
    # 测试查找
    test_nodes = ["dp_studio_entrance", "yline_start", "workstation_zone", "disability_innovation_sign", "glass_cage_room", "lounge_area", "storage_zone", "equipment_corner"]
    
    print(f"\n🔍 测试查找每个节点:")
    for node_id in test_nodes:
        details = find_node_details_by_hint(node_id, detailed_data)
        if len(details) == 0:
            print(f"   ⚠️ {node_id}: 未找到detail数据")
        else:
            print(f"   ✅ {node_id}: 找到 {len(details)} 项")

def main():
    """主函数"""
    print("🧪 Sense_B锚点对齐检查")
    print("=" * 70)
    
    # 1. 检查锚点对齐
    struct_nodes, detail_nodes = check_sense_b()
    
    # 2. 测试detail查找
    test_sense_b_detail_lookup()
    
    print(f"\n✅ 检查完成!")

if __name__ == "__main__":
    main()
