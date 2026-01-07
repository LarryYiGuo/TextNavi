#!/usr/bin/env python3
"""
深度分析Structure文件的检索索引和匹配问题
检查是否与BLIP caption有良好的匹配度
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

def analyze_retrieval_indexing(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """深度分析检索索引"""
    print(f"\n🔍 深度分析检索索引: {filename}")
    print("=" * 80)
    
    analysis = {
        "filename": filename,
        "total_nodes": 0,
        "nodes_with_retrieval": 0,
        "retrieval_coverage": {},
        "index_terms_analysis": {},
        "tags_analysis": {},
        "potential_issues": []
    }
    
    # 调试：打印数据结构
    print(f"🔍 数据结构键: {list(data.keys())}")
    
    if "topology" in data:
        topology = data["topology"]
        print(f"🔍 topology键: {list(topology.keys())}")
        
        if "nodes" in topology:
            nodes = topology["nodes"]
            analysis["total_nodes"] = len(nodes)
            print(f"📊 总节点数: {analysis['total_nodes']}")
            
            # 分析每个节点的检索字段
            for i, node in enumerate(nodes):
                node_id = node.get("id", f"node_{i}")
                print(f"\n📍 节点 {i+1}: {node_id}")
                
                if "retrieval" in node:
                    analysis["nodes_with_retrieval"] += 1
                    retrieval = node["retrieval"]
                    
                    # 分析index_terms
                    if "index_terms" in retrieval:
                        index_terms = retrieval["index_terms"]
                        print(f"   🔍 index_terms ({len(index_terms)}): {index_terms}")
                        
                        # 检查index_terms的质量
                        for term in index_terms:
                            if term not in analysis["index_terms_analysis"]:
                                analysis["index_terms_analysis"][term] = 0
                            analysis["index_terms_analysis"][term] += 1
                        
                        # 检查是否有重复或空值
                        if len(index_terms) != len(set(index_terms)):
                            analysis["potential_issues"].append(f"节点 {node_id}: index_terms有重复")
                        
                        if any(not term.strip() for term in index_terms):
                            analysis["potential_issues"].append(f"节点 {node_id}: index_terms包含空值")
                    else:
                        print(f"   ⚠️ 缺少index_terms")
                        analysis["potential_issues"].append(f"节点 {node_id}: 缺少index_terms")
                    
                    # 分析tags
                    if "tags" in retrieval:
                        tags = retrieval["tags"]
                        print(f"   🏷️ tags ({len(tags)}): {tags}")
                        
                        # 检查tags的质量
                        for tag in tags:
                            if tag not in analysis["tags_analysis"]:
                                analysis["tags_analysis"][tag] = 0
                            analysis["tags_analysis"][tag] += 1
                        
                        # 检查是否有重复或空值
                        if len(tags) != len(set(tags)):
                            analysis["potential_issues"].append(f"节点 {node_id}: tags有重复")
                        
                        if any(not tag.strip() for tag in tags):
                            analysis["potential_issues"].append(f"节点 {node_id}: tags包含空值")
                    else:
                        print(f"   ⚠️ 缺少tags")
                        analysis["potential_issues"].append(f"节点 {node_id}: 缺少tags")
                    
                    # 检查检索字段的完整性
                    expected_fields = ["index_terms", "tags"]
                    missing_fields = [field for field in expected_fields if field not in retrieval]
                    if missing_fields:
                        analysis["potential_issues"].append(f"节点 {node_id}: 缺少字段 {missing_fields}")
                else:
                    print(f"   ❌ 缺少retrieval字段")
                    analysis["potential_issues"].append(f"节点 {node_id}: 缺少retrieval字段")
        else:
            print("❌ topology中缺少nodes字段")
            analysis["potential_issues"].append("topology中缺少nodes字段")
    else:
        print("❌ 文件缺少topology字段")
        analysis["potential_issues"].append("文件缺少topology字段")
    
    # 计算覆盖率
    if analysis["total_nodes"] > 0:
        retrieval_coverage = analysis["nodes_with_retrieval"] / analysis["total_nodes"]
        analysis["retrieval_coverage"] = {
            "nodes_with_retrieval": analysis["nodes_with_retrieval"],
            "total_nodes": analysis["total_nodes"],
            "coverage_percentage": retrieval_coverage * 100
        }
        print(f"\n📊 检索字段覆盖率: {retrieval_coverage:.1%} ({analysis['nodes_with_retrieval']}/{analysis['total_nodes']})")
    
    return analysis

def analyze_global_retrieval(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """分析全局检索字段"""
    print(f"\n🌐 分析全局检索字段: {filename}")
    print("=" * 60)
    
    analysis = {
        "filename": filename,
        "has_global_retrieval": False,
        "global_fields": {},
        "cnl_index_analysis": {},
        "keywords_analysis": {},
        "potential_issues": []
    }
    
    if "retrieval" in data:
        analysis["has_global_retrieval"] = True
        global_retrieval = data["retrieval"]
        analysis["global_fields"] = list(global_retrieval.keys())
        
        print(f"🔍 全局检索字段: {analysis['global_fields']}")
        
        # 分析cnl_index
        if "cnl_index" in global_retrieval:
            cnl_index = global_retrieval["cnl_index"]
            print(f"📝 cnl_index ({len(cnl_index)} 项):")
            for i, item in enumerate(cnl_index):
                print(f"   {i+1}. {item[:100]}...")
                analysis["cnl_index_analysis"][f"item_{i+1}"] = len(item)
        else:
            print("⚠️ 缺少cnl_index")
            analysis["potential_issues"].append("缺少cnl_index字段")
        
        # 分析keywords
        if "keywords" in global_retrieval:
            keywords = global_retrieval["keywords"]
            print(f"🔑 keywords ({len(keywords)}): {keywords}")
            analysis["keywords_analysis"] = {
                "count": len(keywords),
                "keywords": keywords
            }
        else:
            print("⚠️ 缺少keywords")
            analysis["potential_issues"].append("缺少keywords字段")
    else:
        print("❌ 缺少全局retrieval字段")
        analysis["potential_issues"].append("缺少全局retrieval字段")
    
    return analysis

def simulate_blip_matching(analysis: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """模拟BLIP caption与检索索引的匹配"""
    print(f"\n🤖 模拟BLIP caption匹配: {filename}")
    print("=" * 60)
    
    # 模拟一些典型的BLIP caption
    test_captions = [
        "I am at the Maker Space entrance with glass doors behind me",
        "There is a yellow line on the floor starting from the entrance",
        "I can see a brown chair on the yellow line",
        "The yellow line bends left toward the windows",
        "I am near large windows with soft seats",
        "There is a TV screen and storage shelves",
        "I can see a small table with purple chairs",
        "There is an orange sofa against the wall"
    ]
    
    matching_results = []
    
    for caption in test_captions:
        caption_lower = caption.lower()
        print(f"\n📝 测试caption: {caption}")
        
        # 检查与index_terms的匹配
        index_matches = []
        for term, count in analysis.get("index_terms_analysis", {}).items():
            if term.lower() in caption_lower:
                index_matches.append((term, count))
        
        # 检查与tags的匹配
        tag_matches = []
        for tag, count in analysis.get("tags_analysis", {}).items():
            if tag.lower() in caption_lower:
                tag_matches.append((tag, count))
        
        # 检查与keywords的匹配
        keyword_matches = []
        keywords = analysis.get("keywords_analysis", {}).get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in caption_lower:
                keyword_matches.append(keyword)
        
        # 计算匹配分数
        total_matches = len(index_matches) + len(tag_matches) + len(keyword_matches)
        match_score = total_matches / 10.0  # 归一化到0-1范围
        
        print(f"   🔍 index_terms匹配: {len(index_matches)} 项")
        if index_matches:
            for term, count in index_matches[:3]:  # 只显示前3个
                print(f"      - {term} (出现{count}次)")
        
        print(f"   🏷️ tags匹配: {len(tag_matches)} 项")
        if tag_matches:
            for tag, count in tag_matches[:3]:  # 只显示前3个
                print(f"      - {tag} (出现{count}次)")
        
        print(f"   🔑 keywords匹配: {len(keyword_matches)} 项")
        if keyword_matches:
            for keyword in keyword_matches[:3]:  # 只显示前3个
                print(f"      - {keyword}")
        
        print(f"   📊 总匹配分数: {match_score:.3f}")
        
        matching_results.append({
            "caption": caption,
            "index_matches": len(index_matches),
            "tag_matches": len(tag_matches),
            "keyword_matches": len(keyword_matches),
            "total_matches": total_matches,
            "match_score": match_score
        })
    
    # 计算平均匹配分数
    if matching_results:
        avg_score = sum(r["match_score"] for r in matching_results) / len(matching_results)
        print(f"\n📊 平均匹配分数: {avg_score:.3f}")
        
        if avg_score < 0.3:
            analysis["potential_issues"].append("BLIP caption匹配分数较低，可能需要优化检索索引")
    
    return matching_results

def main():
    """主函数"""
    print("🚀 开始深度分析Structure文件的检索索引")
    print("=" * 80)
    
    data_dir = "data"
    structure_files = [
        "Sense_A_Finetuned.fixed.jsonl",
        "Sense_B_Finetuned.fixed.jsonl"
    ]
    
    all_analyses = {}
    
    for filename in structure_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            data = load_jsonl_file(filepath)
            if data:
                print(f"\n{'='*80}")
                print(f"📁 分析文件: {filename}")
                print(f"{'='*80}")
                
                # 分析检索索引
                retrieval_analysis = analyze_retrieval_indexing(data[0], filename)
                
                # 分析全局检索字段
                global_analysis = analyze_global_retrieval(data[0], filename)
                
                # 模拟BLIP匹配
                matching_results = simulate_blip_matching(retrieval_analysis, filename)
                
                # 合并分析结果
                all_analyses[filename] = {
                    "retrieval": retrieval_analysis,
                    "global": global_analysis,
                    "matching": matching_results
                }
        else:
            print(f"❌ 文件不存在: {filepath}")
    
    # 生成总结和建议
    print(f"\n{'='*80}")
    print("📋 分析总结和建议")
    print(f"{'='*80}")
    
    for filename, analysis in all_analyses.items():
        print(f"\n📁 {filename}:")
        
        # 检索字段覆盖率
        retrieval = analysis["retrieval"]
        if "retrieval_coverage" in retrieval and retrieval["retrieval_coverage"]:
            coverage = retrieval["retrieval_coverage"]
            if "coverage_percentage" in coverage:
                print(f"   📊 检索字段覆盖率: {coverage['coverage_percentage']:.1f}%")
            else:
                print(f"   📊 检索字段覆盖率: 未计算")
        else:
            print(f"   📊 检索字段覆盖率: 无法计算")
        
        # 潜在问题
        all_issues = []
        if "potential_issues" in retrieval:
            all_issues.extend(retrieval["potential_issues"])
        if "potential_issues" in analysis["global"]:
            all_issues.extend(analysis["global"]["potential_issues"])
        
        if all_issues:
            print(f"   ⚠️ 发现 {len(all_issues)} 个潜在问题:")
            for issue in all_issues[:5]:  # 只显示前5个
                print(f"      - {issue}")
            if len(all_issues) > 5:
                print(f"      ... 还有 {len(all_issues) - 5} 个问题")
        else:
            print(f"   ✅ 未发现明显问题")
    
    print(f"\n🎯 改进建议:")
    print("   1. 确保所有节点都有完整的retrieval字段")
    print("   2. 优化index_terms，使其更贴近BLIP caption")
    print("   3. 增加tags的多样性和相关性")
    print("   4. 定期更新keywords以匹配新的用户描述")
    
    print(f"\n📊 深度分析完成！共分析了 {len(all_analyses)} 个Structure文件")

if __name__ == "__main__":
    main()
