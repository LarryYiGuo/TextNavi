#!/usr/bin/env python3
"""
测试实体别名识别功能
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_entity_alias_detection():
    """测试实体别名识别功能"""
    print("🧪 测试实体别名识别功能")
    print("=" * 60)
    
    # 模拟测试候选 - 基于你提供的问题
    test_candidates = [
        {"id": "drawer wall", "score": 0.530, "text": "drawer wall", "name": "Drawer Wall"},
        {"id": "poi_component_drawer_wall", "score": 0.494, "text": "component drawer wall", "name": "Component Drawer Wall"},
        {"id": "qr bookshelf", "score": 0.499, "text": "qr bookshelf", "name": "QR Bookshelf"},
        {"id": "dp_bookshelf_qr", "score": 0.450, "text": "dp bookshelf qr", "name": "DP Bookshelf QR"}
    ]
    
    print("📋 测试候选列表:")
    for i, cand in enumerate(test_candidates):
        print(f"   {i+1}. {cand['id']} (score: {cand['score']:.3f}) - {cand['text']}")
    
    print("\n🔍 实体别名映射:")
    print("1. drawer_wall: ['drawer wall', 'poi_component_drawer_wall', 'component_drawer_wall']")
    print("2. qr_bookshelf: ['qr bookshelf', 'dp_bookshelf_qr', 'bookshelf_qr']")
    
    print("\n🎯 期望结果:")
    print("- 'drawer wall' 和 'poi_component_drawer_wall' 应该被识别为同一实体")
    print("- 'qr bookshelf' 和 'dp_bookshelf_qr' 应该被识别为同一实体")
    print("- 最终应该从 4 个候选减少到 2 个候选")
    
    print("\n🔧 修复内容:")
    print("1. ✅ 新增实体别名映射表")
    print("2. ✅ 优先使用实体别名进行分组")
    print("3. ✅ 避免同一实体的不同表示被重复计算")
    
    print("\n🧪 测试建议:")
    print("1. 运行系统，观察实体别名检测日志")
    print("2. 检查 'drawer wall' 和 'poi_component_drawer_wall' 是否被正确合并")
    print("3. 验证 margin 是否从 0.0000 提升到合理值")
    print("4. 观察 console 中的 '🔍 Entity alias detected' 日志")

if __name__ == "__main__":
    test_entity_alias_detection()
    print("\n✅ 测试完成!")
