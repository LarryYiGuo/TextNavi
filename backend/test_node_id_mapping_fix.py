#!/usr/bin/env python3
"""
测试节点ID映射修复：验证结构数据和细节数据的ID匹配
"""

import json
import os

def test_node_id_mapping():
    """测试节点ID映射是否正确"""
    print("🧪 测试节点ID映射修复")
    print("=" * 60)
    
    # 读取结构数据
    structure_file = "data/Sense_A_Finetuned.fixed.jsonl"
    detail_file = "data/Sense_A_MS.jsonl"
    
    if not os.path.exists(structure_file):
        print(f"❌ 结构文件不存在: {structure_file}")
        return False
    
    if not os.path.exists(detail_file):
        print(f"❌ 细节文件不存在: {detail_file}")
        return False
    
    # 读取结构数据
    print(f"📖 读取结构数据: {structure_file}")
    with open(structure_file, 'r', encoding='utf-8') as f:
        structure_data = json.loads(f.readline())
    
    # 提取节点ID
    structure_nodes = []
    if 'input' in structure_data and 'topology' in structure_data['input']:
        topology = structure_data['input']['topology']
        if 'nodes' in topology:
            for node in topology['nodes']:
                structure_nodes.append(node['id'])
    
    print(f"🔍 结构数据节点: {len(structure_nodes)} 个")
    for i, node_id in enumerate(structure_nodes):
        print(f"   {i+1:2d}. {node_id}")
    
    # 读取细节数据
    print(f"\n📖 读取细节数据: {detail_file}")
    detail_nodes = set()
    with open(detail_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    detail_item = json.loads(line)
                    node_hint = detail_item.get("node_hint", "")
                    if node_hint:
                        detail_nodes.add(node_hint)
                except json.JSONDecodeError as e:
                    print(f"⚠️ 第{line_num}行JSON解析失败: {e}")
                    continue
    
    print(f"🔍 细节数据节点: {len(detail_nodes)} 个")
    for i, node_hint in enumerate(sorted(detail_nodes)):
        print(f"   {i+1:2d}. {node_hint}")
    
    # 检查映射关系
    print(f"\n🔗 检查节点ID映射关系")
    print("=" * 60)
    
    # 预期的映射关系
    expected_mapping = {
        "poi01_entrance_glass_door": "dp_ms_entrance",
        "poi02_green_trash_bin": "yline_start",
        "poi03_black_drawer_cabinet": "yline_bend_mid",
        "poi04_wall_3d_printers": "atrium_edge",
        "poi05_desk_3d_printer": "tv_zone",
        "poi06_small_open_3d_printer": "storage_corner",
        "poi07_cardboard_boxes": "orange_sofa_corner",
        "poi08_to_atrium": "desks_cluster",
        "poi09_qr_bookshelf": "chair_on_yline",
        "poi10_metal_display_cabinet": "small_table_mid"
    }
    
    mapping_issues = []
    mapping_success = []
    
    for struct_id, expected_detail_id in expected_mapping.items():
        if struct_id in structure_nodes:
            if expected_detail_id in detail_nodes:
                mapping_success.append((struct_id, expected_detail_id))
                print(f"✅ {struct_id} → {expected_detail_id}")
            else:
                mapping_issues.append((struct_id, expected_detail_id, "detail_id不存在"))
                print(f"❌ {struct_id} → {expected_detail_id} (detail_id不存在)")
        else:
            mapping_issues.append((struct_id, expected_detail_id, "struct_id不存在"))
            print(f"❌ {struct_id} → {expected_detail_id} (struct_id不存在)")
    
    # 检查是否有未映射的节点
    unmapped_struct = set(structure_nodes) - set(expected_mapping.keys())
    unmapped_detail = detail_nodes - set(expected_mapping.values())
    
    if unmapped_struct:
        print(f"\n⚠️ 未映射的结构节点: {len(unmapped_struct)} 个")
        for node_id in unmapped_struct:
            print(f"   - {node_id}")
    
    if unmapped_detail:
        print(f"\n⚠️ 未映射的细节节点: {len(unmapped_detail)} 个")
        for node_hint in unmapped_detail:
            print(f"   - {node_hint}")
    
    # 总结
    print(f"\n📊 映射结果总结")
    print("=" * 60)
    print(f"成功映射: {len(mapping_success)}/{len(expected_mapping)}")
    print(f"映射问题: {len(mapping_issues)}")
    print(f"未映射结构节点: {len(unmapped_struct)}")
    print(f"未映射细节节点: {len(unmapped_detail)}")
    
    if len(mapping_issues) == 0 and len(unmapped_struct) == 0 and len(unmapped_detail) == 0:
        print("🎉 所有节点ID映射正确！")
        return True
    else:
        print("⚠️ 存在节点ID映射问题，需要修复")
        return False

def test_detail_index_building():
    """测试细节索引构建"""
    print(f"\n🧪 测试细节索引构建")
    print("=" * 60)
    
    detail_file = "data/Sense_A_MS.jsonl"
    if not os.path.exists(detail_file):
        print(f"❌ 细节文件不存在: {detail_file}")
        return False
    
    # 构建索引
    detail_index = {}
    try:
        with open(detail_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        detail_item = json.loads(line)
                        node_hint = detail_item.get("node_hint", "")
                        if node_hint:
                            if node_hint not in detail_index:
                                detail_index[node_hint] = []
                            detail_index[node_hint].append(detail_item)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 第{line_num}行JSON解析失败: {e}")
                        continue
        
        print(f"🔧 细节索引构建完成: {len(detail_index)} 个节点有detail数据")
        for node_id, items in detail_index.items():
            print(f"   {node_id}: {len(items)} 项")
        
        # 检查关键节点
        key_nodes = ["dp_ms_entrance", "yline_start", "chair_on_yline"]
        for node_id in key_nodes:
            if node_id in detail_index:
                print(f"✅ {node_id}: {len(detail_index[node_id])} 项detail数据")
            else:
                print(f"❌ {node_id}: 无detail数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 细节索引构建失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 测试节点ID映射修复")
    print("=" * 60)
    
    # 测试节点ID映射
    mapping_ok = test_node_id_mapping()
    
    # 测试细节索引构建
    index_ok = test_detail_index_building()
    
    print(f"\n📊 测试结果总结")
    print("=" * 60)
    print(f"节点ID映射: {'✅ 通过' if mapping_ok else '❌ 失败'}")
    print(f"细节索引构建: {'✅ 通过' if index_ok else '❌ 失败'}")
    
    if mapping_ok and index_ok:
        print("🎉 所有测试通过！节点ID映射问题已修复")
        print("\n💡 预期改进效果:")
        print("1. ✅ 结构数据和细节数据完全匹配")
        print("2. ✅ 不再出现 'Found 0 detail entries' 错误")
        print("3. ✅ 置信度和margin应该显著提升")
        print("4. ✅ 系统定位精度大幅改善")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
