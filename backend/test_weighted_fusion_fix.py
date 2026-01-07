#!/usr/bin/env python3
"""
测试weighted fusion修复的脚本
"""

import os
import sys
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_data_files():
    """测试数据文件是否存在和可读"""
    print("🔍 测试数据文件...")
    
    data_files = [
        ("Sense_A_Finetuned.fixed.jsonl", "jsonl"),
        ("Sense_A_MS.jsonl", "jsonl"), 
        ("Sense_B_Finetuned.fixed.jsonl", "json"),
        ("Sense_B_Studio.jsonl", "jsonl")
    ]
    
    for filename, file_type in data_files:
        filepath = os.path.join(current_dir, "data", filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filename}: 存在 ({size} bytes)")
            
            # 根据文件类型选择解析方法
            try:
                if file_type == "json":
                    # 标准JSON文件
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"   📊 成功解析JSON文件")
                        # 检查关键字段
                        if "topology" in data and "nodes" in data["topology"]:
                            print(f"   📋 包含 {len(data['topology']['nodes'])} 个拓扑节点")
                        if "input" in data:
                            print(f"   📋 包含输入配置: {data['input'].get('site_id', 'unknown')}")
                else:
                    # JSONL文件
                    with open(filepath, 'r', encoding='utf-8') as f:
                        line_count = 0
                        for line in f:
                            if line.strip():
                                json.loads(line)  # 测试JSON解析
                                line_count += 1
                        print(f"   📊 成功解析 {line_count} 行JSONL")
            except Exception as e:
                print(f"   ❌ 解析失败: {e}")
        else:
            print(f"❌ {filename}: 不存在")

def test_detail_data_alignment():
    """测试detail数据与structure数据的对齐"""
    print("\n🔍 测试数据对齐...")
    
    # 读取SCENE_B的数据作为示例
    try:
        # 读取structure数据
        struct_file = os.path.join(current_dir, "data", "Sense_B_Finetuned.fixed.jsonl")
        with open(struct_file, 'r', encoding='utf-8') as f:
            struct_data = json.load(f)
        
        # 读取detail数据
        detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
        detail_nodes = set()
        with open(detail_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    detail_item = json.loads(line)
                    node_hint = detail_item.get("node_hint", "")
                    if node_hint:
                        detail_nodes.add(node_hint)
        
        # 获取structure节点
        if "topology" in struct_data:
            struct_nodes = set()
            for node in struct_data["topology"]["nodes"]:
                struct_nodes.add(node["id"])
        else:
            struct_nodes = set()
        
        print(f"📊 Structure节点数量: {len(struct_nodes)}")
        print(f"📊 Detail节点数量: {len(detail_nodes)}")
        
        # 检查对齐
        aligned = detail_nodes.intersection(struct_nodes)
        missing = struct_nodes - detail_nodes
        extra = detail_nodes - struct_nodes
        
        print(f"✅ 对齐的节点: {len(aligned)}")
        if missing:
            print(f"⚠️ 缺少detail的节点: {missing}")
        if extra:
            print(f"⚠️ 多余的detail节点: {extra}")
            
        print(f"📋 对齐的节点列表: {sorted(aligned)}")
        
    except Exception as e:
        print(f"❌ 数据对齐测试失败: {e}")

def test_fusion_weights():
    """测试融合权重配置"""
    print("\n🔍 测试融合权重...")
    
    try:
        # 读取detail数据中的融合权重
        detail_file = os.path.join(current_dir, "data", "Sense_B_Studio.jsonl")
        weights_found = set()
        
        with open(detail_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    detail_item = json.loads(line)
                    fusion = detail_item.get("fusion", {})
                    weights = fusion.get("weights", {})
                    
                    if weights:
                        topo_weight = weights.get("topo_semantic", 0)
                        visual_weight = weights.get("visual_detail", 0)
                        weight_key = f"topo:{topo_weight}, visual:{visual_weight}"
                        weights_found.add(weight_key)
        
        print(f"📊 发现的融合权重配置: {weights_found}")
        
        # 验证权重是否合理
        for weight_config in weights_found:
            if "topo:0.45, visual:0.55" in weight_config:
                print("✅ 融合权重配置正确: 结构45%, 视觉55%")
            else:
                print(f"⚠️ 非标准权重配置: {weight_config}")
                
    except Exception as e:
        print(f"❌ 融合权重测试失败: {e}")

if __name__ == "__main__":
    print("🧪 Weighted Fusion 修复测试")
    print("=" * 50)
    
    test_data_files()
    test_detail_data_alignment()
    test_fusion_weights()
    
    print("\n✅ 测试完成!")
