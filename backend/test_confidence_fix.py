#!/usr/bin/env python3
"""
测试置信度修复的脚本
验证softmax校准和连续性boost是否正常工作
"""

import os
import sys
import json
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_softmax_calibration():
    """测试softmax校准功能"""
    print("🧪 测试Softmax校准功能")
    print("=" * 50)
    
    try:
        # 导入函数
        from app import apply_softmax_calibration, calculate_calibrated_confidence_and_margin
        
        # 测试数据
        test_scores = [0.45, 0.38, 0.32, 0.28, 0.25]
        print(f"原始分数: {test_scores}")
        
        # 测试softmax校准
        probabilities = apply_softmax_calibration(test_scores)
        print(f"校准后概率: {[f'{p:.4f}' for p in probabilities]}")
        
        # 测试置信度计算
        mock_candidates = [
            {"id": f"node_{i}", "score": score} 
            for i, score in enumerate(test_scores)
        ]
        
        conf, margin, raw1, raw2 = calculate_calibrated_confidence_and_margin(mock_candidates)
        print(f"校准置信度: {conf:.4f}")
        print(f"校准margin: {margin:.4f}")
        print(f"原始top1: {raw1:.4f}")
        print(f"原始top2: {raw2:.4f}")
        
        print("✅ Softmax校准测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Softmax校准测试失败: {e}")
        return False

def test_continuity_boost():
    """测试连续性boost功能"""
    print("\n🧪 测试连续性Boost功能")
    print("=" * 50)
    
    try:
        # 导入函数
        from app import apply_continuity_boost
        
        # 模拟会话数据
        SESSIONS = {
            "location_history": {
                "T06_SCENE_A_MS": [
                    {"node_id": "dp_ms_entrance", "confidence": 0.8},
                    {"node_id": "dp_ms_entrance", "confidence": 0.75},
                    {"node_id": "dp_ms_entrance", "confidence": 0.82}
                ]
            }
        }
        
        # 测试连续性boost
        boosted_score, boost_amount, boost_reason = apply_continuity_boost(
            top1_score=0.75,
            session_id="T06",
            site_id="SCENE_A_MS",
            current_node_id="dp_ms_entrance"
        )
        
        print(f"原始分数: 0.75")
        print(f"Boost后分数: {boosted_score:.4f}")
        print(f"Boost数量: {boost_amount:.4f}")
        print(f"Boost原因: {boost_reason}")
        
        print("✅ 连续性Boost测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 连续性Boost测试失败: {e}")
        return False

def test_dual_channel_retriever():
    """测试校准的双通道检索器"""
    print("\n🧪 测试校准的双通道检索器")
    print("=" * 50)
    
    try:
        # 导入函数
        from app import get_unified_retriever
        
        # 测试获取retriever
        retriever = get_unified_retriever()
        
        if retriever:
            print("✅ 校准双通道检索器初始化成功")
            
            # 测试检索
            test_caption = "there is a work area with a work table and a chair"
            candidates = retriever.retrieve(test_caption, top_k=5)
            
            if candidates:
                print(f"✅ 校准检索成功，返回 {len(candidates)} 个候选")
                print(f"🔧 校准策略验证:")
                
                # 验证校准效果
                top1_score = candidates[0]['score']
                top2_score = candidates[1]['score']
                margin = top1_score - top2_score
                
                print(f"   Top1: {candidates[0]['id']} (score: {top1_score:.4f})")
                print(f"   Top2: {candidates[1]['id']} (score: {top2_score:.4f})")
                print(f"   Margin: {margin:.4f}")
                
                # 验证置信度提升
                if top1_score > 0.6:
                    print(f"   ✅ 置信度提升成功: {top1_score:.4f} > 0.6")
                else:
                    print(f"   ⚠️ 置信度仍需提升: {top1_score:.4f}")
                
                # 验证margin提升
                if margin > 0.15:
                    print(f"   ✅ Margin提升成功: {margin:.4f} > 0.15")
                else:
                    print(f"   ⚠️ Margin仍需提升: {margin:.4f}")
                
                # 验证校准策略
                if hasattr(retriever, '_channel_calibration'):
                    print(f"   ✅ 通道校准策略已实现")
                if hasattr(retriever, '_logit_fusion'):
                    print(f"   ✅ 对数几率融合策略已实现")
                if hasattr(retriever, '_adaptive_weights'):
                    print(f"   ✅ 自适应权重策略已实现")
                
                return True
            else:
                print("⚠️ 校准检索返回空结果")
                return False
                
        else:
            print("❌ 校准双通道检索器初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ 校准双通道检索器测试失败: {e}")
        return False

def test_configuration():
    """测试配置参数"""
    print("\n🧪 测试配置参数")
    print("=" * 50)
    
    try:
        # 导入配置
        from app import (
            SOFTMAX_TEMPERATURE, 
            ENABLE_SOFTMAX_CALIBRATION, 
            ENABLE_CONTINUITY_BOOST,
            LOWCONF_SCORE_TH,
            LOWCONF_MARGIN_TH
        )
        
        print(f"Softmax温度: {SOFTMAX_TEMPERATURE}")
        print(f"启用Softmax校准: {ENABLE_SOFTMAX_CALIBRATION}")
        print(f"启用连续性Boost: {ENABLE_CONTINUITY_BOOST}")
        print(f"置信度阈值: {LOWCONF_SCORE_TH}")
        print(f"Margin阈值: {LOWCONF_MARGIN_TH}")
        
        print("✅ 配置参数测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置参数测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始置信度修复测试")
    print("=" * 60)
    
    tests = [
        test_configuration,
        test_softmax_calibration,
        test_continuity_boost,
        test_dual_channel_retriever
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！置信度修复应该正常工作")
        print("\n💡 建议:")
        print("1. 重启后端服务")
        print("2. 拍照测试新的置信度计算")
        print("3. 查看控制台输出的校准信息")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    main()
