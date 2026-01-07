#!/usr/bin/env python3
"""
测试分层架构 (Layered Fusion) 的脚本
验证Structure-only定位和Detail对话增强是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import (
    enhanced_ft_retrieval,
    get_detailed_matching_data,
    get_matching_data,
    find_node_details_by_hint
)

def test_layered_fusion():
    """测试分层架构的核心功能"""
    print("🧪 测试分层架构 (Layered Fusion)")
    print("=" * 50)
    
    # 测试场景
    site_id = "SCENE_A_MS"
    provider = "ft"
    
    print(f"📍 测试场景: {site_id}")
    print(f"🔧 Provider: {provider}")
    print()
    
    # 1. 测试Structure数据加载
    print("1️⃣ 测试Structure数据加载...")
    matching_data = get_matching_data(provider, site_id)
    if matching_data:
        print(f"   ✅ Structure数据加载成功: {len(matching_data)} 项")
        print(f"   📁 文件来源: {matching_data.get('source', 'Unknown')}")
    else:
        print("   ❌ Structure数据加载失败")
        return False
    print()
    
    # 2. 测试Detail数据加载
    print("2️⃣ 测试Detail数据加载...")
    detailed_data = get_detailed_matching_data(site_id)
    if detailed_data:
        print(f"   ✅ Detail数据加载成功: {len(detailed_data)} 项")
        # 显示前几个Detail项
        for i, item in enumerate(detailed_data[:3]):
            print(f"      {i+1}. {item.get('id', 'Unknown')} -> node_hint: {item.get('node_hint', 'None')}")
    else:
        print("   ❌ Detail数据加载失败")
        return False
    print()
    
    # 3. 测试数据对齐
    print("3️⃣ 测试数据对齐...")
    test_node_id = "dp_ms_entrance"
    node_details = find_node_details_by_hint(test_node_id, detailed_data)
    if node_details:
        print(f"   ✅ 节点 {test_node_id} 的Detail数据对齐成功: {len(node_details)} 项")
        for detail in node_details:
            print(f"      - {detail.get('id', 'Unknown')}")
            print(f"        spatial_relations: {detail.get('spatial_relations', {})}")
            print(f"        unique_features: {detail.get('unique_features', [])}")
    else:
        print(f"   ❌ 节点 {test_node_id} 的Detail数据对齐失败")
    print()
    
    # 4. 测试模拟检索
    print("4️⃣ 测试模拟检索...")
    # 模拟一个简单的retriever
    class MockRetriever:
        def retrieve(self, caption, top_k=10, scene_filter=None):
            # 返回模拟的候选结果
            return [
                {"id": "dp_ms_entrance", "score": 0.75, "type": "junction"},
                {"id": "yline_start", "score": 0.65, "type": "junction"},
                {"id": "chair_on_yline", "score": 0.55, "type": "poi"}
            ]
    
    mock_retriever = MockRetriever()
    test_caption = "I am at the Maker Space entrance with glass doors behind me"
    
    print(f"   📝 测试caption: {test_caption}")
    candidates = enhanced_ft_retrieval(test_caption, mock_retriever, site_id, detailed_data)
    
    if candidates:
        print(f"   ✅ 分层融合检索成功: {len(candidates)} 个候选")
        for i, candidate in enumerate(candidates[:3]):
            print(f"      {i+1}. {candidate['id']} (score: {candidate['score']:.3f})")
            print(f"         structure_score: {candidate.get('structure_score', 'N/A')}")
            print(f"         detail_score: {candidate.get('detail_score', 'N/A')}")
            print(f"         detail_metadata: {len(candidate.get('detail_metadata', []))} 项")
            print(f"         retrieval_method: {candidate.get('retrieval_method', 'N/A')}")
    else:
        print("   ❌ 分层融合检索失败")
        return False
    
    print()
    print("🎉 分层架构测试完成！")
    return True

def test_confidence_thresholds():
    """测试置信度阈值设置"""
    print("🔧 测试置信度阈值设置")
    print("=" * 30)
    
    # 从app.py导入阈值
    try:
        from app import LOWCONF_SCORE_TH, LOWCONF_MARGIN_TH
        print(f"   LOWCONF_SCORE_TH: {LOWCONF_SCORE_TH}")
        print(f"   LOWCONF_MARGIN_TH: {LOWCONF_MARGIN_TH}")
        
        # 测试阈值是否合理
        if LOWCONF_SCORE_TH <= 0.5:
            print("   ✅ 置信度阈值设置合理 (≤50%)")
        else:
            print("   ⚠️ 置信度阈值可能过高 (>50%)")
            
        if LOWCONF_MARGIN_TH <= 0.15:
            print("   ✅ 差异阈值设置合理 (≤15%)")
        else:
            print("   ⚠️ 差异阈值可能过高 (>15%)")
            
    except ImportError as e:
        print(f"   ❌ 无法导入阈值设置: {e}")
    
    print()

if __name__ == "__main__":
    print("🚀 启动分层架构测试...")
    print()
    
    # 测试置信度阈值
    test_confidence_thresholds()
    
    # 测试核心功能
    success = test_layered_fusion()
    
    if success:
        print("✅ 所有测试通过！分层架构工作正常。")
        sys.exit(0)
    else:
        print("❌ 测试失败！请检查实现。")
        sys.exit(1)
