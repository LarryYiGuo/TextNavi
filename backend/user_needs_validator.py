"""
用户需求验证器 (User Needs Validator)
实现N1-N6与DG1-DG6的对应关系验证和综合评估报告生成
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# 用户需求定义 (User Needs Definition)
# ============================================================================

class UserNeed(Enum):
    """用户需求枚举"""
    N1_TOPOLOGICAL_MAP = "N1: Topological Map with Distinguishable Landmarks"
    N2_POSITIONING_ACCURACY = "N2: Required Task Positioning Accuracy Without Additional Hardware"
    N3_SEGREGATED_INSTRUCTIONS = "N3: Segregated Instructions with Redundant Cues"
    N4_UNCERTAINTY_TRUST = "N4: Refusal Tasks or Clarification in Low-Confidence Tasks"
    N5_ACCESSIBLE_INTERFACE = "N5: Fully Accessible and Auditable Interface Processes"
    N6_STANDARDIZED_MAPS = "N6: Reproducible and Accessible Maps and Models According to Standards"

class DesignGoal(Enum):
    """设计目标枚举"""
    DG1_NO_HARDWARE = "DG1: No Hardware Dependency"
    DG2_SEMANTIC_MAP = "DG2: Semantic Textual-Topological Map"
    DG3_LOCALIZATION = "DG3: Useful Precision in Localization"
    DG4_INSTRUCTIONS = "DG4: Segmentable and Repeatable Instructions"
    DG5_TRUST = "DG5: Uncertainty and Faculty Trust"
    DG6_ACCESSIBILITY = "DG6: Accessibility, Compliance, and Testability"

@dataclass
class NeedGoalMapping:
    """需求与目标的映射关系"""
    user_need: UserNeed
    design_goals: List[DesignGoal]
    core_validation_points: List[str]
    evaluation_metrics: List[str]
    success_criteria: Dict[str, Any]

# ============================================================================
# 需求映射配置 (Need-Goal Mapping Configuration)
# ============================================================================

NEED_GOAL_MAPPINGS = {
    UserNeed.N1_TOPOLOGICAL_MAP: NeedGoalMapping(
        user_need=UserNeed.N1_TOPOLOGICAL_MAP,
        design_goals=[DesignGoal.DG2_SEMANTIC_MAP],
        core_validation_points=[
            "地标可区分性",
            "拓扑结构完整性", 
            "环境线索一致性"
        ],
        evaluation_metrics=[
            "地标回忆率",
            "指令清晰度",
            "拓扑结构准确性"
        ],
        success_criteria={
            "landmark_recall_rate": 0.8,
            "instruction_clarity": 4.0,
            "topology_accuracy": 0.9
        }
    ),
    
    UserNeed.N2_POSITIONING_ACCURACY: NeedGoalMapping(
        user_need=UserNeed.N2_POSITIONING_ACCURACY,
        design_goals=[DesignGoal.DG1_NO_HARDWARE, DesignGoal.DG3_LOCALIZATION],
        core_validation_points=[
            "单图像定位精度",
            "拓扑距离准确性",
            "导航指令可理解性"
        ],
        evaluation_metrics=[
            "定位误差",
            "任务完成率",
            "用户信任度"
        ],
        success_criteria={
            "positioning_error": 2.0,  # 米
            "task_completion_rate": 0.85,
            "user_trust_score": 7.0
        }
    ),
    
    UserNeed.N3_SEGREGATED_INSTRUCTIONS: NeedGoalMapping(
        user_need=UserNeed.N3_SEGREGATED_INSTRUCTIONS,
        design_goals=[DesignGoal.DG4_INSTRUCTIONS],
        core_validation_points=[
            "指令分段质量",
            "冗余信息有效性",
            "故障容错机制"
        ],
        evaluation_metrics=[
            "任务完成率",
            "偏离事件",
            "认知负荷",
            "SUS评分"
        ],
        success_criteria={
            "task_completion_rate": 0.8,
            "veering_reduction": 0.5,
            "cognitive_load_reduction": 0.3,
            "sus_score": 68
        }
    ),
    
    UserNeed.N4_UNCERTAINTY_TRUST: NeedGoalMapping(
        user_need=UserNeed.N4_UNCERTAINTY_TRUST,
        design_goals=[DesignGoal.DG5_TRUST],
        core_validation_points=[
            "不确定性表达",
            "澄清对话效果",
            "故障转移策略"
        ],
        evaluation_metrics=[
            "歧义减少",
            "信任度变化",
            "风险缓解效果"
        ],
        success_criteria={
            "ambiguity_reduction": 0.6,
            "trust_recovery": 0.8,
            "risk_mitigation": 0.7
        }
    ),
    
    UserNeed.N5_ACCESSIBLE_INTERFACE: NeedGoalMapping(
        user_need=UserNeed.N5_ACCESSIBLE_INTERFACE,
        design_goals=[DesignGoal.DG6_ACCESSIBILITY],
        core_validation_points=[
            "WCAG 2.2合规",
            "VoiceOver兼容",
            "运动觉交互支持"
        ],
        evaluation_metrics=[
            "合规性评分",
            "兼容性测试",
            "可用性评估"
        ],
        success_criteria={
            "wcag_compliance": 0.9,
            "voiceover_compatibility": 0.95,
            "usability_score": 4.0
        }
    ),
    
    UserNeed.N6_STANDARDIZED_MAPS: NeedGoalMapping(
        user_need=UserNeed.N6_STANDARDIZED_MAPS,
        design_goals=[DesignGoal.DG1_NO_HARDWARE, DesignGoal.DG6_ACCESSIBILITY],
        core_validation_points=[
            "IndoorGML标准",
            "空间可访问单元",
            "地图可重用性"
        ],
        evaluation_metrics=[
            "标准合规性",
            "地图质量",
            "可重用性测试"
        ],
        success_criteria={
            "indoor_gml_compliance": 0.95,
            "map_quality": 0.9,
            "reusability": 0.85
        }
    )
}

# ============================================================================
# 用户需求验证器 (User Needs Validator)
# ============================================================================

class UserNeedsValidator:
    """用户需求验证器"""
    
    def __init__(self):
        self.validation_results = {}
        self.session_data = {}
    
    def validate_requirement_mapping(self, user_need: UserNeed, design_goal: DesignGoal) -> bool:
        """验证需求与目标的映射关系"""
        if user_need not in NEED_GOAL_MAPPINGS:
            return False
        
        mapping = NEED_GOAL_MAPPINGS[user_need]
        return design_goal in mapping.design_goals
    
    def get_core_validation_points(self, user_need: UserNeed) -> List[str]:
        """获取用户需求的核心验证点"""
        if user_need not in NEED_GOAL_MAPPINGS:
            return []
        
        return NEED_GOAL_MAPPINGS[user_need].core_validation_points
    
    def get_evaluation_metrics(self, user_need: UserNeed) -> List[str]:
        """获取用户需求的评估指标"""
        if user_need not in NEED_GOAL_MAPPINGS:
            return []
        
        return NEED_GOAL_MAPPINGS[user_need].evaluation_metrics
    
    def get_success_criteria(self, user_need: UserNeed) -> Dict[str, Any]:
        """获取用户需求的成功标准"""
        if user_need not in NEED_GOAL_MAPPINGS:
            return {}
        
        return NEED_GOAL_MAPPINGS[user_need].success_criteria
    
    def record_validation_data(self, session_id: str, user_need: UserNeed, 
                             metric_name: str, value: Any, timestamp: Optional[str] = None):
        """记录验证数据"""
        if session_id not in self.session_data:
            self.session_data[session_id] = {}
        
        if user_need.value not in self.session_data[session_id]:
            self.session_data[session_id][user_need.value] = {}
        
        if metric_name not in self.session_data[session_id][user_need.value]:
            self.session_data[session_id][user_need.value][metric_name] = []
        
        record = {
            "value": value,
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
        
        self.session_data[session_id][user_need.value][metric_name].append(record)
    
    def calculate_requirement_satisfaction(self, session_id: str, user_need: UserNeed) -> Dict[str, Any]:
        """计算用户需求满足度"""
        if session_id not in self.session_data or user_need.value not in self.session_data[session_id]:
            return {"satisfaction_level": "no_data", "details": "No validation data available"}
        
        success_criteria = self.get_success_criteria(user_need)
        session_metrics = self.session_data[session_id][user_need.value]
        
        satisfaction_scores = {}
        overall_satisfaction = 0.0
        criteria_count = 0
        
        for metric_name, criteria_value in success_criteria.items():
            if metric_name in session_metrics and session_metrics[metric_name]:
                # 获取最新的指标值
                latest_value = session_metrics[metric_name][-1]["value"]
                
                # 计算满足度分数 (0-1)
                if isinstance(criteria_value, (int, float)):
                    if metric_name in ["positioning_error"]:  # 误差越小越好
                        satisfaction = max(0, 1 - (latest_value / criteria_value))
                    else:  # 其他指标越大越好
                        satisfaction = min(1, latest_value / criteria_value)
                else:
                    satisfaction = 1.0 if latest_value == criteria_value else 0.0
                
                satisfaction_scores[metric_name] = satisfaction
                overall_satisfaction += satisfaction
                criteria_count += 1
        
        if criteria_count > 0:
            overall_satisfaction /= criteria_count
        
        return {
            "satisfaction_level": self._categorize_satisfaction(overall_satisfaction),
            "overall_score": overall_satisfaction,
            "metric_scores": satisfaction_scores,
            "success_criteria": success_criteria,
            "validation_data": session_metrics
        }
    
    def _categorize_satisfaction(self, score: float) -> str:
        """分类满足度水平"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "satisfactory"
        elif score >= 0.6:
            return "needs_improvement"
        else:
            return "poor"
    
    def generate_comprehensive_report(self, session_id: str) -> Dict[str, Any]:
        """生成综合评估报告"""
        if session_id not in self.session_data:
            return {"error": "No session data available"}
        
        report = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_needs_analysis": {},
            "overall_satisfaction": 0.0,
            "recommendations": [],
            "summary": {}
        }
        
        total_satisfaction = 0.0
        need_count = 0
        
        # 分析每个用户需求
        for user_need in UserNeed:
            satisfaction_data = self.calculate_requirement_satisfaction(session_id, user_need)
            report["user_needs_analysis"][user_need.value] = satisfaction_data
            
            if satisfaction_data["satisfaction_level"] != "no_data":
                total_satisfaction += satisfaction_data["overall_score"]
                need_count += 1
        
        if need_count > 0:
            report["overall_satisfaction"] = total_satisfaction / need_count
        
        # 生成改进建议
        report["recommendations"] = self._generate_recommendations(session_id)
        
        # 生成总结
        report["summary"] = self._generate_summary(report)
        
        return report
    
    def _generate_recommendations(self, session_id: str) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for user_need in UserNeed:
            satisfaction_data = self.calculate_requirement_satisfaction(session_id, user_need)
            
            if satisfaction_data["satisfaction_level"] == "no_data":
                continue
            
            if satisfaction_data["overall_score"] < 0.8:
                need_name = user_need.value.split(": ")[1] if ": " in user_need.value else user_need.value
                recommendations.append(f"Improve {need_name} - Current satisfaction: {satisfaction_data['overall_score']:.2f}")
            
            # 检查具体指标
            for metric_name, score in satisfaction_data.get("metric_scores", {}).items():
                if score < 0.7:
                    recommendations.append(f"Focus on {metric_name} improvement for {user_need.value}")
        
        return recommendations
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告总结"""
        user_needs = report["user_needs_analysis"]
        
        # 统计满足度水平
        satisfaction_levels = {}
        for need_data in user_needs.values():
            level = need_data.get("satisfaction_level", "unknown")
            satisfaction_levels[level] = satisfaction_levels.get(level, 0) + 1
        
        # 识别最需要改进的领域
        improvement_areas = []
        for need_name, need_data in user_needs.items():
            if need_data.get("overall_score", 0) < 0.7:
                improvement_areas.append(need_name)
        
        return {
            "satisfaction_distribution": satisfaction_levels,
            "improvement_areas": improvement_areas,
            "overall_grade": self._calculate_grade(report["overall_satisfaction"]),
            "key_achievements": self._identify_achievements(user_needs)
        }
    
    def _calculate_grade(self, score: float) -> str:
        """计算总体等级"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        else:
            return "C"
    
    def _identify_achievements(self, user_needs: Dict[str, Any]) -> List[str]:
        """识别主要成就"""
        achievements = []
        
        for need_name, need_data in user_needs.items():
            if need_data.get("overall_score", 0) >= 0.9:
                need_short = need_name.split(": ")[1] if ": " in need_name else need_name
                achievements.append(f"Excellent performance in {need_short}")
            elif need_data.get("overall_score", 0) >= 0.8:
                need_short = need_name.split(": ")[1] if ": " in need_name else need_name
                achievements.append(f"Good performance in {need_short}")
        
        return achievements
    
    def export_validation_data(self, session_id: str, filename: str):
        """导出验证数据到CSV文件"""
        if session_id not in self.session_data:
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['user_need', 'metric_name', 'value', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for user_need, metrics in self.session_data[session_id].items():
                    for metric_name, values in metrics.items():
                        for value_record in values:
                            writer.writerow({
                                'user_need': user_need,
                                'metric_name': metric_name,
                                'value': value_record['value'],
                                'timestamp': value_record['timestamp']
                            })
            
            return True
        except Exception as e:
            print(f"Failed to export validation data: {e}")
            return False
    
    def get_requirement_goal_matrix(self) -> Dict[str, List[str]]:
        """获取需求-目标对应矩阵"""
        matrix = {}
        
        for user_need in UserNeed:
            if user_need in NEED_GOAL_MAPPINGS:
                goals = [goal.value for goal in NEED_GOAL_MAPPINGS[user_need].design_goals]
                matrix[user_need.value] = goals
        
        return matrix

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建验证器实例
    validator = UserNeedsValidator()
    
    # 示例：记录验证数据
    session_id = "test_session_001"
    
    # 记录N1的验证数据
    validator.record_validation_data(session_id, UserNeed.N1_TOPOLOGICAL_MAP, "landmark_recall_rate", 0.85)
    validator.record_validation_data(session_id, UserNeed.N1_TOPOLOGICAL_MAP, "instruction_clarity", 4.2)
    
    # 记录N2的验证数据
    validator.record_validation_data(session_id, UserNeed.N2_POSITIONING_ACCURACY, "positioning_error", 1.5)
    validator.record_validation_data(session_id, UserNeed.N2_POSITIONING_ACCURACY, "task_completion_rate", 0.88)
    
    # 生成综合报告
    report = validator.generate_comprehensive_report(session_id)
    
    # 打印报告
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 导出数据
    validator.export_validation_data(session_id, f"validation_data_{session_id}.csv")
    
    # 显示需求-目标矩阵
    matrix = validator.get_requirement_goal_matrix()
    print("\nRequirement-Goal Matrix:")
    for need, goals in matrix.items():
        print(f"{need}: {', '.join(goals)}")
