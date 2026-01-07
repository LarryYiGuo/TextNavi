#!/usr/bin/env python3
"""
测试语义去重修复的脚本
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_semantic_deduplication():
    """测试语义去重功能"""
    print("🔍 测试语义去重功能...")
    
    # 模拟EnhancedDualChannelRetriever类
    class MockRetriever:
        def _semantic_deduplication(self, candidates, caption_lower):
            """语义去重：合并语义相似的节点，避免返回重复的TV screen等"""
            if not candidates:
                return candidates
            
            # 定义语义相似组
            semantic_groups = {
                "tv_screen_group": [
                    "tv screen", "large tv screen", "large tv screen near entry",
                    "tv", "television", "display", "screen", "monitor"
                ],
                "window_group": [
                    "glass window", "window wall", "windows", "glass", "window"
                ],
                "sofa_group": [
                    "orange sofa", "sofa", "couch", "seating", "chair"
                ],
                "space_group": [
                    "open space", "large open space", "open area", "atrium", "space"
                ],
                "boxes_group": [
                    "boxes", "box", "cardboard", "stacked", "floor", "on floor"
                ],
                "table_group": [
                    "table", "desk", "workbench", "surface", "counter"
                ],
                "storage_group": [
                    "storage", "shelf", "cabinet", "drawer", "container"
                ]
            }
            
            # 按语义组分组候选
            grouped_candidates = {}
            for candidate in candidates:
                candidate_id = candidate["id"].lower()
                candidate_text = candidate.get("text", "").lower()
                candidate_name = candidate.get("name", "").lower()
                
                # 检查属于哪个语义组
                assigned_group = None
                best_match_score = 0
                
                for group_name, keywords in semantic_groups.items():
                    match_score = 0
                    for keyword in keywords:
                        # 检查候选的各个字段
                        if keyword in candidate_id:
                            match_score += 2  # ID匹配给予最高权重
                        if keyword in candidate_text:
                            match_score += 1.5  # 文本匹配给予高权重
                        if keyword in candidate_name:
                            match_score += 1.0  # 名称匹配给予中等权重
                    
                    # 选择匹配度最高的组
                    if match_score > best_match_score:
                        best_match_score = match_score
                        assigned_group = group_name
                
                # 如果匹配度太低，则不分组
                if best_match_score < 1.0:
                    assigned_group = None
                
                if assigned_group:
                    if assigned_group not in grouped_candidates:
                        grouped_candidates[assigned_group] = []
                    grouped_candidates[assigned_group].append(candidate)
                else:
                    # 不属于任何组的候选，单独处理
                    if "other" not in grouped_candidates:
                        grouped_candidates["other"] = []
                    grouped_candidates["other"].append(candidate)
            
            # 对每个语义组，选择最高分的候选
            deduplicated = []
            for group_name, group_candidates in grouped_candidates.items():
                if group_name == "other":
                    # 其他候选直接添加
                    deduplicated.extend(group_candidates)
                else:
                    # 语义组选择最高分的
                    if len(group_candidates) > 1:
                        print(f"🔍 Semantic deduplication: {group_name} has {len(group_candidates)} candidates")
                        for i, cand in enumerate(group_candidates):
                            print(f"   {i+1}. {cand['id']} (score: {cand['score']:.3f})")
                    
                    # 选择最高分的候选
                    best_candidate = max(group_candidates, key=lambda x: x["score"])
                    best_candidate["semantic_group"] = group_name
                    best_candidate["merged_candidates"] = len(group_candidates)
                    deduplicated.append(best_candidate)
            
            print(f"🔍 Semantic deduplication: {len(candidates)} → {len(deduplicated)} candidates")
            return deduplicated
    
    # 创建测试数据
    test_candidates = [
        {"id": "boxes on floor", "text": "boxes on floor", "name": "boxes on floor", "score": 0.602},
        {"id": "cardboard boxes", "text": "cardboard boxes", "name": "cardboard boxes", "score": 0.550},
        {"id": "open atrium ahead beyond stacked boxes", "text": "open atrium ahead beyond stacked boxes", "name": "open atrium ahead beyond stacked boxes", "score": 0.417},
        {"id": "tv screen", "text": "large tv screen", "name": "tv zone", "score": 0.800},
        {"id": "display monitor", "text": "computer monitor", "name": "monitor area", "score": 0.750},
        {"id": "orange sofa", "text": "orange sofa corner", "name": "sofa area", "score": 0.600},
        {"id": "chair seating", "text": "chair on yellow line", "name": "chair zone", "score": 0.550}
    ]
    
    print("🧪 测试候选列表:")
    for i, candidate in enumerate(test_candidates):
        print(f"   {i+1}. {candidate['id']} (score: {candidate['score']:.3f})")
    
    # 测试语义去重
    retriever = MockRetriever()
    caption = "there are boxes on the floor with some cardboard boxes"
    deduplicated = retriever._semantic_deduplication(test_candidates, caption.lower())
    
    print(f"\n🔍 去重结果:")
    for i, candidate in enumerate(deduplicated):
        semantic_group = candidate.get("semantic_group", "other")
        merged_count = candidate.get("merged_candidates", 1)
        print(f"   {i+1}. {candidate['id']} (score: {candidate['score']:.3f}) - {semantic_group} (merged {merged_count})")

if __name__ == "__main__":
    print("🧪 语义去重修复测试")
    print("=" * 50)
    
    test_semantic_deduplication()
    
    print("\n✅ 测试完成!")
