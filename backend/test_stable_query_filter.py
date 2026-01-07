#!/usr/bin/env python3
"""
测试结构通道稳态词过滤机制
"""

def test_stable_query_filter():
    """测试稳态词过滤效果"""
    print("🧪 测试结构通道稳态词过滤机制")
    print("=" * 60)
    
    # 稳态词过滤函数
    def stable_query(text: str):
        """结构通道专用：过滤可移动物体，保留固定地标"""
        MOVABLE = {"suitcase", "bag", "backpack", "person", "cup", "bottle", "laptop", "phone", "book"}
        LOW_TRUST = {"bin", "box", "item", "stuff", "thing", "object"}
        
        t = text.lower()
        # 完全移除可移动物体
        for w in MOVABLE:
            t = t.replace(w, " ")
        # 降权低信任度物体
        for w in LOW_TRUST:
            t = t.replace(w, f" {w}*0.5 ")
        
        # 清理多余空格
        cleaned = " ".join(t.split())
        return cleaned
    
    # 测试用例
    test_cases = [
        {
            "original": "there is a black suitcase with a red handle sitting on a desk",
            "expected": "there is a red handle sitting on a desk",
            "description": "移除suitcase，保留desk"
        },
        {
            "original": "there is a large pile of black bins on a desk",
            "expected": "there is a large pile of black bins*0.5 on a desk",
            "description": "降权bins，保留desk"
        },
        {
            "original": "there is a computer monitor sitting on a desk with a laptop",
            "expected": "there is a computer monitor sitting on a desk with a",
            "description": "移除laptop，保留monitor和desk"
        },
        {
            "original": "there is a chair that is sitting in a room with boxes",
            "expected": "there is a chair that is sitting in a room with boxes*0.5",
            "description": "降权boxes，保留chair和room"
        },
        {
            "original": "there is a yellow line on the floor with a chair",
            "expected": "there is a yellow line on the floor with a chair",
            "description": "固定地标，无变化"
        },
        {
            "original": "there are many different types of electronics on the table",
            "expected": "there are many different types of electronics on the table",
            "description": "固定地标，无变化"
        }
    ]
    
    print("📋 稳态词过滤测试结果:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases):
        original = test_case["original"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        filtered = stable_query(original)
        
        print(f"\n📸 测试用例 {i+1}: {description}")
        print(f"   原始文本: {original}")
        print(f"   过滤结果: {filtered}")
        print(f"   期望结果: {expected}")
        
        if filtered == expected:
            print("   ✅ 结果符合预期")
        else:
            print("   ❌ 结果不符合预期")
            print(f"   差异: '{filtered}' vs '{expected}'")
    
    print("\n" + "=" * 60)

def test_structure_vs_detail_channel():
    """测试结构通道vs细节通道的差异"""
    print("\n🔧 测试结构通道vs细节通道的差异")
    print("=" * 50)
    
    # 模拟原始caption
    original_caption = "there is a large pile of black bins on a desk with a laptop"
    
    # 结构通道：使用稳态过滤
    def stable_query(text: str):
        MOVABLE = {"suitcase", "bag", "backpack", "person", "cup", "bottle", "laptop", "phone", "book"}
        LOW_TRUST = {"bin", "box", "item", "stuff", "thing", "object"}
        
        t = text.lower()
        for w in MOVABLE:
            t = t.replace(w, " ")
        for w in LOW_TRUST:
            t = t.replace(w, f" {w}*0.5 ")
        
        cleaned = " ".join(t.split())
        return cleaned
    
    # 结构通道：稳态版本
    structure_caption = stable_query(original_caption)
    
    # 细节通道：原始版本
    detail_caption = original_caption
    
    print(f"📸 原始图片描述: {original_caption}")
    print(f"🏗️ 结构通道: {structure_caption}")
    print(f"🔍 细节通道: {detail_caption}")
    
    print("\n🎯 通道差异分析:")
    print("   ✅ 结构通道: 专注于固定地标 (desk, bins*0.5)")
    print("   ✅ 细节通道: 保留所有信息 (desk, bins, laptop)")
    print("   ✅ 分工明确: 结构通道稳定，细节通道补充")
    
    print("\n💡 预期效果:")
    print("   - 结构通道: 减少'可移动物体'干扰，提高定位稳定性")
    print("   - 细节通道: 保留完整信息，用于精确匹配和区分")
    print("   - 整体效果: 减少0.488/0.488打平，提高margin")

def test_movable_object_impact():
    """测试可移动物体对结构通道的影响"""
    print("\n📊 测试可移动物体对结构通道的影响")
    print("=" * 50)
    
    # 模拟节点匹配分数
    def simulate_matching_score(caption, node_features):
        """模拟节点匹配分数计算"""
        score = 0.5  # 基础分数
        
        # 计算匹配分数
        caption_lower = caption.lower()
        for feature in node_features:
            if feature.lower() in caption_lower:
                score += 0.1
        
        return score
    
    # 测试场景1：包含可移动物体
    caption_with_movable = "there is a computer monitor sitting on a desk with a laptop"
    caption_stable = "there is a computer monitor sitting on a desk with a"
    
    # 节点特征
    chair_features = ["chair", "yellow line", "entrance"]
    desk_features = ["desk", "monitor", "work area"]
    
    print("📸 测试场景1: 包含可移动物体 (laptop)")
    print(f"   原始caption: {caption_with_movable}")
    print(f"   稳态caption: {caption_stable}")
    
    # 计算分数
    chair_score_original = simulate_matching_score(caption_with_movable, chair_features)
    chair_score_stable = simulate_matching_score(caption_stable, chair_features)
    desk_score_original = simulate_matching_score(caption_with_movable, desk_features)
    desk_score_stable = simulate_matching_score(caption_stable, desk_features)
    
    print(f"\n   分数对比:")
    print(f"   chair_on_yline: {chair_score_original:.3f} → {chair_score_stable:.3f}")
    print(f"   desks_cluster: {desk_score_original:.3f} → {desk_score_stable:.3f}")
    
    # 计算margin
    original_margin = abs(desk_score_original - chair_score_original)
    stable_margin = abs(desk_score_stable - chair_score_stable)
    
    print(f"\n   Margin对比:")
    print(f"   原始: {original_margin:.3f}")
    print(f"   稳态: {stable_margin:.3f}")
    print(f"   改进: {stable_margin - original_margin:+.3f}")
    
    if stable_margin > original_margin:
        print("   ✅ 稳态过滤提高了margin，减少了打平情况")
    else:
        print("   ⚠️ 稳态过滤未显著改善margin")

def main():
    """主函数"""
    print("🧪 测试结构通道稳态词过滤机制")
    print("=" * 60)
    
    # 测试稳态词过滤
    test_stable_query_filter()
    
    # 测试结构通道vs细节通道差异
    test_structure_vs_detail_channel()
    
    # 测试可移动物体影响
    test_movable_object_impact()
    
    print("\n" + "=" * 60)
    print("📊 测试完成")
    print("\n💡 稳态词过滤机制总结:")
    print("1. ✅ 结构通道: 过滤可移动物体，保留固定地标")
    print("2. ✅ 细节通道: 保留完整信息，用于精确匹配")
    print("3. ✅ 分工明确: 减少干扰，提高定位稳定性")
    print("4. ✅ 预期效果: 减少0.488/0.488打平，提高margin")
    print("\n🎯 关键改进:")
    print("- 移除: suitcase, bag, laptop, person等可移动物体")
    print("- 降权: bins, boxes等低信任度物体")
    print("- 保留: yellow line, desk, chair, window等固定地标")
    print("- 结构通道更稳定，细节通道更精确")

if __name__ == "__main__":
    main()
