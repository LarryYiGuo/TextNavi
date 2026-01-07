#!/usr/bin/env python3
"""
分析四个JSONL文件的一致性和潜在问题
检查是否与之前的User Needs和DGs修改保持一致
"""

import json
import os
from typing import Dict, List, Any

def load_jsonl_file(filepath: str) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    try:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 第{line_num}行JSON解析错误: {e}")
        return data
    except Exception as e:
        print(f"❌ 加载文件失败 {filepath}: {e}")
        return []

def analyze_structure_file(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """分析Structure文件的结构和内容"""
    print(f"\n🔍 分析Structure文件: {filename}")
    print("=" * 60)
    
    analysis = {
        "filename": filename,
        "has_topology": False,
        "has_nodes": False,
        "has_edges": False,
        "has_landmarks": False,
        "has_retrieval": False,
        "node_count": 0,
        "edge_count": 0,
        "landmark_count": 0,
        "retrieval_fields": [],
        "evaluation_hooks": [],
        "accessibility_fields": [],
        "issues": []
    }
    
    # 检查基本结构
    if "topology" in data:
        analysis["has_topology"] = True
        topology = data["topology"]
        
        # 检查节点
        if "nodes" in topology:
            analysis["has_nodes"] = True
            analysis["node_count"] = len(topology["nodes"])
            
            # 分析第一个节点的详细信息
            if topology["nodes"]:
                first_node = topology["nodes"][0]
                print(f"📊 节点数量: {analysis['node_count']}")
                print(f"📍 示例节点: {first_node.get('id', 'Unknown')}")
                
                # 检查检索字段
                if "retrieval" in first_node:
                    analysis["has_retrieval"] = True
                    retrieval = first_node["retrieval"]
                    analysis["retrieval_fields"] = list(retrieval.keys())
                    
                    print(f"🔍 检索字段: {analysis['retrieval_fields']}")
                    if "index_terms" in retrieval:
                        print(f"   index_terms: {retrieval['index_terms']}")
                    if "tags" in retrieval:
                        print(f"   tags: {retrieval['tags']}")
                
                # 检查评估钩子
                if "evaluation_hooks" in first_node:
                    hooks = first_node["evaluation_hooks"]
                    analysis["evaluation_hooks"] = hooks.get("tags", [])
                    print(f"🏷️ 评估标签: {analysis['evaluation_hooks']}")
                
                # 检查无障碍字段
                if "accessibility" in first_node:
                    accessibility = first_node["accessibility"]
                    analysis["accessibility_fields"] = list(accessibility.keys())
                    print(f"♿ 无障碍字段: {analysis['accessibility_fields']}")
        
        # 检查边
        if "edges" in topology:
            analysis["has_edges"] = True
            analysis["edge_count"] = len(topology["edges"])
            print(f"🔄 边数量: {analysis['edge_count']}")
        
        # 检查地标
        if "landmarks" in topology:
            analysis["has_landmarks"] = True
            analysis["landmark_count"] = len(topology["landmarks"])
            print(f"🏛️ 地标数量: {analysis['landmark_count']}")
    
    # 检查其他重要字段
    if "retrieval" in data:
        global_retrieval = data["retrieval"]
        print(f"🌐 全局检索字段: {list(global_retrieval.keys())}")
        if "cnl_index" in global_retrieval:
            print(f"   cnl_index: {len(global_retrieval['cnl_index'])} 项")
        if "keywords" in global_retrieval:
            print(f"   keywords: {global_retrieval['keywords']}")
    
    # 检查输出字段
    if "output" in data:
        output = data["output"]
        print(f"📝 输出长度: {len(output)} 字符")
        print(f"   前100字符: {output[:100]}...")
    
    return analysis

def analyze_detail_file(data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """分析Detail文件的结构和内容"""
    print(f"\n🔍 分析Detail文件: {filename}")
    print("=" * 60)
    
    if not data:
        return {"filename": filename, "error": "文件为空或加载失败"}
    
    analysis = {
        "filename": filename,
        "total_entries": len(data),
        "has_node_hint": 0,
        "has_spatial_relations": 0,
        "has_unique_features": 0,
        "has_fusion": 0,
        "node_hint_values": set(),
        "issues": []
    }
    
    # 分析第一个条目
    first_entry = data[0]
    print(f"📊 总条目数: {analysis['total_entries']}")
    print(f"📍 示例条目ID: {first_entry.get('id', 'Unknown')}")
    
    # 检查关键字段
    for entry in data:
        if "node_hint" in entry:
            analysis["has_node_hint"] += 1
            analysis["node_hint_values"].add(entry["node_hint"])
        
        if "spatial_relations" in entry:
            analysis["has_spatial_relations"] += 1
        
        if "unique_features" in entry:
            analysis["has_unique_features"] += 1
        
        if "fusion" in entry:
            analysis["has_fusion"] += 1
    
    print(f"🔗 包含node_hint的条目: {analysis['has_node_hint']}/{analysis['total_entries']}")
    print(f"🧭 包含spatial_relations的条目: {analysis['has_spatial_relations']}/{analysis['total_entries']}")
    print(f"⭐ 包含unique_features的条目: {analysis['has_unique_features']}/{analysis['total_entries']}")
    print(f"🔄 包含fusion的条目: {analysis['has_fusion']}/{analysis['total_entries']}")
    
    if analysis["node_hint_values"]:
        print(f"🎯 node_hint值: {sorted(list(analysis['node_hint_values']))}")
    
    # 检查数据质量
    if analysis["has_node_hint"] < analysis["total_entries"]:
        analysis["issues"].append("部分条目缺少node_hint字段")
    
    if analysis["has_spatial_relations"] < analysis["total_entries"]:
        analysis["issues"].append("部分条目缺少spatial_relations字段")
    
    return analysis

def check_consistency_between_files(structure_analysis: Dict, detail_analysis: Dict) -> Dict[str, Any]:
    """检查Structure和Detail文件之间的一致性"""
    print(f"\n🔗 检查Structure和Detail文件的一致性")
    print("=" * 60)
    
    consistency = {
        "node_hint_coverage": 0.0,
        "potential_mismatches": [],
        "recommendations": []
    }
    
    # 检查node_hint覆盖率
    if "node_hint_values" in detail_analysis and "node_count" in structure_analysis:
        detail_nodes = detail_analysis["node_hint_values"]
        structure_nodes = structure_analysis["node_count"]
        
        if structure_nodes > 0:
            consistency["node_hint_coverage"] = len(detail_nodes) / structure_nodes
            print(f"📊 node_hint覆盖率: {consistency['node_hint_coverage']:.2%} ({len(detail_nodes)}/{structure_nodes})")
        
        # 检查潜在的节点ID不匹配
        if "node_ids" in structure_analysis:
            structure_node_ids = set(structure_analysis["node_ids"])
            missing_nodes = structure_node_ids - detail_nodes
            extra_nodes = detail_nodes - structure_node_ids
            
            if missing_nodes:
                consistency["potential_mismatches"].append(f"Detail文件缺少节点: {missing_nodes}")
                print(f"⚠️ Detail文件缺少节点: {missing_nodes}")
            
            if extra_nodes:
                consistency["potential_mismatches"].append(f"Detail文件包含未知节点: {extra_nodes}")
                print(f"⚠️ Detail文件包含未知节点: {extra_nodes}")
    
    # 生成建议
    if consistency["node_hint_coverage"] < 0.8:
        consistency["recommendations"].append("建议增加Detail文件的node_hint覆盖率")
    
    if detail_analysis.get("has_spatial_relations", 0) < detail_analysis.get("total_entries", 0):
        consistency["recommendations"].append("建议为所有Detail条目添加spatial_relations")
    
    if detail_analysis.get("has_unique_features", 0) < detail_analysis.get("total_entries", 0):
        consistency["recommendations"].append("建议为所有Detail条目添加unique_features")
    
    return consistency

def main():
    """主函数"""
    print("🚀 开始分析JSONL文件的一致性")
    print("=" * 80)
    
    data_dir = "data"
    
    # 分析Structure文件
    structure_files = [
        "Sense_A_Finetuned.fixed.jsonl",
        "Sense_B_Finetuned.fixed.jsonl"
    ]
    
    # 分析Detail文件
    detail_files = [
        "Sense_A_MS.jsonl",
        "Sense_B_Studio.jsonl"
    ]
    
    all_analyses = {}
    
    # 分析Structure文件
    for filename in structure_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            data = load_jsonl_file(filepath)
            if data:
                analysis = analyze_structure_file(data[0], filename)
                all_analyses[filename] = analysis
        else:
            print(f"❌ 文件不存在: {filepath}")
    
    # 分析Detail文件
    for filename in detail_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            data = load_jsonl_file(filepath)
            if data:
                analysis = analyze_detail_file(data, filename)
                all_analyses[filename] = analysis
        else:
            print(f"❌ 文件不存在: {filepath}")
    
    # 检查一致性
    print(f"\n📋 分析总结")
    print("=" * 80)
    
    for filename, analysis in all_analyses.items():
        if "error" not in analysis:
            print(f"✅ {filename}: 分析完成")
        else:
            print(f"❌ {filename}: {analysis['error']}")
    
    # 生成建议
    print(f"\n💡 改进建议")
    print("=" * 80)
    
    recommendations = []
    for filename, analysis in all_analyses.items():
        if "issues" in analysis and analysis["issues"]:
            print(f"🔧 {filename}:")
            for issue in analysis["issues"]:
                print(f"   - {issue}")
                recommendations.append(f"{filename}: {issue}")
    
    if not recommendations:
        print("🎉 所有文件都符合预期结构！")
    
    print(f"\n📊 分析完成！共分析了 {len(all_analyses)} 个文件")

if __name__ == "__main__":
    main()
