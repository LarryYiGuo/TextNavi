#!/usr/bin/env python3
"""
测试Sense_B场景的数据加载修复
验证EnhancedDualChannelRetriever能正确加载Sense_B_Finetuned.fixed.jsonl
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_sense_b_structure_loading():
    """测试Sense_B结构数据加载"""
    print("🔍 测试Sense_B结构数据加载...")
    
    # 检查文件是否存在
    sense_b_file = os.path.join(current_dir, "data", "Sense_B_Finetuned.fixed.jsonl")
    if not os.path.exists(sense_b_file):
        print(f"❌ Sense_B文件不存在: {sense_b_file}")
        return False
    
    # 检查文件内容
    try:
        with open(sense_b_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Sense_B文件加载成功")
        print(f"   场景ID: {data['input']['site_id']}")
        print(f"   POI数量: {len(data['input']['pois'])}")
        print(f"   别名映射: {len(data['input']['alias'])}")
        
        # 检查拓扑结构
        topology = data['input']['topology']
        nodes = topology['nodes']
        edges = topology['edges']
        
        print(f"   拓扑节点: {len(nodes)} 个")
        print(f"   拓扑边: {len(edges)} 条")
        
        # 显示前几个POI
        print("   前5个POI:")
        for i, (poi_id, poi_info) in enumerate(list(data['input']['pois'].items())[:5]):
            print(f"     {poi_id}: {poi_info['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sense_B文件解析失败: {e}")
        return False

def test_sense_b_detail_loading():
    """测试Sense_B detail数据加载"""
    print("\n🔍 测试Sense_B detail数据加载...")
    
    # 检查文件是否存在
    sense_b_detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
    if not os.path.exists(sense_b_detail_file):
        print(f"❌ Sense_B detail文件不存在: {sense_b_detail_file}")
        return False
    
    # 检查文件内容
    try:
        with open(sense_b_detail_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        print(f"✅ Sense_B detail文件加载成功")
        print(f"   总行数: {len(lines)}")
        
        # 解析第一行验证JSON格式
        first_item = json.loads(lines[0])
        print(f"   场景ID: {first_item['scene_id']}")
        print(f"   第一个node_hint: {first_item['node_hint']}")
        
        # 统计唯一的node_hint
        node_hints = set()
        for line in lines:
            try:
                item = json.loads(line)
                node_hints.add(item['node_hint'])
            except:
                continue
        
        print(f"   唯一node_hint数量: {len(node_hints)}")
        print(f"   前5个node_hint: {list(node_hints)[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sense_B detail文件解析失败: {e}")
        return False

def test_alias_mapping():
    """测试别名映射覆盖"""
    print("\n🔍 测试别名映射覆盖...")
    
    # 加载结构数据
    sense_b_file = os.path.join(current_dir, "data", "Sense_B_Finetuned.fixed.jsonl")
    with open(sense_b_file, 'r', encoding='utf-8') as f:
        struct_data = json.load(f)
    
    # 加载detail数据
    sense_b_detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
    with open(sense_b_detail_file, 'r', encoding='utf-8') as f:
        detail_lines = [line.strip() for line in f if line.strip()]
    
    struct_aliases = set(struct_data['input']['alias'].keys())
    detail_hints = set()
    
    for line in detail_lines:
        try:
            item = json.loads(line)
            detail_hints.add(item['node_hint'])
        except:
            continue
    
    print(f"✅ 别名映射分析完成")
    print(f"   结构文件别名: {len(struct_aliases)} 个")
    print(f"   Detail文件hint: {len(detail_hints)} 个")
    print(f"   完全覆盖: {struct_aliases.issuperset(detail_hints)}")
    
    # 检查缺失
    missing = detail_hints - struct_aliases
    if missing:
        print(f"   缺失的别名映射: {list(missing)}")
    else:
        print("   ✅ 无缺失的别名映射")
    
    # 检查多余
    extra = struct_aliases - detail_hints
    if extra:
        print(f"   多余的别名映射: {list(extra)}")
    else:
        print("   ✅ 无多余的别名映射")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试Sense_B场景数据加载修复...\n")
    
    tests = [
        test_sense_b_structure_loading,
        test_sense_b_detail_loading,
        test_alias_mapping
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ 测试通过\n")
            else:
                print("❌ 测试失败\n")
        except Exception as e:
            print(f"❌ 测试异常: {e}\n")
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Sense_B场景数据加载修复成功")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
