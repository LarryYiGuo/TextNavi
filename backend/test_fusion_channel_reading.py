#!/usr/bin/env python3
"""
测试fusion channel的JSONL文件读取能力
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_jsonl_reading():
    """测试JSONL文件读取能力"""
    print("🔍 测试JSONL文件读取能力...")
    
    # 测试文件列表
    test_files = [
        ("Sense_A_MS.jsonl", "SCENE_A_MS"),
        ("Sense_B_Studio.jsonl", "SCENE_B_STUDIO")
    ]
    
    for filename, scene_id in test_files:
        filepath = os.path.join("data", filename)
        print(f"\n🧪 测试文件: {filename}")
        print(f"   场景: {scene_id}")
        
        if not os.path.exists(filepath):
            print(f"   ❌ 文件不存在: {filepath}")
            continue
        
        # 读取文件内容
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"   📊 文件大小: {os.path.getsize(filepath)} bytes")
            print(f"   📊 总行数: {len(lines)}")
            
            # 解析JSONL内容
            valid_entries = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        valid_entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️ 第{i+1}行JSON解析失败: {e}")
            
            print(f"   ✅ 成功解析: {len(valid_entries)} 个有效条目")
            
            # 检查关键字段
            if valid_entries:
                first_entry = valid_entries[0]
                print(f"   📋 第一个条目的字段:")
                for key, value in first_entry.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      {key}: {value[:50]}...")
                    else:
                        print(f"      {key}: {value}")
                
                # 检查node_hint字段
                node_hints = set()
                for entry in valid_entries:
                    node_hint = entry.get("node_hint", "")
                    if node_hint:
                        node_hints.add(node_hint)
                
                print(f"   🎯 涉及的节点数量: {len(node_hints)}")
                print(f"   🎯 节点列表: {sorted(list(node_hints))}")
                
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")

def test_structure_file_reading():
    """测试structure文件的读取能力"""
    print("\n🔍 测试structure文件读取能力...")
    
    # 测试文件列表
    test_files = [
        ("Sense_A_Finetuned.fixed.jsonl", "SCENE_A_MS"),
        ("Sense_B_Finetuned.fixed.jsonl", "SCENE_B_STUDIO")
    ]
    
    for filename, scene_id in test_files:
        filepath = os.path.join("data", filename)
        print(f"\n🧪 测试文件: {filename}")
        print(f"   场景: {scene_id}")
        
        if not os.path.exists(filepath):
            print(f"   ❌ 文件不存在: {filepath}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"   📊 文件大小: {os.path.getsize(filepath)} bytes")
            
            # 尝试解析为JSON
            try:
                data = json.loads(content)
                print(f"   ✅ 成功解析为标准JSON格式")
                
                # 检查结构
                if "input" in data and "topology" in data["input"]:
                    nodes = data["input"]["topology"].get("nodes", [])
                    print(f"   🏗️ 从input.topology中找到 {len(nodes)} 个节点")
                elif "topology" in data:
                    nodes = data["topology"].get("nodes", [])
                    print(f"   🏗️ 从顶级topology中找到 {len(nodes)} 个节点")
                else:
                    print(f"   ⚠️ 未找到topology结构")
                
                # 检查其他关键字段
                key_fields = ["landmarks", "retrieval", "navigation_policy"]
                for field in key_fields:
                    if field in data:
                        print(f"   📋 包含字段: {field}")
                    else:
                        print(f"   ❌ 缺少字段: {field}")
                        
            except json.JSONDecodeError:
                print(f"   ⚠️ 标准JSON解析失败，尝试JSONL格式")
                
                # 尝试作为JSONL读取
                lines = content.split('\n')
                valid_entries = []
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            valid_entries.append(entry)
                        except json.JSONDecodeError:
                            pass
                
                if valid_entries:
                    print(f"   ✅ 成功解析为JSONL格式: {len(valid_entries)} 个条目")
                else:
                    print(f"   ❌ JSONL解析也失败")
                    
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")

def test_fusion_channel_integration():
    """测试fusion channel的集成读取能力"""
    print("\n🔍 测试fusion channel集成读取能力...")
    
    # 模拟EnhancedDualChannelRetriever的读取逻辑
    class MockFusionChannel:
        def __init__(self):
            self.current_scene_filter = None
        
        def _retrieve_from_structure_map(self, scene_filter):
            """模拟从structure map读取"""
            try:
                if scene_filter == "SCENE_A_MS":
                    filepath = os.path.join("data", "Sense_A_Finetuned.fixed.jsonl")
                elif scene_filter == "SCENE_B_STUDIO":
                    filepath = os.path.join("data", "Sense_B_Finetuned.fixed.jsonl")
                else:
                    return None
                
                if not os.path.exists(filepath):
                    return None
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 智能格式检测
                try:
                    data = json.loads(content)
                    print(f"   ✅ {scene_filter}: 成功读取为标准JSON格式")
                    return data
                except json.JSONDecodeError:
                    print(f"   ⚠️ {scene_filter}: 标准JSON解析失败")
                    return None
                    
            except Exception as e:
                print(f"   ❌ {scene_filter}: 读取失败 - {e}")
                return None
        
        def _retrieve_from_detail_map(self, scene_filter):
            """模拟从detail map读取"""
            try:
                if scene_filter == "SCENE_A_MS":
                    filepath = os.path.join("data", "Sense_A_MS.jsonl")
                elif scene_filter == "SCENE_B_STUDIO":
                    filepath = os.path.join("data", "Sense_B_Studio.jsonl")
                else:
                    return []
                
                if not os.path.exists(filepath):
                    return []
                
                detail_items = []
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                detail_item = json.loads(line)
                                detail_items.append(detail_item)
                            except json.JSONDecodeError:
                                continue
                
                print(f"   ✅ {scene_filter}: 成功读取 {len(detail_items)} 个detail项")
                return detail_items
                
            except Exception as e:
                print(f"   ❌ {scene_filter}: 读取失败 - {e}")
                return []
    
    # 测试两个场景
    fusion_channel = MockFusionChannel()
    
    print("\n🧪 测试SCENE_A_MS...")
    structure_data = fusion_channel._retrieve_from_structure_map("SCENE_A_MS")
    detail_data = fusion_channel._retrieve_from_detail_map("SCENE_A_MS")
    
    print("\n🧪 测试SCENE_B_STUDIO...")
    structure_data = fusion_channel._retrieve_from_structure_map("SCENE_B_STUDIO")
    detail_data = fusion_channel._retrieve_from_detail_map("SCENE_B_STUDIO")

if __name__ == "__main__":
    print("🧪 Fusion Channel JSONL读取能力测试")
    print("=" * 60)
    
    test_jsonl_reading()
    test_structure_file_reading()
    test_fusion_channel_integration()
    
    print("\n✅ 测试完成!")
