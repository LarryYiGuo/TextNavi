#!/usr/bin/env python3
"""
测试完整的detail查找流程
"""

import os
import json
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_full_detail_flow():
    """测试完整的detail查找流程"""
    print("🔧 测试完整的detail查找流程")
    print("=" * 50)
    
    # 1. 模拟get_detailed_matching_data
    def get_detailed_matching_data(site_id: str) -> list:
        """Get detailed matching data from Detail files for layered fusion conversation enhancement"""
        detail_file_mapping = {
            "SCENE_A_MS": "Sense_A_MS.jsonl",
            "SCENE_B_STUDIO": "Sense_B_Studio.jsonl"
        }
        
        filename = detail_file_mapping.get(site_id)
        if not filename:
            print(f"⚠️ No Detail file mapping found for site_id: {site_id}")
            return []
        
        filepath = os.path.join(current_dir, "data", filename)
        try:
            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            print(f"✅ Loaded {len(data)} detailed descriptions from {filepath} for {site_id}")
            return data
        except Exception as e:
            print(f"⚠️ Failed to load detailed descriptions from {filename}: {e}")
            return []
    
    # 2. 模拟find_node_details_by_hint
    def find_node_details_by_hint(node_id: str, detailed_data: list) -> list:
        """Find detail descriptions from Sense_A_MS.jsonl using node_hint field"""
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
    
    # 3. 测试完整流程
    print("📋 测试步骤:")
    print("1. 调用get_detailed_matching_data")
    print("2. 调用find_node_details_by_hint")
    print("3. 验证结果")
    print()
    
    # 步骤1: 加载detail数据
    detailed_data = get_detailed_matching_data("SCENE_A_MS")
    print(f"📊 加载的detail数据数量: {len(detailed_data)}")
    
    if not detailed_data:
        print("❌ detailed_data为空，这是问题所在！")
        return
    
    # 步骤2: 测试查找
    test_nodes = ["chair_on_yline", "desks_cluster", "yline_start", "yline_bend_mid", "tv_zone", "dp_ms_entrance", "small_table_mid", "storage_corner", "atrium_edge"]
    
    print(f"\n🔍 测试查找每个节点:")
    for node_id in test_nodes:
        details = find_node_details_by_hint(node_id, detailed_data)
        if len(details) == 0:
            print(f"   ⚠️ {node_id}: 未找到detail数据")
        else:
            print(f"   ✅ {node_id}: 找到 {len(details)} 项")
    
    # 步骤3: 检查数据完整性
    print(f"\n🔍 检查数据完整性:")
    node_hints = set()
    for item in detailed_data:
        node_hint = item.get("node_hint", "")
        if node_hint:
            node_hints.add(node_hint)
    
    print(f"   Detail文件中的node_hint: {sorted(node_hints)}")
    print(f"   测试的节点: {sorted(test_nodes)}")
    
    missing_nodes = set(test_nodes) - node_hints
    if missing_nodes:
        print(f"   ⚠️ 缺失的节点: {sorted(missing_nodes)}")
    else:
        print(f"   ✅ 所有测试节点都有对应的detail数据")

def main():
    """主函数"""
    print("🧪 完整Detail查找流程测试")
    print("=" * 70)
    
    test_full_detail_flow()
    
    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    main()
