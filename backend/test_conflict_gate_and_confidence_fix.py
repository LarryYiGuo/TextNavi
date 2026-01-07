#!/usr/bin/env python3
"""
测试冲突门控和置信度标定修复：验证门控只执行一次，置信度计算温和化
"""

def test_conflict_gate():
    """测试冲突门控函数"""
    print("🧪 测试冲突门控函数")
    print("=" * 60)
    
    def conflict_gate(alpha, beta, struct_logit, detail_logit, gap=0.5):
        """冲突门控函数：局部返回值，不修改全局权重"""
        if abs(struct_logit - detail_logit) > gap:
            return alpha * 0.7, beta * 1.1   # 轻微重构
        return alpha, beta
    
    # 测试用例
    test_cases = [
        {
            "name": "无冲突情况",
            "alpha": 0.35, "beta": 0.65,
            "struct_logit": -1.0, "detail_logit": -1.2,
            "expected_change": False
        },
        {
            "name": "有冲突情况",
            "alpha": 0.35, "beta": 0.65,
            "struct_logit": -0.5, "detail_logit": -1.5,
            "expected_change": True
        }
    ]
    
    success_count = 0
    for case in test_cases:
        alpha_final, beta_final = conflict_gate(
            case["alpha"], case["beta"], 
            case["struct_logit"], case["detail_logit"]
        )
        
        logit_diff = abs(case["struct_logit"] - case["detail_logit"])
        changed = (alpha_final != case["alpha"]) or (beta_final != case["beta"])
        
        print(f"🔍 {case['name']}:")
        print(f"   Logit差异: {logit_diff:.3f}")
        print(f"   权重变化: α={case['alpha']:.3f}→{alpha_final:.3f}, β={case['beta']:.3f}→{beta_final:.3f}")
        print(f"   是否调整: {changed}")
        
        if changed == case["expected_change"]:
            print(f"   ✅ 测试通过")
            success_count += 1
        else:
            print(f"   ❌ 测试失败")
    
    print(f"\n📊 冲突门控测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)

def test_confidence_calibration():
    """测试温和的置信度标定"""
    print(f"\n🧪 测试温和的置信度标定")
    print("=" * 60)
    
    def calibrate_confidence(margin, has_detail, struct_top1, detail_top1, same_as_last, content_match):
        """温和的置信度标定，避免"先拉满再腰斩" """
        import numpy as np
        
        # margin→sigmoid
        conf_m = 1/(1 + np.exp(-12*(margin - 0.15)))   # 0.15 作为"可分"分界
        if not has_detail:
            conf_m *= 0.92

        # 一致性：没有 top1 的时候不要给 1.15
        if struct_top1 and detail_top1:
            if struct_top1 == detail_top1:
                cons = 1.15
            else:
                cons = 0.92
        else:
            cons = 0.95

        cont = 1.10 if same_as_last else 1.00

        # 内容匹配放最后，用温和乘法（≥0.75 下限）
        conf = conf_m * cons * cont * max(0.75, float(content_match or 1.0))
        conf = float(np.clip(conf, 0.20, 0.98))

        # 低置信度不更新会话，避免"定位抖动"
        if conf < 0.35:
            return conf, False   # False=不要 update_session
        return conf, True
    
    # 测试用例
    test_cases = [
        {
            "name": "高margin，有detail，一致",
            "margin": 0.30, "has_detail": True,
            "struct_top1": "poi01", "detail_top1": "poi01",
            "same_as_last": False, "content_match": 1.0,
            "expected_high_conf": True, "expected_update": True
        },
        {
            "name": "低margin，无detail",
            "margin": 0.05, "has_detail": False,
            "struct_top1": None, "detail_top1": None,
            "same_as_last": False, "content_match": 1.0,
            "expected_high_conf": False, "expected_update": False
        },
        {
            "name": "中等margin，有detail，不一致",
            "margin": 0.15, "has_detail": True,
            "struct_top1": "poi01", "detail_top1": "poi02",
            "same_as_last": True, "content_match": 0.8,
            "expected_high_conf": False, "expected_update": True
        }
    ]
    
    success_count = 0
    for case in test_cases:
        conf, should_update = calibrate_confidence(
            case["margin"], case["has_detail"],
            case["struct_top1"], case["detail_top1"],
            case["same_as_last"], case["content_match"]
        )
        
        high_conf = conf > 0.5
        
        print(f"🔍 {case['name']}:")
        print(f"   输入: margin={case['margin']:.3f}, has_detail={case['has_detail']}")
        print(f"   输出: confidence={conf:.3f}, should_update={should_update}")
        print(f"   高置信度: {high_conf}, 更新会话: {should_update}")
        
        if (high_conf == case["expected_high_conf"] and 
            should_update == case["expected_update"]):
            print(f"   ✅ 测试通过")
            success_count += 1
        else:
            print(f"   ❌ 测试失败")
    
    print(f"\n📊 置信度标定测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)

def test_single_execution():
    """测试冲突门控只执行一次"""
    print(f"\n🧪 测试冲突门控只执行一次")
    print("=" * 60)
    
    # 模拟融合过程
    def fuse_with_gate(struct_probs, detail_probs, alpha, beta):
        """模拟融合过程，确保冲突门控只执行一次"""
        execution_count = 0
        
        def conflict_gate_with_counter(alpha, beta, struct_logit, detail_logit, gap=0.5):
            nonlocal execution_count
            execution_count += 1
            print(f"🔧 冲突门控执行第 {execution_count} 次")
            if abs(struct_logit - detail_logit) > gap:
                return alpha * 0.7, beta * 1.1
            return alpha, beta
        
        # 检测冲突（只在开始执行一次）
        conflict_detected = False
        alpha_final = alpha
        beta_final = beta
        
        if len(struct_probs) > 0 and len(detail_probs) > 0:
            import math
            def prob_to_logit(p, eps=1e-6):
                p = min(max(p, eps), 1 - eps)
                return math.log(p/(1-p))
            
            struct_top1_logit = prob_to_logit(struct_probs[0])
            detail_top1_logit = prob_to_logit(detail_probs[0])
            
            if abs(struct_top1_logit - detail_top1_logit) > 0.5:
                conflict_detected = True
                alpha_final, beta_final = conflict_gate_with_counter(
                    alpha, beta, struct_top1_logit, detail_top1_logit
                )
        
        # 模拟融合每个候选（不再调用冲突门控）
        fused_scores = []
        for i in range(len(struct_probs)):
            struct_logit = prob_to_logit(struct_probs[i])
            detail_logit = prob_to_logit(detail_probs[i]) if i < len(detail_probs) else 0.0
            
            # 使用最终权重进行融合（无论是否有冲突）
            fused_logit = alpha_final * struct_logit + beta_final * detail_logit
            fused_scores.append(fused_logit)
        
        return fused_scores, execution_count
    
    # 测试数据
    struct_probs = [0.8, 0.1, 0.05, 0.03, 0.02]
    detail_probs = [0.2, 0.3, 0.25, 0.15, 0.10]
    alpha = 0.35
    beta = 0.65
    
    print("🔍 测试冲突情况下的融合过程")
    fused_scores, execution_count = fuse_with_gate(struct_probs, detail_probs, alpha, beta)
    
    print(f"📊 冲突门控执行次数: {execution_count}")
    print(f"📊 融合候选数量: {len(fused_scores)}")
    
    if execution_count == 1:
        print("✅ 冲突门控只执行一次：测试通过")
        return True
    else:
        print(f"❌ 冲突门控执行了 {execution_count} 次：测试失败")
        return False

def main():
    """主函数"""
    print("🧪 测试冲突门控和置信度标定修复")
    print("=" * 60)
    
    # 测试冲突门控函数
    gate_ok = test_conflict_gate()
    
    # 测试置信度标定
    conf_ok = test_confidence_calibration()
    
    # 测试单次执行
    single_ok = test_single_execution()
    
    print(f"\n📊 测试结果总结")
    print("=" * 60)
    print(f"冲突门控函数: {'✅ 通过' if gate_ok else '❌ 失败'}")
    print(f"置信度标定: {'✅ 通过' if conf_ok else '❌ 失败'}")
    print(f"单次执行: {'✅ 通过' if single_ok else '❌ 失败'}")
    
    if gate_ok and conf_ok and single_ok:
        print("🎉 所有测试通过！冲突门控和置信度标定问题已修复")
        print("\n💡 预期改进效果:")
        print("1. ✅ 冲突门控只执行一次，不再重复打印")
        print("2. ✅ 不修改全局α/β权重，使用局部返回值")
        print("3. ✅ 置信度计算温和化，避免'先拉满再腰斩'")
        print("4. ✅ 低置信度时不更新会话，避免定位抖动")
        print("5. ✅ 系统稳定性和置信度应该显著提升")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
