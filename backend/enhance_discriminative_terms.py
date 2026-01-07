#!/usr/bin/env python3
"""
为关键节点添加增强的判别词和反证词
"""

import json
import copy

def enhance_discriminative_terms():
    """为关键节点添加增强的判别词和反证词"""
    
    # 读取原始数据
    with open('data/Sense_A_Finetuned.fixed.jsonl', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 增强的判别词和反证词配置
    enhancements = {
        "chair_on_yline": {
            "cnl_index": [
                "chair directly on yellow floor line",
                "yellow line underfoot", 
                "near entrance",
                "no window adjacency",
                "single brown office chair",
                "yellow floor marking visible"
            ],
            "index_terms": [
                "yellow line", "floor guide", "entrance-adjacent", "chair",
                "brown seat", "black back", "office chair", "yellow path"
            ],
            "negative": [
                "not near windows", "not multiple benches", "not storage corner",
                "not work area", "not desk cluster", "not multiple tables"
            ]
        },
        "desks_cluster": {
            "cnl_index": [
                "multiple work tables with tools/bins/boxes",
                "near windows", 
                "not on yellow floor line",
                "workstation area",
                "computer monitors",
                "office workspace"
            ],
            "index_terms": [
                "work tables", "bins", "boxes", "windows",
                "desks cluster", "workstation", "office area", "monitors"
            ],
            "negative": [
                "no yellow line underfoot", "not at entrance",
                "not single chair", "not yellow path"
            ]
        },
        "small_table_mid": {
            "cnl_index": [
                "low meeting table in aisle",
                "between TV and orange sofa",
                "white round table",
                "not on yellow line",
                "obstacle in path"
            ],
            "index_terms": [
                "low table", "meeting table", "white table", "aisle table",
                "round table", "obstacle", "path table"
            ],
            "negative": [
                "not yellow line", "not entrance area", "not multiple desks",
                "not workstation", "not near windows"
            ]
        },
        "atrium_edge": {
            "cnl_index": [
                "large windows with soft seats",
                "atrium threshold",
                "natural light",
                "outdoor view",
                "soft seating area"
            ],
            "index_terms": [
                "windows", "soft seats", "beanbags", "natural light",
                "atrium", "outdoor view", "seating area"
            ],
            "negative": [
                "not yellow line", "not entrance", "not work area",
                "not storage", "not single chair"
            ]
        }
    }
    
    # 应用增强
    nodes = data['input']['topology']['nodes']
    for node in nodes:
        node_id = node['id']
        if node_id in enhancements:
            print(f"🔧 增强节点: {node_id}")
            
            # 确保retrieval字段存在
            if 'retrieval' not in node:
                node['retrieval'] = {}
            
            # 更新cnl_index
            if 'cnl_index' not in node['retrieval']:
                node['retrieval']['cnl_index'] = []
            node['retrieval']['cnl_index'].extend(enhancements[node_id]['cnl_index'])
            
            # 更新index_terms
            if 'index_terms' not in node['retrieval']:
                node['retrieval']['index_terms'] = []
            node['retrieval']['index_terms'].extend(enhancements[node_id]['index_terms'])
            
            # 添加negative字段
            node['retrieval']['negative'] = enhancements[node_id]['negative']
            
            print(f"   ✅ 添加 {len(enhancements[node_id]['cnl_index'])} 个cnl_index")
            print(f"   ✅ 添加 {len(enhancements[node_id]['index_terms'])} 个index_terms") 
            print(f"   ✅ 添加 {len(enhancements[node_id]['negative'])} 个negative提示")
    
    # 保存增强后的数据
    output_file = 'data/Sense_A_Finetuned_enhanced.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 增强完成！保存到: {output_file}")
    return output_file

def test_enhanced_terms():
    """测试增强的判别词效果"""
    print("\n🧪 测试增强的判别词效果")
    print("=" * 50)
    
    # 测试查询
    test_queries = [
        "there is a computer monitor sitting on a desk in a room",
        "there is a large pile of black bins on a desk",
        "there is a cat sitting on a chair in a room",
        "there are many different types of electronics on the table"
    ]
    
    # 模拟节点信息
    nodes_info = {
        "chair_on_yline": {
            "cnl_index": ["chair directly on yellow floor line", "yellow line underfoot", "near entrance"],
            "index_terms": ["yellow line", "floor guide", "entrance-adjacent", "chair"],
            "negative": ["not near windows", "not multiple benches", "not storage corner", "not work area", "not desk cluster"]
        },
        "desks_cluster": {
            "cnl_index": ["multiple work tables with tools/bins/boxes", "near windows", "not on yellow floor line"],
            "index_terms": ["work tables", "bins", "boxes", "windows"],
            "negative": ["no yellow line underfoot", "not at entrance", "not single chair"]
        }
    }
    
    for query in test_queries:
        print(f"\n📸 查询: {query}")
        print("-" * 30)
        
        for node_id, node_info in nodes_info.items():
            # 计算正向匹配分数
            positive_score = 0
            for term in node_info['index_terms']:
                if term.lower() in query.lower():
                    positive_score += 1
            
            # 计算反证惩罚
            negative_penalty = 0
            for neg_term in node_info['negative']:
                if neg_term.lower() in query.lower():
                    negative_penalty += 0.15
            
            # 最终分数
            final_score = positive_score - negative_penalty
            
            print(f"  {node_id}:")
            print(f"    正向匹配: {positive_score:.2f}")
            print(f"    反证惩罚: {negative_penalty:.2f}")
            print(f"    最终分数: {final_score:.2f}")

def main():
    """主函数"""
    print("🔧 为关键节点添加增强的判别词和反证词")
    print("=" * 60)
    
    # 增强数据
    output_file = enhance_discriminative_terms()
    
    # 测试效果
    test_enhanced_terms()
    
    print("\n" + "=" * 60)
    print("📊 增强完成")
    print("\n💡 主要改进:")
    print("1. ✅ 为chair_on_yline添加了yellow line、entrance等判别词")
    print("2. ✅ 为desks_cluster添加了work tables、windows等判别词")
    print("3. ✅ 为small_table_mid添加了low table、aisle等判别词")
    print("4. ✅ 为atrium_edge添加了windows、soft seats等判别词")
    print("5. ✅ 添加了negative反证提示，命中时施加惩罚")
    print("\n🎯 预期效果:")
    print("- 结构通道的0.488/0.488打平情况减少")
    print("- 更准确的节点区分")
    print("- 减少chair_on_yline的误识别")

if __name__ == "__main__":
    main()
