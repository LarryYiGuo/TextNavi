#!/usr/bin/env python3
"""
测试所有数据文件的格式和读取方式
"""

import os
import json
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_file_format(filename, filepath):
    """测试单个文件的格式"""
    print(f"\n🔍 测试文件: {filename}")
    print(f"   路径: {filepath}")
    
    if not os.path.exists(filepath):
        print("   ❌ 文件不存在")
        return False
    
    # 获取文件大小
    size = os.path.getsize(filepath)
    print(f"   大小: {size} bytes")
    
    # 检查文件扩展名
    if filename.endswith('.jsonl'):
        expected_format = "JSONL"
    else:
        expected_format = "JSON"
    print(f"   期望格式: {expected_format}")
    
    # 尝试读取文件
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否为空
        if not content.strip():
            print("   ❌ 文件为空")
            return False
        
        # 尝试解析
        if expected_format == "JSONL":
            # JSONL格式：每行一个JSON对象
            lines = content.strip().split('\n')
            valid_lines = 0
            total_lines = len(lines)
            
            print(f"   总行数: {total_lines}")
            
            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        json.loads(line)
                        valid_lines += 1
                    except json.JSONDecodeError as e:
                        print(f"   第{i}行JSON解析失败: {e}")
                        return False
            
            print(f"   ✅ 成功解析 {valid_lines}/{total_lines} 行JSON")
            return True
            
        else:
            # JSON格式：整个文件是一个JSON对象
            try:
                data = json.loads(content)
                print(f"   ✅ 成功解析为标准JSON")
                
                # 检查关键字段
                if "topology" in data and "nodes" in data["topology"]:
                    node_count = len(data["topology"]["nodes"])
                    print(f"   📋 包含 {node_count} 个拓扑节点")
                elif "input" in data and "topology" in data["input"]:
                    node_count = len(data["input"]["topology"]["nodes"])
                    print(f"   📋 包含 {node_count} 个拓扑节点")
                else:
                    print(f"   ⚠️ 未找到拓扑节点信息")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析失败: {e}")
                return False
                
    except Exception as e:
        print(f"   ❌ 文件读取失败: {e}")
        return False

def test_structure_file_reading():
    """测试structure文件的读取方式"""
    print(f"\n🔧 测试Structure文件读取方式")
    
    # 模拟_retrieve_from_structure_map函数的逻辑
    def read_structure_file(scene_filter):
        try:
            # 根据场景选择文件
            if scene_filter == "SCENE_A_MS":
                textmap_file = os.path.join("data", "Sense_A_Finetuned.fixed.jsonl")
            elif scene_filter == "SCENE_B_STUDIO":
                textmap_file = os.path.join("data", "Sense_B_Finetuned.fixed.jsonl")
            else:
                return None, "Unknown scene"
            
            print(f"   尝试读取: {textmap_file}")
            
            # 读取textmap文件 - 支持JSON和JSONL两种格式
            textmap_data = None
            try:
                # 首先尝试作为标准JSON读取
                with open(textmap_file, 'r', encoding='utf-8') as f:
                    textmap_data = json.load(f)
                    print(f"   ✅ 成功读取为标准JSON格式")
                    return textmap_data, "JSON"
            except json.JSONDecodeError:
                # 如果失败，尝试作为JSONL读取
                try:
                    with open(textmap_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                textmap_data = json.loads(line)
                                break  # 只读取第一行
                    print(f"   ✅ 成功读取为JSONL格式")
                    return textmap_data, "JSONL"
                except Exception as e:
                    print(f"   ❌ 无法读取文件: {e}")
                    return None, "Error"
            
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
            return None, "Error"
    
    # 测试两个场景
    for scene in ["SCENE_A_MS", "SCENE_B_STUDIO"]:
        print(f"\n   测试场景: {scene}")
        data, format_type = read_structure_file(scene)
        if data:
            # 检查节点信息
            nodes = []
            if "input" in data and "topology" in data["input"]:
                nodes = data["input"]["topology"].get("nodes", [])
                print(f"   📋 从input.topology中读取到 {len(nodes)} 个节点")
            elif "topology" in data:
                nodes = data["topology"].get("nodes", [])
                print(f"   📋 从顶级topology中读取到 {len(nodes)} 个节点")
            
            if nodes:
                print(f"   📋 前3个节点ID: {[node.get('id', 'unknown') for node in nodes[:3]]}")
        else:
            print(f"   ❌ 读取失败")

def test_detail_file_reading():
    """测试detail文件的读取方式"""
    print(f"\n🔧 测试Detail文件读取方式")
    
    # 模拟_retrieve_from_detail_map函数的逻辑
    def read_detail_file(scene_filter):
        try:
            # 根据场景选择文件
            if scene_filter == "SCENE_A_MS":
                detail_file = os.path.join("data", "Sense_A_MS.jsonl")
            elif scene_filter == "SCENE_B_STUDIO":
                detail_file = os.path.join("data", "Sense_B_Studio.jsonl")
            else:
                return None, "Unknown scene"
            
            print(f"   尝试读取: {detail_file}")
            
            if not os.path.exists(detail_file):
                print(f"   ❌ 文件不存在")
                return None, "File not found"
            
            # 解析JSONL格式
            detail_items = []
            with open(detail_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            detail_item = json.loads(line)
                            node_id = detail_item.get("node_hint", "")
                            if node_id:
                                detail_items.append(detail_item)
                        except json.JSONDecodeError as e:
                            print(f"   第{line_num}行JSON解析失败: {e}")
                            return None, "JSON decode error"
            
            print(f"   ✅ 成功读取 {len(detail_items)} 个detail项")
            return detail_items, "JSONL"
            
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
            return None, "Error"
    
    # 测试两个场景
    for scene in ["SCENE_A_MS", "SCENE_B_STUDIO"]:
        print(f"\n   测试场景: {scene}")
        data, format_type = read_detail_file(scene)
        if data:
            # 检查前几个item
            if len(data) > 0:
                first_item = data[0]
                print(f"   📋 第一个item的node_hint: {first_item.get('node_hint', 'unknown')}")
                print(f"   📋 第一个item的scene_id: {first_item.get('scene_id', 'unknown')}")
        else:
            print(f"   ❌ 读取失败")

def main():
    """主函数"""
    print("🧪 数据文件格式和读取方式测试")
    print("=" * 60)
    
    # 测试所有文件
    files_to_test = [
        ("Sense_A_Finetuned.fixed.jsonl", "data/Sense_A_Finetuned.fixed.jsonl"),
        ("Sense_A_MS.jsonl", "data/Sense_A_MS.jsonl"),
        ("Sence_A_4o.fixed.jsonl", "data/Sence_A_4o.fixed.jsonl"),
        ("Sense_B_4o.fixed.jsonl", "data/Sense_B_4o.fixed.jsonl"),
        ("Sense_B_Finetuned.fixed.jsonl", "data/Sense_B_Finetuned.fixed.jsonl"),
        ("Sense_B_Studio.jsonl", "data/Sense_B_Studio.jsonl")
    ]
    
    all_passed = True
    for filename, filepath in files_to_test:
        if not test_file_format(filename, filepath):
            all_passed = False
    
    # 测试读取方式
    test_structure_file_reading()
    test_detail_file_reading()
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ 所有文件格式测试通过!")
    else:
        print("❌ 部分文件格式测试失败!")
    
    print("\n📊 总结:")
    print("   - Structure文件: 支持JSON和JSONL两种格式")
    print("   - Detail文件: 必须是JSONL格式（每行一个JSON对象）")
    print("   - 代码已适配两种格式，能自动检测并正确读取")

if __name__ == "__main__":
    main()
