#!/usr/bin/env python3
"""
测试语义匹配问题，特别是为什么chair_on_yline总是被错误识别
"""

import json
import re

def load_structure_data():
    """加载结构数据"""
    try:
        with open('data/Sense_A_Finetuned.fixed.jsonl', 'r', encoding='utf-8') as f:
            content = f.read()
            data = json.loads(content)
            return data
    except Exception as e:
        print(f"❌ 加载结构数据失败: {e}")
        return None

def analyze_node_index_terms(data):
    """分析节点的索引词"""
    if not data or 'input' not in data or 'topology' not in data['input']:
        print("❌ 数据结构不完整")
        return
    
    nodes = data['input']['topology']['nodes']
    print("🔍 分析节点索引词和语义匹配")
    print("=" * 60)
    
    # 测试图片描述
    test_captions = [
        "there is a table with a bunch of electronics on it",
        "there is a book shelf with books and a sign on it", 
        "there is a cat sitting on a chair in a room",
        "there are many different types of electronics on the table"
    ]
    
    for caption in test_captions:
        print(f"\n📸 测试图片描述: {caption}")
        print("-" * 40)
        
        # 分析每个节点的匹配度
        node_scores = []
        for node in nodes:
            node_id = node['id']
            index_terms = node.get('retrieval', {}).get('index_terms', [])
            
            # 计算匹配分数
            score = 0
            matched_terms = []
            
            # 检查关键词匹配
            caption_lower = caption.lower()
            for term in index_terms:
                term_lower = term.lower()
                if term_lower in caption_lower:
                    score += 1
                    matched_terms.append(term)
                # 检查部分匹配
                elif any(word in caption_lower for word in term_lower.split()):
                    score += 0.5
                    matched_terms.append(f"{term}(partial)")
            
            if score > 0:
                node_scores.append({
                    'node_id': node_id,
                    'score': score,
                    'matched_terms': matched_terms,
                    'index_terms': index_terms[:5]  # 只显示前5个
                })
        
        # 按分数排序
        node_scores.sort(key=lambda x: x['score'], reverse=True)
        
        print("🏆 匹配结果排序:")
        for i, result in enumerate(node_scores[:5]):
            print(f"  {i+1}. {result['node_id']}: {result['score']:.1f}分")
            print(f"     匹配词: {', '.join(result['matched_terms'])}")
            print(f"     索引词: {', '.join(result['index_terms'])}")
            print()

def analyze_chair_on_yline_bias(data):
    """分析chair_on_yline的偏差"""
    if not data or 'input' not in data or 'topology' not in data['input']:
        return
    
    nodes = data['input']['topology']['nodes']
    chair_node = None
    
    for node in nodes:
        if node['id'] == 'chair_on_yline':
            chair_node = node
            break
    
    if not chair_node:
        print("❌ 未找到chair_on_yline节点")
        return
    
    print("🔍 分析chair_on_yline的索引词")
    print("=" * 40)
    
    index_terms = chair_node.get('retrieval', {}).get('index_terms', [])
    print(f"索引词数量: {len(index_terms)}")
    print("索引词列表:")
    for i, term in enumerate(index_terms):
        print(f"  {i+1}. {term}")
    
    # 检查是否有过于宽泛的索引词
    broad_terms = []
    for term in index_terms:
        if len(term.split()) <= 2:  # 短词可能过于宽泛
            broad_terms.append(term)
    
    if broad_terms:
        print(f"\n⚠️ 可能过于宽泛的索引词: {', '.join(broad_terms)}")
        print("这些词可能导致误匹配")

def main():
    """主函数"""
    print("🧪 测试语义匹配问题")
    print("=" * 60)
    
    # 加载数据
    data = load_structure_data()
    if not data:
        return
    
    # 分析节点索引词
    analyze_node_index_terms(data)
    
    # 分析chair_on_yline偏差
    analyze_chair_on_yline_bias(data)
    
    print("\n" + "=" * 60)
    print("📊 分析完成")
    print("\n💡 建议:")
    print("1. 检查chair_on_yline的索引词是否过于宽泛")
    print("2. 调整结构通道和细节通道的权重")
    print("3. 增强语义去重逻辑")
    print("4. 添加内容相关性检查")

if __name__ == "__main__":
    main()
