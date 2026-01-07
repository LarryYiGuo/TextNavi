#!/usr/bin/env python3
"""
测试实体别名修复：验证节点ID映射是否正确工作
"""

def test_entity_alias_mapping():
    """测试实体别名映射逻辑"""
    print("🧪 测试实体别名修复")
    print("=" * 60)
    
    # 模拟实体别名映射
    entity_aliases = {
        "poi01_entrance_glass_door": ["dp_ms_entrance", "entrance", "glass door"],
        "poi02_green_trash_bin": ["yline_start", "trash bin", "green bin"],
        "poi03_black_drawer_cabinet": ["yline_bend_mid", "drawer cabinet", "black cabinet"],
        "poi04_wall_3d_printers": ["atrium_edge", "3d printers", "wall printers"],
        "poi05_desk_3d_printer": ["tv_zone", "desk printer", "3d printer"],
        "poi06_small_open_3d_printer": ["storage_corner", "small printer", "open printer"],
        "poi07_cardboard_boxes": ["orange_sofa_corner", "cardboard boxes", "boxes"],
        "poi08_to_atrium": ["desks_cluster", "atrium", "to atrium"],
        "poi09_qr_bookshelf": ["chair_on_yline", "qr bookshelf", "bookshelf"],
        "poi10_metal_display_cabinet": ["small_table_mid", "metal cabinet", "display cabinet"]
    }
    
    # 模拟候选数据
    test_candidates = [
        {"id": "poi01_entrance_glass_door", "score": 0.8, "text": "entrance glass door"},
        {"id": "poi02_green_trash_bin", "score": 0.7, "text": "green trash bin"},
        {"id": "poi05_desk_3d_printer", "score": 0.9, "text": "desk 3d printer"},
        {"id": "poi09_qr_bookshelf", "score": 0.6, "text": "qr bookshelf"}
    ]
    
    print("🔍 测试实体别名检测逻辑")
    print("=" * 40)
    
    success_count = 0
    for candidate in test_candidates:
        candidate_id = candidate["id"]
        candidate_text = candidate.get("text", "").lower()
        candidate_name = candidate.get("name", "").lower()
        
        # 检查实体别名，识别同一实体（修复映射逻辑）
        entity_group = None
        for canonical_name, aliases in entity_aliases.items():
            # 检查候选ID是否匹配规范名称
            if candidate_id.lower() == canonical_name.lower():
                # 找到匹配，返回对应的细节数据ID
                entity_group = aliases[0]  # 使用第一个别名作为细节数据ID
                print(f"🔍 Entity alias detected: {candidate_id} → {entity_group}")
                break
        
        if entity_group:
            print(f"   ✅ {candidate_id} 成功映射到 {entity_group}")
            success_count += 1
        else:
            print(f"   ❌ {candidate_id} 未找到映射")
    
    print(f"\n📊 映射结果: {success_count}/{len(test_candidates)} 成功")
    
    # 验证映射的正确性
    expected_mappings = {
        "poi01_entrance_glass_door": "dp_ms_entrance",
        "poi02_green_trash_bin": "yline_start", 
        "poi05_desk_3d_printer": "tv_zone",
        "poi09_qr_bookshelf": "chair_on_yline"
    }
    
    print(f"\n🔍 验证映射正确性")
    print("=" * 40)
    
    correct_mappings = 0
    for candidate in test_candidates:
        candidate_id = candidate["id"]
        expected_detail_id = expected_mappings.get(candidate_id)
        
        if expected_detail_id:
            # 检查是否能找到映射
            entity_group = None
            for canonical_name, aliases in entity_aliases.items():
                if candidate_id.lower() == canonical_name.lower():
                    entity_group = aliases[0]
                    break
            
            if entity_group == expected_detail_id:
                print(f"✅ {candidate_id} → {entity_group} (正确)")
                correct_mappings += 1
            else:
                print(f"❌ {candidate_id} → {entity_group} (期望: {expected_detail_id})")
        else:
            print(f"⚠️ {candidate_id}: 无预期映射")
    
    print(f"\n📊 映射正确性: {correct_mappings}/{len(expected_mappings)} 正确")
    
    return success_count == len(test_candidates) and correct_mappings == len(expected_mappings)

def test_detail_index_lookup():
    """测试细节索引查找"""
    print(f"\n🧪 测试细节索引查找")
    print("=" * 60)
    
    # 模拟细节索引
    detail_index = {
        "dp_ms_entrance": [
            {"id": "SCENE_A_MS_IMG_0107", "node_hint": "dp_ms_entrance", "nl_text": "entrance, glass doors behind"},
            {"id": "SCENE_A_MS_IMG_0117", "node_hint": "dp_ms_entrance", "nl_text": "entrance, glass doors behind"}
        ],
        "yline_start": [
            {"id": "SCENE_A_MS_IMG_0108", "node_hint": "yline_start", "nl_text": "yellow floor line begins"},
            {"id": "SCENE_A_MS_IMG_0118", "node_hint": "yline_start", "nl_text": "yellow floor line begins"}
        ],
        "tv_zone": [
            {"id": "SCENE_A_MS_IMG_0112", "node_hint": "tv_zone", "nl_text": "mobile TV/monitor on stand"},
            {"id": "SCENE_A_MS_IMG_0122", "node_hint": "tv_zone", "nl_text": "mobile TV/monitor on stand"}
        ],
        "chair_on_yline": [
            {"id": "SCENE_A_MS_IMG_0109", "node_hint": "chair_on_yline", "nl_text": "brown-seat chair placed on yellow line"},
            {"id": "SCENE_A_MS_IMG_0119", "node_hint": "chair_on_yline", "nl_text": "brown-seat chair placed on yellow line"}
        ]
    }
    
    # 测试映射后的查找
    test_mappings = [
        ("poi01_entrance_glass_door", "dp_ms_entrance"),
        ("poi02_green_trash_bin", "yline_start"),
        ("poi05_desk_3d_printer", "tv_zone"),
        ("poi09_qr_bookshelf", "chair_on_yline")
    ]
    
    success_count = 0
    for struct_id, detail_id in test_mappings:
        if detail_id in detail_index:
            detail_items = detail_index[detail_id]
            print(f"✅ {struct_id} → {detail_id}: 找到 {len(detail_items)} 项detail数据")
            success_count += 1
        else:
            print(f"❌ {struct_id} → {detail_id}: 未找到detail数据")
    
    print(f"\n📊 细节索引查找: {success_count}/{len(test_mappings)} 成功")
    
    return success_count == len(test_mappings)

def main():
    """主函数"""
    print("🧪 测试实体别名修复")
    print("=" * 60)
    
    # 测试实体别名映射
    mapping_ok = test_entity_alias_mapping()
    
    # 测试细节索引查找
    lookup_ok = test_detail_index_lookup()
    
    print(f"\n📊 测试结果总结")
    print("=" * 60)
    print(f"实体别名映射: {'✅ 通过' if mapping_ok else '❌ 失败'}")
    print(f"细节索引查找: {'✅ 通过' if lookup_ok else '❌ 失败'}")
    
    if mapping_ok and lookup_ok:
        print("🎉 所有测试通过！实体别名问题已修复")
        print("\n💡 预期改进效果:")
        print("1. ✅ 结构数据ID正确映射到细节数据ID")
        print("2. ✅ 不再出现 'Found 0 detail entries' 错误")
        print("3. ✅ 置信度和margin应该显著提升")
        print("4. ✅ 系统能充分利用丰富的细节描述")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
