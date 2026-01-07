#!/usr/bin/env python3
"""
调试detail索引问题
"""

import os
import json
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_detail_index_build():
    """测试detail索引构建"""
    print("🔧 测试detail索引构建")
    print("=" * 50)
    
    # 模拟_build_detail_index方法
    def _build_detail_index(scene_filter):
        """构建detail索引，确保与structure节点ID对齐"""
        detail_index = {}
        try:
            # 从实际的detail文件中读取数据
            detail_file = None
            if scene_filter == "SCENE_A_MS":
                detail_file = os.path.join(current_dir, "data", "Sense_A_MS.jsonl")
            elif scene_filter == "SCENE_B_STUDIO":
                detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
            
            if detail_file and os.path.exists(detail_file):
                print(f"🔧 从文件构建detail索引: {detail_file}")
                with open(detail_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                detail_item = json.loads(line)
                                node_hint = detail_item.get("node_hint", "")
                                if node_hint:
                                    if node_hint not in detail_index:
                                        detail_index[node_hint] = []
                                    detail_index[node_hint].append(detail_item)
                            except json.JSONDecodeError:
                                continue
                
                print(f"🔧 Detail索引构建完成: {len(detail_index)} 个节点有detail数据")
                for node_id, items in detail_index.items():
                    print(f"   {node_id}: {len(items)} 项")
            else:
                print(f"⚠️ 未找到detail文件或场景未设置")
                
        except Exception as e:
            print(f"⚠️ Detail索引构建失败: {e}")
            
        return detail_index
    
    # 测试构建
    detail_index = _build_detail_index("SCENE_A_MS")
    
    # 测试查找
    print(f"\n🔍 测试查找:")
    test_nodes = ["chair_on_yline", "desks_cluster", "yline_start", "yline_bend_mid", "tv_zone", "dp_ms_entrance", "small_table_mid", "storage_corner", "atrium_edge"]
    
    for node_id in test_nodes:
        items = detail_index.get(node_id, [])
        print(f"   {node_id}: {len(items)} 项")
        if len(items) == 0:
            print(f"     ⚠️ 未找到detail数据！")
    
    return detail_index

def test_find_node_details_by_hint():
    """测试find_node_details_by_hint函数"""
    print(f"\n🔧 测试find_node_details_by_hint函数")
    print("=" * 50)
    
    # 加载detail数据
    detail_file = os.path.join(current_dir, "data", "Sense_A_MS.jsonl")
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
        """Find detail descriptions from Sense_A_MS.jsonl using node_hint field"""
        if not detailed_data:
            return []
        
        node_details = []
        for item in detailed_data:
            # Use node_hint field to match with structure nodes
            if item.get("node_hint") == node_id:
                node_details.append(item)
        
        print(f"🔍 Found {len(node_details)} detail entries for node {node_id}")
        return node_details
    
    # 测试查找
    test_nodes = ["chair_on_yline", "desks_cluster", "yline_start", "yline_bend_mid", "tv_zone", "dp_ms_entrance", "small_table_mid", "storage_corner", "atrium_edge"]
    
    for node_id in test_nodes:
        details = find_node_details_by_hint(node_id, detailed_data)
        if len(details) == 0:
            print(f"   ⚠️ {node_id}: 未找到detail数据")

def main():
    """主函数"""
    print("🧪 Detail索引调试测试")
    print("=" * 70)
    
    # 1. 测试索引构建
    detail_index = test_detail_index_build()
    
    # 2. 测试查找函数
    test_find_node_details_by_hint()
    
    print(f"\n✅ 调试完成!")

if __name__ == "__main__":
    main()
