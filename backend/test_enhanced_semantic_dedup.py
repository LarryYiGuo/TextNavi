#!/usr/bin/env python3
"""
测试增强的语义去重功能
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_enhanced_semantic_dedup():
    """测试增强的语义去重功能"""
    print("🧪 测试增强的语义去重功能")
    print("=" * 60)
    
    # 模拟测试候选
    test_candidates = [
        {"id": "chair_on_yline", "score": 1.000, "text": "chair on yellow line", "name": "Chair on Y-line"},
        {"id": "orange_sofa_corner", "score": 0.000, "text": "orange sofa corner", "name": "Orange Sofa"},
        {"id": "small_table_mid", "score": 0.200, "text": "small table middle", "name": "Small Table"},
        {"id": "desks_cluster", "score": 1.000, "text": "desks cluster", "name": "Desks Cluster"},
        {"id": "atrium_edge", "score": 0.150, "text": "atrium edge", "name": "Atrium Edge"},
        {"id": "dp_ms_entrance", "score": 0.000, "text": "dp maker space entrance", "name": "DP MS Entrance"},
        {"id": "yline_start", "score": 0.000, "text": "yellow line start", "name": "Y-line Start"},
        {"id": "yline_bend_mid", "score": 0.000, "text": "yellow line bend middle", "name": "Y-line Bend"},
        {"id": "tv_zone", "score": 0.000, "text": "tv zone", "name": "TV Zone"},
        {"id": "storage_corner", "score": 0.000, "text": "storage corner", "name": "Storage Corner"}
    ]
    
    print("📋 测试候选列表:")
    for i, cand in enumerate(test_candidates):
        print(f"   {i+1}. {cand['id']} (score: {cand['score']:.3f}) - {cand['text']}")
    
    print("\n🔍 语义分组分析:")
    print("1. chair_group: chair_on_yline, orange_sofa_corner")
    print("2. desk_group: desks_cluster")
    print("3. table_group: small_table_mid")
    print("4. space_group: atrium_edge, dp_ms_entrance")
    print("5. wall_group: yline_start, yline_bend_mid")
    print("6. tv_screen_group: tv_zone")
    print("7. storage_group: storage_corner")
    
    print("\n🎯 期望结果:")
    print("- chair_on_yline 和 orange_sofa_corner 应该合并到 chair_group")
    print("- desks_cluster 应该单独在 desk_group")
    print("- small_table_mid 应该单独在 table_group")
    print("- 最终应该从 10 个候选减少到 7 个候选")
    
    print("\n🧪 测试建议:")
    print("1. 运行系统，观察语义去重日志")
    print("2. 检查 chair_on_yline 和 desks_cluster 是否被正确分组")
    print("3. 验证 margin 是否从 0.0000 提升到合理值")

if __name__ == "__main__":
    test_enhanced_semantic_dedup()
    print("\n✅ 测试完成!")
