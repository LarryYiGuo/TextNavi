#!/usr/bin/env python3
"""
创建正确的Sense_B_Finetuned.fixed.jsonl文件
"""

import json
import os

def create_correct_textmap():
    """创建正确的textmap文件"""
    
    # 正确的拓扑结构
    correct_topology = {
        "nodes": [
            {
                "id": "dp_studio_entrance",
                "type": "junction",
                "name": "Studio entrance central line (inside)",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["segment_summary"],
                "landmarks": ["lm_glass_doors_back", "lm_yellow_line", "lm_entrance_area"],
                "categories": ["junction", "portal"],
                "retrieval": {
                    "index_terms": ["Studio entrance", "entrance", "yellow floor line", "yellow line", "floor yellow line", "yellow tape line", "yellow floor marking", "yellow path", "entrance area", "door"],
                    "tags": ["entrance", "portal", "navigation", "path", "floor marking", "yellow", "line"]
                }
            },
            {
                "id": "yline_start",
                "type": "junction",
                "name": "Yellow line start",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["segment_summary"],
                "landmarks": ["lm_yellow_line"],
                "categories": ["junction"],
                "retrieval": {
                    "index_terms": ["Yellow line start", "yellow line start", "floor yellow line", "yellow tape line", "yellow floor marking", "yellow path", "yellow line begins", "yellow line origin", "yellow strip", "yellow marking"],
                    "tags": ["navigation", "path", "floor marking", "yellow", "line", "start"]
                }
            },
            {
                "id": "workstation_zone",
                "type": "poi",
                "name": "Main workstation area with computers",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["prominent_landmark"],
                "landmarks": ["lm_workstation_desks", "lm_computer_monitors"],
                "categories": ["poi", "work_area"],
                "retrieval": {
                    "index_terms": ["workstation zone", "main workstation area", "workstation desks", "computer monitors", "work area", "desks with monitors", "computer workstations", "work tables", "monitor desks", "workstation area"],
                    "tags": ["workstation", "desks", "computers", "monitors", "work area", "technology"]
                }
            },
            {
                "id": "disability_innovation_sign",
                "type": "landmark",
                "name": "Disability Innovation sign area",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["prominent_landmark"],
                "landmarks": ["lm_disability_sign", "lm_global_disability_hub"],
                "categories": ["landmark", "poi"],
                "retrieval": {
                    "index_terms": ["Disability Innovation sign", "Disability Innovation", "Global Disability Innovation Hub", "Global Disability Innovation", "Disability Innovation Hub", "large sign", "purple letters", "3D letters", "prominent sign", "Disability Innovation area"],
                    "tags": ["landmark", "sign", "Disability Innovation", "Global Disability Innovation Hub", "purple", "3D", "prominent"]
                }
            },
            {
                "id": "glass_cage_room",
                "type": "poi",
                "name": "The CAGE glass room",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["prominent_landmark"],
                "landmarks": ["lm_glass_room", "lm_cage_sign"],
                "categories": ["poi", "room"],
                "retrieval": {
                    "index_terms": ["The CAGE", "CAGE", "glass room", "glass enclosure", "glass partition", "glass walled room", "glass office", "glass room office", "glass enclosed room", "The CAGE room"],
                    "tags": ["room", "glass", "enclosure", "partition", "CAGE", "office"]
                }
            },
            {
                "id": "lounge_area",
                "type": "poi",
                "name": "Lounge area with colorful seating",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["prominent_landmark"],
                "landmarks": ["lm_colorful_chairs", "lm_beanbag_chairs"],
                "categories": ["poi", "lounge"],
                "retrieval": {
                    "index_terms": ["lounge area", "colorful seating", "colorful chairs", "beanbag chairs", "beanbags", "soft seating", "bright seating", "colorful furniture", "lounge furniture", "comfortable seating"],
                    "tags": ["lounge", "seating", "colorful", "beanbags", "soft", "comfortable"]
                }
            },
            {
                "id": "storage_zone",
                "type": "poi",
                "name": "Storage area with shelves and cabinets",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["prominent_landmark"],
                "landmarks": ["lm_storage_shelves", "lm_metal_cabinets"],
                "categories": ["poi", "storage"],
                "retrieval": {
                    "index_terms": ["storage zone", "storage area", "storage shelves", "metal cabinets", "storage cabinets", "shelves", "cabinets", "storage space", "storage area", "storage zone"],
                    "tags": ["storage", "shelves", "cabinets", "metal", "organization"]
                }
            },
            {
                "id": "equipment_corner",
                "type": "poi",
                "name": "Equipment corner with specialized tools",
                "level": "L2",
                "region_id": "gdi_studio",
                "rdl": ["segment_summary"],
                "landmarks": ["lm_specialized_equipment", "lm_tools"],
                "categories": ["destination", "poi"],
                "retrieval": {
                    "index_terms": ["equipment corner", "specialized equipment", "specialized tools", "tools", "equipment", "equipment area", "tool area", "specialized area", "equipment corner", "specialized corner"],
                    "tags": ["equipment", "tools", "specialized", "corner", "destination"]
                }
            }
        ],
        "edges": [
            {
                "from": "dp_studio_entrance",
                "to": "yline_start",
                "kind": "open_area",
                "turn_hint": "straight",
                "step_count": 1
            },
            {
                "from": "yline_start",
                "to": "workstation_zone",
                "kind": "open_area",
                "turn_hint": "follow_line",
                "step_count": 3
            },
            {
                "from": "workstation_zone",
                "to": "disability_innovation_sign",
                "kind": "open_area",
                "turn_hint": "straight",
                "step_count": 2
            },
            {
                "from": "disability_innovation_sign",
                "to": "glass_cage_room",
                "kind": "open_area",
                "turn_hint": "right",
                "step_count": 2
            },
            {
                "from": "glass_cage_room",
                "to": "lounge_area",
                "kind": "open_area",
                "turn_hint": "left",
                "step_count": 3
            },
            {
                "from": "lounge_area",
                "to": "storage_zone",
                "kind": "open_area",
                "turn_hint": "straight",
                "step_count": 2
            },
            {
                "from": "storage_zone",
                "to": "equipment_corner",
                "kind": "open_area",
                "turn_hint": "right",
                "step_count": 2
            }
        ]
    }
    
    # 创建完整的textmap结构
    textmap_data = {
        "input": {
            "room": "UCL East - Global Disability Innovation Hub",
            "location": "Studio — inside entrance facing the yellow floor line (workspace included)",
            "site_id": "SCENE_B_STUDIO"
        },
        "topology": correct_topology,
        "output": "Inside the Studio entrance, the yellow floor line begins and leads to the main workstation area with computer monitors and desks. A large Disability Innovation sign with purple 3D letters is prominently displayed, marking the entrance to a glass room called The CAGE, which houses the Global Disability Innovation Hub. The lounge area features colorful chairs and beanbag seating, while the storage zone contains metal shelves and cabinets. The equipment corner holds specialized tools and equipment for various projects."
    }
    
    # 保存文件
    file_path = os.path.join(os.path.dirname(__file__), "data", "Sense_B_Finetuned.fixed.jsonl")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(textmap_data, f, ensure_ascii=False, indent=2)
    
    # 验证
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        nodes_count = len(data.get("topology", {}).get("nodes", []))
        print(f"✅ 文件创建成功，节点数量: {nodes_count}")
        print(f"✅ 文件已保存: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 文件创建失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 开始创建正确的textmap文件...")
    success = create_correct_textmap()
    if success:
        print("🎉 创建完成！")
    else:
        print("❌ 创建失败！")
