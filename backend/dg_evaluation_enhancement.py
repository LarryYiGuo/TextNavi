"""
DG1-DG6 评估系统增强模块
Enhanced Evaluation System for DG1-DG6 Design Goals

This module implements enhanced evaluation capabilities to meet the six design goals
outlined in the research study.
"""

import json
import csv
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

# ============================================================================
# 评估指标定义 (Evaluation Metrics Definition)
# ============================================================================

class TaskStatus(Enum):
    """任务状态枚举"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

class ErrorType(Enum):
    """错误类型枚举"""
    SYSTEM_ERROR = "system_error"
    USER_MISUNDERSTANDING = "user_misunderstanding"
    NAVIGATION_ERROR = "navigation_error"
    LOCALIZATION_ERROR = "localization_error"
    INTERFACE_ERROR = "interface_error"

@dataclass
class NASA_TLX_Score:
    """NASA-TLX认知负荷评分"""
    mental_demand: int  # 1-20
    physical_demand: int  # 1-20
    temporal_demand: int  # 1-20
    performance: int  # 1-20
    effort: int  # 1-20
    frustration: int  # 1-20
    
    def calculate_weighted_score(self, weights: List[float]) -> float:
        """计算加权总分"""
        scores = [self.mental_demand, self.physical_demand, self.temporal_demand,
                 self.performance, self.effort, self.frustration]
        return sum(s * w for s, w in zip(scores, weights))

@dataclass
class SUS_Score:
    """SUS系统可用性评分"""
    q1: int  # 1-5
    q2: int  # 1-5
    q3: int  # 1-5
    q4: int  # 1-5
    q5: int  # 1-5
    q6: int  # 1-5
    q7: int  # 1-5
    q8: int  # 1-5
    q9: int  # 1-5
    q10: int  # 1-5
    
    def calculate_sus_score(self) -> float:
        """计算SUS分数 (0-100)"""
        # SUS计算规则：奇数题直接计算，偶数题反向计算
        scores = []
        for i, score in enumerate([self.q1, self.q2, self.q3, self.q4, self.q5,
                                 self.q6, self.q7, self.q8, self.q9, self.q10]):
            if i % 2 == 0:  # 奇数题 (0-indexed)
                scores.append(score - 1)
            else:  # 偶数题
                scores.append(5 - score)
        
        total = sum(scores) * 2.5
        return total

# ============================================================================
# DG1: No Hardware Dependency 评估
# ============================================================================

class HardwareDependencyEvaluator:
    """硬件依赖评估器"""
    
    def __init__(self):
        self.setup_log = []
        self.installation_burden = {}
    
    def record_setup_process(self, session_id: str, steps: List[str], 
                           time_taken: float, success: bool):
        """记录设置过程"""
        setup_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": steps,
            "time_taken": time_taken,
            "success": success,
            "burden_score": self._calculate_burden_score(steps, time_taken)
        }
        self.setup_log.append(setup_record)
        
    def _calculate_burden_score(self, steps: List[str], time_taken: float) -> float:
        """计算安装负担分数 (0-10, 越低越好)"""
        # 基于步骤数量和时间的简单负担计算
        step_penalty = len(steps) * 0.5
        time_penalty = min(time_taken / 60, 5)  # 超过5分钟按5分计算
        return min(step_penalty + time_penalty, 10)

# ============================================================================
# DG2: Semantic Textual-Topological Map 评估
# ============================================================================

class SemanticMapEvaluator:
    """语义地图评估器"""
    
    def __init__(self):
        self.landmark_recall_tests = []
        self.instruction_clarity_scores = []
        self.error_attribution_log = []
    
    def record_landmark_recall(self, session_id: str, task_id: str,
                              landmarks_presented: List[str], landmarks_recalled: List[str],
                              time_delay: float):
        """记录地标回忆测试"""
        recall_rate = len(set(landmarks_recalled) & set(landmarks_presented)) / len(landmarks_presented)
        
        test_record = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "landmarks_presented": landmarks_presented,
            "landmarks_recalled": landmarks_recalled,
            "recall_rate": recall_rate,
            "time_delay": time_delay
        }
        self.landmark_recall_tests.append(test_record)
    
    def record_instruction_clarity(self, session_id: str, instruction_id: str,
                                 clarity_score: int, understanding_score: int):
        """记录指令清晰度评分"""
        clarity_record = {
            "session_id": session_id,
            "instruction_id": instruction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "clarity_score": clarity_score,  # 1-5
            "understanding_score": understanding_score,  # 1-5
            "overall_score": (clarity_score + understanding_score) / 2
        }
        self.instruction_clarity_scores.append(clarity_record)
    
    def record_error_attribution(self, session_id: str, error_id: str,
                               error_type: ErrorType, user_explanation: str,
                               system_analysis: str):
        """记录错误归因分析"""
        attribution_record = {
            "session_id": session_id,
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type.value,
            "user_explanation": user_explanation,
            "system_analysis": system_analysis,
            "attribution": self._analyze_error_attribution(user_explanation, system_analysis)
        }
        self.error_attribution_log.append(attribution_record)
    
    def _analyze_error_attribution(self, user_explanation: str, system_analysis: str) -> str:
        """分析错误归因"""
        # 简单的关键词分析
        user_keywords = ["misunderstood", "confused", "didn't understand", "thought"]
        system_keywords = ["bug", "error", "failed", "incorrect"]
        
        user_score = sum(1 for keyword in user_keywords if keyword in user_explanation.lower())
        system_score = sum(1 for keyword in system_keywords if keyword in system_analysis.lower())
        
        if user_score > system_score:
            return "user_misunderstanding"
        elif system_score > user_score:
            return "system_error"
        else:
            return "unclear"

# ============================================================================
# DG3: Useful Precision in Localization 评估
# ============================================================================

class LocalizationEvaluator:
    """定位精度评估器"""
    
    def __init__(self):
        self.interaction_behavior_log = []
        self.error_recovery_log = []
        self.trust_scores = []
    
    def record_interaction_behavior(self, session_id: str, photo_count: int,
                                  first_photo_success: bool, adjustment_actions: List[str]):
        """记录交互行为"""
        behavior_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "photo_count": photo_count,
            "first_photo_success": first_photo_success,
            "adjustment_actions": adjustment_actions,
            "interaction_fluency": self._calculate_fluency_score(photo_count, first_photo_success)
        }
        self.interaction_behavior_log.append(behavior_record)
    
    def record_error_recovery(self, session_id: str, error_type: str,
                            recovery_time: float, recovery_strategy: str,
                            success: bool):
        """记录错误恢复过程"""
        recovery_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "recovery_time": recovery_time,
            "recovery_strategy": recovery_strategy,
            "success": success
        }
        self.error_recovery_log.append(recovery_record)
    
    def record_trust_score(self, session_id: str, trust_score: int, context: str):
        """记录用户信任度评分"""
        trust_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "trust_score": trust_score,  # 1-10
            "context": context
        }
        self.trust_scores.append(trust_record)
    
    def _calculate_fluency_score(self, photo_count: int, first_photo_success: bool) -> float:
        """计算交互流畅性分数 (0-10)"""
        if first_photo_success and photo_count <= 2:
            return 10.0
        elif first_photo_success and photo_count <= 3:
            return 8.0
        elif photo_count <= 4:
            return 6.0
        else:
            return 4.0

# ============================================================================
# DG4: Segmentable and Repeatable Instructions 评估
# ============================================================================

class InstructionEvaluator:
    """指令评估器"""
    
    def __init__(self):
        self.task_completion_log = []
        self.veering_events = []
        self.nasa_tlx_scores = []
        self.sus_scores = []
    
    def record_task_completion(self, session_id: str, task_id: str,
                             task_type: str, status: TaskStatus,
                             completion_time: float, veering_count: int):
        """记录任务完成情况"""
        completion_record = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": task_type,
            "status": status.value,
            "completion_time": completion_time,
            "veering_count": veering_count,
            "success": status == TaskStatus.COMPLETED
        }
        self.task_completion_log.append(completion_record)
    
    def record_veering_event(self, session_id: str, task_id: str,
                           veering_type: str, veering_degree: float,
                           recovery_action: str):
        """记录偏离事件"""
        veering_record = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "veering_type": veering_type,
            "veering_degree": veering_degree,
            "recovery_action": recovery_action
        }
        self.veering_events.append(veering_record)
    
    def record_nasa_tlx(self, session_id: str, task_id: str, scores: NASA_TLX_Score):
        """记录NASA-TLX评分"""
        nasa_record = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mental_demand": scores.mental_demand,
            "physical_demand": scores.physical_demand,
            "temporal_demand": scores.temporal_demand,
            "performance": scores.performance,
            "effort": scores.effort,
            "frustration": scores.frustration,
            "weighted_score": scores.calculate_weighted_score([1, 1, 1, 1, 1, 1])  # 等权重
        }
        self.nasa_tlx_scores.append(nasa_record)
    
    def record_sus_score(self, session_id: str, scores: SUS_Score):
        """记录SUS评分"""
        sus_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "q1": scores.q1, "q2": scores.q2, "q3": scores.q3, "q4": scores.q4, "q5": scores.q5,
            "q6": scores.q6, "q7": scores.q7, "q8": scores.q8, "q9": scores.q9, "q10": scores.q10,
            "sus_score": scores.calculate_sus_score()
        }
        self.sus_scores.append(sus_record)

# ============================================================================
# DG5: Uncertainty and Faculty Trust 评估
# ============================================================================

class UncertaintyTrustEvaluator:
    """不确定性和信任度评估器"""
    
    def __init__(self):
        self.clarification_dialogue_log = []
        self.trust_change_log = []
        self.error_recovery_mechanism_log = []
    
    def record_clarification_dialogue(self, session_id: str, dialogue_id: str,
                                    ambiguity_before: int, ambiguity_after: int,
                                    dialogue_count: int):
        """记录澄清对话效果"""
        dialogue_record = {
            "session_id": session_id,
            "dialogue_id": dialogue_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ambiguity_before": ambiguity_before,  # 1-5
            "ambiguity_after": ambiguity_after,    # 1-5
            "dialogue_count": dialogue_count,
            "ambiguity_reduction": ambiguity_before - ambiguity_after,
            "effectiveness": "effective" if ambiguity_before > ambiguity_after else "ineffective"
        }
        self.clarification_dialogue_log.append(dialogue_record)
    
    def record_trust_change(self, session_id: str, event_id: str,
                          trust_before: int, trust_after: int,
                          event_type: str):
        """记录信任度变化"""
        trust_change_record = {
            "session_id": session_id,
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "trust_before": trust_before,  # 1-10
            "trust_after": trust_after,    # 1-10
            "trust_change": trust_after - trust_before,
            "event_type": event_type,
            "recovery_ability": "high" if trust_after >= trust_before else "low"
        }
        self.trust_change_log.append(trust_change_record)
    
    def record_error_recovery_mechanism(self, session_id: str, error_id: str,
                                      mechanism_used: str, success: bool,
                                      user_safety: bool):
        """记录错误恢复机制测试"""
        recovery_mechanism_record = {
            "session_id": session_id,
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mechanism_used": mechanism_used,
            "success": success,
            "user_safety": user_safety,
            "effectiveness": "high" if success and user_safety else "medium" if success else "low"
        }
        self.error_recovery_mechanism_log.append(recovery_mechanism_record)

# ============================================================================
# DG6: Accessibility, Compliance, and Testability 评估
# ============================================================================

class AccessibilityEvaluator:
    """可访问性评估器"""
    
    def __init__(self):
        self.wcag_compliance_log = []
        self.voiceover_compatibility_log = []
        self.usability_test_log = []
        self.interface_perception_log = []
    
    def record_wcag_compliance(self, session_id: str, wcag_guideline: str,
                              compliance_status: str, issues_found: List[str]):
        """记录WCAG合规性检查"""
        wcag_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "wcag_guideline": wcag_guideline,
            "compliance_status": compliance_status,
            "issues_found": issues_found,
            "compliance_score": self._calculate_compliance_score(compliance_status, len(issues_found))
        }
        self.wcag_compliance_log.append(wcag_record)
    
    def record_voiceover_compatibility(self, session_id: str, feature_tested: str,
                                    compatibility_status: str, voice_feedback_quality: int):
        """记录VoiceOver兼容性测试"""
        voiceover_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "feature_tested": feature_tested,
            "compatibility_status": compatibility_status,
            "voice_feedback_quality": voice_feedback_quality,  # 1-5
            "compatible": compatibility_status == "compatible"
        }
        self.voiceover_compatibility_log.append(voiceover_record)
    
    def record_usability_test(self, session_id: str, task_id: str,
                            operation_flow: List[str], operation_time: float,
                            efficiency_score: int):
        """记录可用性测试"""
        usability_record = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "operation_flow": operation_flow,
            "operation_time": operation_time,
            "efficiency_score": efficiency_score,  # 1-5
            "efficiency_level": self._categorize_efficiency(operation_time, efficiency_score)
        }
        self.usability_test_log.append(usability_record)
    
    def record_interface_perception(self, session_id: str, element_id: str,
                                  accurately_perceived: bool, content_informative: bool,
                                  interaction_flow_reasonable: bool):
        """记录界面元素感知性测试"""
        perception_record = {
            "session_id": session_id,
            "element_id": element_id,
            "timestamp": datetime.utcnow().isoformat(),
            "accurately_perceived": accurately_perceived,
            "content_informative": content_informative,
            "interaction_flow_reasonable": interaction_flow_reasonable,
            "overall_perception_score": self._calculate_perception_score(
                accurately_perceived, content_informative, interaction_flow_reasonable
            )
        }
        self.interface_perception_log.append(perception_record)
    
    def _calculate_compliance_score(self, status: str, issues_count: int) -> float:
        """计算合规性分数"""
        base_score = 100 if status == "compliant" else 50 if status == "partially_compliant" else 0
        penalty = issues_count * 10
        return max(0, base_score - penalty)
    
    def _categorize_efficiency(self, operation_time: float, efficiency_score: int) -> str:
        """分类效率水平"""
        if operation_time < 30 and efficiency_score >= 4:
            return "high"
        elif operation_time < 60 and efficiency_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _calculate_perception_score(self, accurately_perceived: bool, 
                                  content_informative: bool, 
                                  interaction_flow_reasonable: bool) -> float:
        """计算感知性分数"""
        score = 0
        if accurately_perceived:
            score += 33.3
        if content_informative:
            score += 33.3
        if interaction_flow_reasonable:
            score += 33.4
        return score

# ============================================================================
# 主评估管理器
# ============================================================================

class DGEvaluationManager:
    """DG1-DG6评估管理器"""
    
    def __init__(self):
        self.dg1_evaluator = HardwareDependencyEvaluator()
        self.dg2_evaluator = SemanticMapEvaluator()
        self.dg3_evaluator = LocalizationEvaluator()
        self.dg4_evaluator = InstructionEvaluator()
        self.dg5_evaluator = UncertaintyTrustEvaluator()
        self.dg6_evaluator = AccessibilityEvaluator()
    
    def generate_evaluation_report(self, session_id: str) -> Dict[str, Any]:
        """生成综合评估报告"""
        report = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dg1_hardware_dependency": self._analyze_dg1(session_id),
            "dg2_semantic_map": self._analyze_dg2(session_id),
            "dg3_localization": self._analyze_dg3(session_id),
            "dg4_instructions": self._analyze_dg4(session_id),
            "dg5_uncertainty_trust": self._analyze_dg5(session_id),
            "dg6_accessibility": self._analyze_dg6(session_id),
            "overall_score": 0.0
        }
        
        # 计算总体分数
        scores = [
            report["dg1_hardware_dependency"]["score"],
            report["dg2_semantic_map"]["score"],
            report["dg3_localization"]["score"],
            report["dg4_instructions"]["score"],
            report["dg5_uncertainty_trust"]["score"],
            report["dg6_accessibility"]["score"]
        ]
        report["overall_score"] = sum(scores) / len(scores)
        
        return report
    
    def _analyze_dg1(self, session_id: str) -> Dict[str, Any]:
        """分析DG1指标"""
        setup_records = [r for r in self.dg1_evaluator.setup_log if r["session_id"] == session_id]
        if not setup_records:
            return {"score": 0.0, "status": "no_data", "details": "No setup data available"}
        
        avg_burden = sum(r["burden_score"] for r in setup_records) / len(setup_records)
        success_rate = sum(1 for r in setup_records if r["success"]) / len(setup_records)
        
        # 负担分数转换为正向分数 (0-10 -> 10-0)
        score = 10 - avg_burden
        
        return {
            "score": score,
            "status": "analyzed",
            "setup_success_rate": success_rate,
            "average_burden_score": avg_burden,
            "recommendations": self._get_dg1_recommendations(score, success_rate)
        }
    
    def _analyze_dg2(self, session_id: str) -> Dict[str, Any]:
        """分析DG2指标"""
        recall_tests = [r for r in self.dg2_evaluator.landmark_recall_tests if r["session_id"] == session_id]
        clarity_scores = [r for r in self.dg2_evaluator.instruction_clarity_scores if r["session_id"] == session_id]
        
        if not recall_tests and not clarity_scores:
            return {"score": 0.0, "status": "no_data", "details": "No semantic map data available"}
        
        avg_recall_rate = sum(r["recall_rate"] for r in recall_tests) / len(recall_tests) if recall_tests else 0
        avg_clarity = sum(r["overall_score"] for r in clarity_scores) / len(clarity_scores) if clarity_scores else 0
        
        # 综合分数 (0-10)
        score = (avg_recall_rate * 5 + avg_clarity * 2) / 2
        
        return {
            "score": score,
            "status": "analyzed",
            "average_recall_rate": avg_recall_rate,
            "average_clarity_score": avg_clarity,
            "recommendations": self._get_dg2_recommendations(score, avg_recall_rate, avg_clarity)
        }
    
    def _analyze_dg3(self, session_id: str) -> Dict[str, Any]:
        """分析DG3指标"""
        behavior_logs = [r for r in self.dg3_evaluator.interaction_behavior_log if r["session_id"] == session_id]
        trust_scores = [r for r in self.dg3_evaluator.trust_scores if r["session_id"] == session_id]
        
        if not behavior_logs and not trust_scores:
            return {"score": 0.0, "status": "no_data", "details": "No localization data available"}
        
        avg_fluency = sum(r["interaction_fluency"] for r in behavior_logs) / len(behavior_logs) if behavior_logs else 0
        avg_trust = sum(r["trust_score"] for r in trust_scores) / len(trust_scores) if trust_scores else 0
        
        # 综合分数 (0-10)
        score = (avg_fluency + avg_trust) / 2
        
        return {
            "score": score,
            "status": "analyzed",
            "average_fluency_score": avg_fluency,
            "average_trust_score": avg_trust,
            "recommendations": self._get_dg3_recommendations(score, avg_fluency, avg_trust)
        }
    
    def _analyze_dg4(self, session_id: str) -> Dict[str, Any]:
        """分析DG4指标"""
        completion_logs = [r for r in self.dg4_evaluator.task_completion_log if r["session_id"] == session_id]
        sus_scores = [r for r in self.dg4_evaluator.sus_scores if r["session_id"] == session_id]
        
        if not completion_logs and not sus_scores:
            return {"score": 0.0, "status": "no_data", "details": "No instruction data available"}
        
        task_success_rate = sum(1 for r in completion_logs if r["success"]) / len(completion_logs) if completion_logs else 0
        avg_sus = sum(r["sus_score"] for r in sus_scores) / len(sus_scores) if sus_scores else 0
        
        # 综合分数 (0-10)
        score = (task_success_rate * 5 + avg_sus / 10) / 2
        
        return {
            "score": score,
            "status": "analyzed",
            "task_success_rate": task_success_rate,
            "average_sus_score": avg_sus,
            "recommendations": self._get_dg4_recommendations(score, task_success_rate, avg_sus)
        }
    
    def _analyze_dg5(self, session_id: str) -> Dict[str, Any]:
        """分析DG5指标"""
        dialogue_logs = [r for r in self.dg5_evaluator.clarification_dialogue_log if r["session_id"] == session_id]
        trust_changes = [r for r in self.dg5_evaluator.trust_change_log if r["session_id"] == session_id]
        
        if not dialogue_logs and not trust_changes:
            return {"score": 0.0, "status": "no_data", "details": "No uncertainty/trust data available"}
        
        avg_ambiguity_reduction = sum(r["ambiguity_reduction"] for r in dialogue_logs) / len(dialogue_logs) if dialogue_logs else 0
        avg_trust_recovery = sum(1 for r in trust_changes if r["recovery_ability"] == "high") / len(trust_changes) if trust_changes else 0
        
        # 综合分数 (0-10)
        score = (avg_ambiguity_reduction * 2 + avg_trust_recovery * 5) / 2
        
        return {
            "score": score,
            "status": "analyzed",
            "average_ambiguity_reduction": avg_ambiguity_reduction,
            "trust_recovery_rate": avg_trust_recovery,
            "recommendations": self._get_dg5_recommendations(score, avg_ambiguity_reduction, avg_trust_recovery)
        }
    
    def _analyze_dg6(self, session_id: str) -> Dict[str, Any]:
        """分析DG6指标"""
        wcag_logs = [r for r in self.dg6_evaluator.wcag_compliance_log if r["session_id"] == session_id]
        voiceover_logs = [r for r in self.dg6_evaluator.voiceover_compatibility_log if r["session_id"] == session_id]
        
        if not wcag_logs and not voiceover_logs:
            return {"score": 0.0, "status": "no_data", "details": "No accessibility data available"}
        
        avg_wcag_score = sum(r["compliance_score"] for r in wcag_logs) / len(wcag_logs) if wcag_logs else 0
        voiceover_compatibility_rate = sum(1 for r in voiceover_logs if r["compatible"]) / len(voiceover_logs) if voiceover_logs else 0
        
        # 综合分数 (0-10)
        score = (avg_wcag_score / 10 + voiceover_compatibility_rate * 5) / 2
        
        return {
            "score": score,
            "status": "analyzed",
            "wcag_compliance_score": avg_wcag_score,
            "voiceover_compatibility_rate": voiceover_compatibility_rate,
            "recommendations": self._get_dg6_recommendations(score, avg_wcag_score, voiceover_compatibility_rate)
        }
    
    def _get_dg1_recommendations(self, score: float, success_rate: float) -> List[str]:
        """获取DG1改进建议"""
        recommendations = []
        if score < 7:
            recommendations.append("Reduce setup complexity and installation burden")
        if success_rate < 0.8:
            recommendations.append("Improve setup success rate through better user guidance")
        return recommendations
    
    def _get_dg2_recommendations(self, score: float, recall_rate: float, clarity: float) -> List[str]:
        """获取DG2改进建议"""
        recommendations = []
        if recall_rate < 0.7:
            recommendations.append("Enhance landmark memorability and recognition")
        if clarity < 4:
            recommendations.append("Improve instruction clarity and comprehensibility")
        return recommendations
    
    def _get_dg3_recommendations(self, score: float, fluency: float, trust: float) -> List[str]:
        """获取DG3改进建议"""
        recommendations = []
        if fluency < 7:
            recommendations.append("Optimize interaction flow and reduce photo requirements")
        if trust < 7:
            recommendations.append("Build user trust through consistent and accurate localization")
        return recommendations
    
    def _get_dg4_recommendations(self, score: float, success_rate: float, sus_score: float) -> List[str]:
        """获取DG4改进建议"""
        recommendations = []
        if success_rate < 0.8:
            recommendations.append("Improve task completion rate through better instructions")
        if sus_score < 68:
            recommendations.append("Enhance system usability based on SUS feedback")
        return recommendations
    
    def _get_dg5_recommendations(self, score: float, ambiguity_reduction: float, trust_recovery: float) -> List[str]:
        """获取DG5改进建议"""
        recommendations = []
        if ambiguity_reduction < 1:
            recommendations.append("Enhance clarification dialogue effectiveness")
        if trust_recovery < 0.7:
            recommendations.append("Improve trust recovery mechanisms after errors")
        return recommendations
    
    def _get_dg6_recommendations(self, score: float, wcag_score: float, voiceover_rate: float) -> List[str]:
        """获取DG6改进建议"""
        recommendations = []
        if wcag_score < 80:
            recommendations.append("Improve WCAG 2.2 compliance")
        if voiceover_rate < 0.8:
            recommendations.append("Enhance VoiceOver compatibility")
        return recommendations
    
    def export_evaluation_data(self, filename: str):
        """导出评估数据到CSV文件"""
        # 实现数据导出功能
        pass

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建评估管理器
    evaluator = DGEvaluationManager()
    
    # 示例：记录DG1数据
    evaluator.dg1_evaluator.record_setup_process(
        session_id="test_session_001",
        steps=["install_app", "grant_permissions", "first_photo"],
        time_taken=120.5,
        success=True
    )
    
    # 示例：记录DG2数据
    evaluator.dg2_evaluator.record_landmark_recall(
        session_id="test_session_001",
        task_id="landmark_test_001",
        landmarks_presented=["entrance", "3d_printer", "bookshelf"],
        landmarks_recalled=["entrance", "3d_printer"],
        time_delay=300.0
    )
    
    # 生成评估报告
    report = evaluator.generate_evaluation_report("test_session_001")
    print(json.dumps(report, indent=2, ensure_ascii=False))
