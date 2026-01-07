#!/usr/bin/env python3
"""
测试detail索引修复的脚本
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_detail_index_building():
    """测试detail索引构建"""
    print("🔍 测试detail索引构建...")
    
    # 模拟EnhancedDualChannelRetriever类
    class MockRetriever:
        def __init__(self):
            self.current_scene_filter = None
        
        def _build_detail_index(self):
            """构建detail索引，确保与structure节点ID对齐"""
            detail_index = {}
            try:
                # 从实际的detail文件中读取数据
                detail_file = None
                if hasattr(self, 'current_scene_filter'):
                    if self.current_scene_filter == "SCENE_A_MS":
                        detail_file = os.path.join("data", "Sense_A_MS.jsonl")
                    elif self.current_scene_filter == "SCENE_B_STUDIO":
                        detail_file = os.path.join("data", "Sense_B_Studio.jsonl")
                
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
    
    # 测试SCENE_A_MS
    print("\n🧪 测试SCENE_A_MS场景...")
    retriever = MockRetriever()
    retriever.current_scene_filter = "SCENE_A_MS"
    detail_index = retriever._build_detail_index()
    
    # 测试特定节点的detail查找
    test_nodes = ["chair_on_yline", "small_table_mid", "atrium_edge"]
    for node_id in test_nodes:
        if node_id in detail_index:
            print(f"✅ {node_id}: 找到 {len(detail_index[node_id])} 个detail项")
        else:
            print(f"❌ {node_id}: 未找到detail项")
    
    # 测试SCENE_B_STUDIO
    print("\n🧪 测试SCENE_B_STUDIO场景...")
    retriever.current_scene_filter = "SCENE_B_STUDIO"
    detail_index = retriever._build_detail_index()
    
    # 测试特定节点的detail查找
    test_nodes = ["workstation_zone", "glass_cage_room", "lounge_area"]
    for node_id in test_nodes:
        if node_id in detail_index:
            print(f"✅ {node_id}: 找到 {len(detail_index[node_id])} 个detail项")
        else:
            print(f"❌ {node_id}: 未找到detail项")

if __name__ == "__main__":
    print("🧪 Detail索引修复测试")
    print("=" * 50)
    
    test_detail_index_building()
    
    print("\n✅ 测试完成!")
