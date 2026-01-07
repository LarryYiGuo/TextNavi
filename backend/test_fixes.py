#!/usr/bin/env python3
"""
测试修复后的系统
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试关键模块导入"""
    print("🧪 测试关键模块导入")
    print("=" * 50)
    
    try:
        # 测试基本导入
        from app import enhanced_ft_retrieval, calculate_calibrated_confidence_and_margin
        print("✅ 基本函数导入成功")
        
        # 测试缺失函数处理
        from app import enhanced_metrics_collector
        print("✅ enhanced_metrics_collector 导入成功")
        
        # 测试get_location_description
        from app import get_location_description
        print("✅ get_location_description 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_confidence_calculation():
    """测试置信度计算"""
    print("\n🧪 测试置信度计算")
    print("=" * 50)
    
    try:
        from app import calculate_calibrated_confidence_and_margin
        
        # 模拟候选数据
        candidates = [
            {"id": "dp_ms_entrance", "score": 0.6577, "has_detail": False},
            {"id": "poi_3d_printer_table", "score": 0.2048, "has_detail": True},
            {"id": "dp_bookshelf_qr", "score": 0.0753, "has_detail": False}
        ]
        
        # 测试置信度计算
        confidence, margin, top1_score, top2_score = calculate_calibrated_confidence_and_margin(candidates)
        
        print(f"✅ 置信度计算成功:")
        print(f"   Confidence: {confidence:.4f}")
        print(f"   Margin: {margin:.4f}")
        print(f"   Top1 score: {top1_score:.4f}")
        print(f"   Top2 score: {top2_score:.4f}")
        
        # 验证结果合理性
        assert 0.0 <= confidence <= 1.0, "置信度应在0-1范围内"
        assert margin >= 0.0, "Margin应为非负数"
        assert confidence <= 0.65, "无detail时置信度应≤65%"
        
        print("✅ 置信度计算结果合理")
        return True
        
    except Exception as e:
        print(f"❌ 置信度计算测试失败: {e}")
        return False

def test_continuity_boost():
    """测试连续性boost"""
    print("\n🧪 测试连续性boost")
    print("=" * 50)
    
    try:
        from app import apply_continuity_boost
        
        # 测试连续性boost
        boost, reason = apply_continuity_boost(
            top1_score=0.6,
            session_id="T06",
            site_id="SCENE_B_STUDIO",
            current_node_id="dp_ms_entrance"
        )
        
        print(f"✅ 连续性boost计算成功:")
        print(f"   Boost: {boost:.4f}")
        print(f"   Reason: {reason}")
        
        # 验证boost范围
        assert -0.05 <= boost <= 0.10, "Boost应在-0.05到0.10范围内"
        
        print("✅ 连续性boost结果合理")
        return True
        
    except Exception as e:
        print(f"❌ 连续性boost测试失败: {e}")
        return False

def test_enhanced_ft_retrieval():
    """测试增强的FT检索"""
    print("\n🧪 测试增强的FT检索")
    print("=" * 50)
    
    try:
        from app import enhanced_ft_retrieval, get_unified_retriever
        
        # 获取retriever
        retriever = get_unified_retriever()
        if not retriever:
            print("❌ 无法获取unified retriever")
            return False
        
        print("✅ Unified retriever 获取成功")
        
        # 测试检索
        caption = "there is a room with a tv and a chair"
        site_id = "SCENE_B_STUDIO"
        
        candidates = enhanced_ft_retrieval(caption, retriever, site_id, [])
        
        if candidates:
            print(f"✅ 增强FT检索成功，返回 {len(candidates)} 个候选")
            
            # 检查第一个候选
            top1 = candidates[0]
            print(f"   Top1: {top1['id']} (score: {top1['score']:.4f})")
            print(f"   Has detail: {top1.get('has_detail', False)}")
            print(f"   Detail items: {top1.get('detail_items', 0)}")
            
            return True
        else:
            print("❌ 增强FT检索返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ 增强FT检索测试失败: {e}")
        return False

def test_dynamic_navigation():
    """测试动态导航"""
    print("\n🧪 测试动态导航")
    print("=" * 50)
    
    try:
        from app import generate_dynamic_navigation_response
        
        # 测试动态导航响应生成
        response = generate_dynamic_navigation_response(
            site_id="SCENE_B_STUDIO",
            node_id="dp_ms_entrance",
            confidence=0.7,
            low_conf=False,
            matching_data={},
            lang="en"
        )
        
        print(f"✅ 动态导航响应生成成功:")
        print(f"   Response: {response[:100]}...")
        
        assert response, "响应不应为空"
        assert "dp_ms_entrance" in response, "响应应包含节点ID"
        
        return True
        
    except Exception as e:
        print(f"❌ 动态导航测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试修复后的系统")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_confidence_calculation,
        test_continuity_boost,
        test_enhanced_ft_retrieval,
        test_dynamic_navigation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} 通过")
            else:
                print(f"❌ {test.__name__} 失败")
        except Exception as e:
            print(f"❌ {test.__name__} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统修复成功")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
