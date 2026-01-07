"""
Evaluation and regression testing for dual-channel retrieval system
A/B testing between single-channel (old) vs dual-channel fusion (new)
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualChannelEvaluator:
    """
    双通道检索系统评测器
    执行A/B测试：单通道（旧）vs 双通道融合（新）
    """
    
    def __init__(self, 
                 results_dir: str = "logs/evaluation",
                 test_data_file: str = "test_photos.json"):
        """
        初始化评测器
        
        Args:
            results_dir: 结果保存目录
            test_data_file: 测试数据文件
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_data_file = test_data_file
        self.test_data = self._load_test_data()
        
        # 评测指标
        self.metrics = {
            "top1_accuracy": [],
            "top3_accuracy": [],
            "avg_confidence": [],
            "avg_margin": [],
            "misclassification_distribution": {},
            "response_time": [],
            "landmark_specific_metrics": {}
        }
        
        # 关键区域（重点关注）
        self.key_areas = {
            "yellow_line_segment": "黄线段",
            "printing_zone": "打印区", 
            "bookshelf_drawer_glass": "书架-抽屉-玻璃门三角关系"
        }
        
        logger.info(f"双通道检索评测器初始化完成，结果目录: {self.results_dir}")
    
    def _load_test_data(self) -> Dict:
        """加载测试数据"""
        try:
            with open(self.test_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"测试数据文件未找到: {self.test_data_file}")
            return self._create_sample_test_data()
        except Exception as e:
            logger.error(f"加载测试数据失败: {e}")
            return {}
    
    def _create_sample_test_data(self) -> Dict:
        """创建示例测试数据"""
        sample_data = {
            "test_photos": [
                {
                    "id": "test_001",
                    "file_path": "test_photos/photo_001.jpg",
                    "ground_truth": "poi_3d_printer_table",
                    "scene_id": "SCENE_A_MS",
                    "area_type": "printing_zone",
                    "expected_landmarks": ["3d printer", "ender", "orange accents", "filament spools"]
                },
                {
                    "id": "test_002", 
                    "file_path": "test_photos/photo_002.jpg",
                    "ground_truth": "dp_bookshelf_qr",
                    "scene_id": "SCENE_A_MS",
                    "area_type": "storage_zone",
                    "expected_landmarks": ["qr code", "bookshelf", "rnib scrabble", "accessibility brochures"]
                },
                {
                    "id": "test_003",
                    "file_path": "test_photos/photo_003.jpg", 
                    "ground_truth": "poi_component_drawer_wall",
                    "scene_id": "SCENE_A_MS",
                    "area_type": "storage_zone",
                    "expected_landmarks": ["component drawer", "black metal frame", "numbered labels"]
                }
            ]
        }
        return sample_data
    
    def run_ab_test(self, 
                    single_channel_system,
                    dual_channel_system,
                    test_photos: List[Dict] = None) -> Dict:
        """
        运行A/B测试
        
        Args:
            single_channel_system: 单通道检索系统
            dual_channel_system: 双通道检索系统
            test_photos: 测试照片列表
        
        Returns:
            A/B测试结果
        """
        if test_photos is None:
            test_photos = self.test_data.get("test_photos", [])
        
        logger.info(f"开始A/B测试，测试照片数量: {len(test_photos)}")
        
        results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_photos": len(test_photos),
                "single_channel": "baseline",
                "dual_channel": "enhanced"
            },
            "single_channel_results": [],
            "dual_channel_results": [],
            "comparison_metrics": {}
        }
        
        # 运行单通道测试
        logger.info("运行单通道检索测试...")
        for photo in test_photos:
            result = self._evaluate_single_photo(
                photo, single_channel_system, "single_channel"
            )
            results["single_channel_results"].append(result)
        
        # 运行双通道测试
        logger.info("运行双通道检索测试...")
        for photo in test_photos:
            result = self._evaluate_single_photo(
                photo, dual_channel_system, "dual_channel"
            )
            results["dual_channel_results"].append(result)
        
        # 计算对比指标
        results["comparison_metrics"] = self._calculate_comparison_metrics(
            results["single_channel_results"],
            results["dual_channel_results"]
        )
        
        # 保存结果
        self._save_results(results)
        
        logger.info("A/B测试完成")
        return results
    
    def _evaluate_single_photo(self, 
                              photo: Dict, 
                              retrieval_system,
                              system_type: str) -> Dict:
        """
        评估单张照片
        
        Args:
            photo: 照片信息
            retrieval_system: 检索系统
            system_type: 系统类型
        
        Returns:
            评估结果
        """
        try:
            # 模拟检索过程（实际使用时需要真实的检索系统）
            if system_type == "single_channel":
                # 模拟单通道检索结果
                retrieval_result = self._mock_single_channel_retrieval(photo)
            else:
                # 模拟双通道检索结果
                retrieval_result = self._mock_dual_channel_retrieval(photo)
            
            # 计算评估指标
            evaluation_result = self._calculate_photo_metrics(
                photo, retrieval_result, system_type
            )
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"评估照片失败 {photo['id']}: {e}")
            return {
                "photo_id": photo["id"],
                "system_type": system_type,
                "error": str(e),
                "success": False
            }
    
    def _mock_single_channel_retrieval(self, photo: Dict) -> Dict:
        """模拟单通道检索结果"""
        # 模拟单通道检索的置信度和margin
        confidence = np.random.uniform(0.5, 0.8)
        margin = np.random.uniform(0.1, 0.3)
        
        return {
            "confidence": confidence,
            "margin": margin,
            "top1_prediction": photo["ground_truth"],
            "top3_predictions": [photo["ground_truth"], "other_1", "other_2"],
            "response_time": np.random.uniform(0.5, 2.0)
        }
    
    def _mock_dual_channel_retrieval(self, photo: Dict) -> Dict:
        """模拟双通道检索结果"""
        # 模拟双通道检索的置信度和margin（应该更好）
        confidence = np.random.uniform(0.6, 0.9)
        margin = np.random.uniform(0.2, 0.4)
        
        return {
            "confidence": confidence,
            "margin": margin,
            "top1_prediction": photo["ground_truth"],
            "top3_predictions": [photo["ground_truth"], "other_1", "other_2"],
            "response_time": np.random.uniform(0.3, 1.5),
            "channel_weights": {"w_a": 0.45, "w_b": 0.55}
        }
    
    def _calculate_photo_metrics(self, 
                                photo: Dict, 
                                retrieval_result: Dict,
                                system_type: str) -> Dict:
        """
        计算单张照片的评估指标
        
        Args:
            photo: 照片信息
            retrieval_result: 检索结果
            system_type: 系统类型
        
        Returns:
            评估指标
        """
        # 基础信息
        result = {
            "photo_id": photo["id"],
            "system_type": system_type,
            "ground_truth": photo["ground_truth"],
            "area_type": photo["area_type"],
            "success": True
        }
        
        # Top-1准确率
        result["top1_correct"] = (
            retrieval_result["top1_prediction"] == photo["ground_truth"]
        )
        
        # Top-3准确率
        result["top3_correct"] = (
            photo["ground_truth"] in retrieval_result["top3_predictions"]
        )
        
        # 置信度和margin
        result["confidence"] = retrieval_result["confidence"]
        result["margin"] = retrieval_result["margin"]
        
        # 响应时间
        result["response_time"] = retrieval_result["response_time"]
        
        # 地标识别质量
        result["landmark_quality"] = self._evaluate_landmark_quality(
            photo, retrieval_result
        )
        
        return result
    
    def _evaluate_landmark_quality(self, 
                                  photo: Dict, 
                                  retrieval_result: Dict) -> Dict:
        """评估地标识别质量"""
        expected_landmarks = photo.get("expected_landmarks", [])
        
        # 这里应该分析检索结果中的地标描述
        # 暂时返回模拟结果
        detected_landmarks = np.random.choice(
            expected_landmarks, 
            size=min(3, len(expected_landmarks)), 
            replace=False
        ).tolist()
        
        coverage_rate = len(detected_landmarks) / len(expected_landmarks) if expected_landmarks else 0
        
        return {
            "expected_landmarks": expected_landmarks,
            "detected_landmarks": detected_landmarks,
            "coverage_rate": coverage_rate,
            "quality_score": coverage_rate * retrieval_result["confidence"]
        }
    
    def _calculate_comparison_metrics(self, 
                                     single_results: List[Dict],
                                     dual_results: List[Dict]) -> Dict:
        """
        计算对比指标
        
        Args:
            single_results: 单通道结果
            dual_results: 双通道结果
        
        Returns:
            对比指标
        """
        comparison = {}
        
        # 过滤成功的结果
        single_success = [r for r in single_results if r.get("success", False)]
        dual_success = [r for r in dual_results if r.get("success", False)]
        
        if not single_success or not dual_success:
            logger.warning("没有成功的结果用于对比")
            return comparison
        
        # Top-1准确率对比
        single_top1_acc = np.mean([r["top1_correct"] for r in single_success])
        dual_top1_acc = np.mean([r["top1_correct"] for r in dual_success])
        comparison["top1_accuracy"] = {
            "single_channel": single_top1_acc,
            "dual_channel": dual_top1_acc,
            "improvement": dual_top1_acc - single_top1_acc,
            "improvement_rate": (dual_top1_acc - single_top1_acc) / single_top1_acc * 100 if single_top1_acc > 0 else 0
        }
        
        # Top-3准确率对比
        single_top3_acc = np.mean([r["top3_correct"] for r in single_success])
        dual_top3_acc = np.mean([r["top3_correct"] for r in dual_success])
        comparison["top3_accuracy"] = {
            "single_channel": single_top3_acc,
            "dual_channel": dual_top3_acc,
            "improvement": dual_top3_acc - single_top3_acc,
            "improvement_rate": (dual_top3_acc - single_top3_acc) / single_top3_acc * 100 if single_top3_acc > 0 else 0
        }
        
        # 平均置信度对比
        single_avg_conf = np.mean([r["confidence"] for r in single_success])
        dual_avg_conf = np.mean([r["confidence"] for r in dual_success])
        comparison["avg_confidence"] = {
            "single_channel": single_avg_conf,
            "dual_channel": dual_avg_conf,
            "improvement": dual_avg_conf - single_avg_conf,
            "improvement_rate": (dual_avg_conf - single_avg_conf) / single_avg_conf * 100 if single_avg_conf > 0 else 0
        }
        
        # 平均Margin对比
        single_avg_margin = np.mean([r["margin"] for r in single_success])
        dual_avg_margin = np.mean([r["margin"] for r in dual_success])
        comparison["avg_margin"] = {
            "single_channel": single_avg_margin,
            "dual_channel": dual_avg_margin,
            "improvement": dual_avg_margin - single_avg_margin,
            "improvement_rate": (dual_avg_margin - single_avg_margin) / single_avg_margin * 100 if single_avg_margin > 0 else 0
        }
        
        # 响应时间对比
        single_avg_time = np.mean([r["response_time"] for r in single_success])
        dual_avg_time = np.mean([r["response_time"] for r in dual_success])
        comparison["avg_response_time"] = {
            "single_channel": single_avg_time,
            "dual_channel": dual_avg_time,
            "improvement": single_avg_time - dual_avg_time,  # 时间越短越好
            "improvement_rate": (single_avg_time - dual_avg_time) / single_avg_time * 100 if single_avg_time > 0 else 0
        }
        
        # 关键区域性能对比
        comparison["key_area_performance"] = self._analyze_key_area_performance(
            single_results, dual_results
        )
        
        return comparison
    
    def _analyze_key_area_performance(self, 
                                     single_results: List[Dict],
                                     dual_results: List[Dict]) -> Dict:
        """分析关键区域性能"""
        key_area_analysis = {}
        
        for area_name, area_desc in self.key_areas.items():
            # 过滤该区域的结果
            single_area = [r for r in single_results if r.get("area_type") == area_name]
            dual_area = [r for r in dual_results if r.get("area_type") == area_name]
            
            if not single_area or not dual_area:
                continue
            
            # 计算该区域的指标
            single_top1 = np.mean([r["top1_correct"] for r in single_area])
            dual_top1 = np.mean([r["top1_correct"] for r in dual_area])
            
            key_area_analysis[area_name] = {
                "description": area_desc,
                "single_channel_top1": single_top1,
                "dual_channel_top1": dual_top1,
                "improvement": dual_top1 - single_top1,
                "improvement_rate": (dual_top1 - single_top1) / single_top1 * 100 if single_top1 > 0 else 0
            }
        
        return key_area_analysis
    
    def _save_results(self, results: Dict):
        """保存评测结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dual_channel_evaluation_{timestamp}.json"
        filepath = self.results_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"评测结果已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存评测结果失败: {e}")
    
    def generate_report(self, results: Dict) -> str:
        """生成评测报告"""
        report = []
        report.append("# 双通道检索系统A/B测试报告")
        report.append(f"测试时间: {results['test_info']['timestamp']}")
        report.append(f"测试照片数量: {results['test_info']['total_photos']}")
        report.append("")
        
        # 总体性能对比
        report.append("## 总体性能对比")
        metrics = results["comparison_metrics"]
        
        for metric_name, metric_data in metrics.items():
            if metric_name == "key_area_performance":
                continue
                
            report.append(f"### {metric_name.replace('_', ' ').title()}")
            report.append(f"- 单通道: {metric_data['single_channel']:.3f}")
            report.append(f"- 双通道: {metric_data['dual_channel']:.3f}")
            report.append(f"- 改进: {metric_data['improvement']:.3f} ({metric_data['improvement_rate']:.1f}%)")
            report.append("")
        
        # 关键区域性能
        if "key_area_performance" in metrics:
            report.append("## 关键区域性能")
            for area_name, area_data in metrics["key_area_performance"].items():
                report.append(f"### {area_data['description']}")
                report.append(f"- 单通道 Top-1: {area_data['single_channel_top1']:.3f}")
                report.append(f"- 双通道 Top-1: {area_data['dual_channel_top1']:.3f}")
                report.append(f"- 改进: {area_data['improvement']:.3f} ({area_data['improvement_rate']:.1f}%)")
                report.append("")
        
        # 建议和结论
        report.append("## 建议和结论")
        
        # 分析改进幅度
        top1_improvement = metrics.get("top1_accuracy", {}).get("improvement_rate", 0)
        confidence_improvement = metrics.get("avg_confidence", {}).get("improvement_rate", 0)
        margin_improvement = metrics.get("avg_margin", {}).get("improvement_rate", 0)
        
        if top1_improvement > 10:
            report.append("✅ **Top-1准确率显著提升**，双通道融合效果明显")
        elif top1_improvement > 5:
            report.append("⚠️ **Top-1准确率有所提升**，双通道融合有一定效果")
        else:
            report.append("❌ **Top-1准确率提升有限**，需要进一步优化")
        
        if confidence_improvement > 10:
            report.append("✅ **置信度显著提升**，系统确定性增强")
        
        if margin_improvement > 15:
            report.append("✅ **Margin显著提升**，识别稳定性大幅改善")
        
        report.append("")
        report.append("## 下一步优化建议")
        report.append("1. 收集更多测试数据，特别是关键区域的照片")
        report.append("2. 优化权重分配策略，根据场景动态调整")
        report.append("3. 增强空间关系建模，提高空间推理能力")
        report.append("4. 持续优化BLIP提示词，提高描述质量")
        
        return "\n".join(report)
    
    def export_to_csv(self, results: Dict):
        """导出结果到CSV格式"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出详细结果
        detailed_data = []
        for result in results["single_channel_results"] + results["dual_channel_results"]:
            if result.get("success", False):
                detailed_data.append({
                    "photo_id": result["photo_id"],
                    "system_type": result["system_type"],
                    "ground_truth": result["ground_truth"],
                    "area_type": result["area_type"],
                    "top1_correct": result["top1_correct"],
                    "top3_correct": result["top3_correct"],
                    "confidence": result["confidence"],
                    "margin": result["margin"],
                    "response_time": result["response_time"]
                })
        
        if detailed_data:
            df = pd.DataFrame(detailed_data)
            csv_filename = f"detailed_results_{timestamp}.csv"
            csv_filepath = self.results_dir / csv_filename
            df.to_csv(csv_filepath, index=False, encoding='utf-8')
            logger.info(f"详细结果已导出到CSV: {csv_filepath}")
        
        # 导出对比指标
        comparison_data = []
        metrics = results["comparison_metrics"]
        for metric_name, metric_data in metrics.items():
            if metric_name == "key_area_performance":
                continue
            comparison_data.append({
                "metric": metric_name,
                "single_channel": metric_data["single_channel"],
                "dual_channel": metric_data["dual_channel"],
                "improvement": metric_data["improvement"],
                "improvement_rate": metric_data["improvement_rate"]
            })
        
        if comparison_data:
            df_comp = pd.DataFrame(comparison_data)
            comp_csv_filename = f"comparison_metrics_{timestamp}.csv"
            comp_csv_filepath = self.results_dir / comp_csv_filename
            df_comp.to_csv(comp_csv_filepath, index=False, encoding='utf-8')
            logger.info(f"对比指标已导出到CSV: {comp_csv_filepath}")


# 使用示例
if __name__ == "__main__":
    # 创建评测器
    evaluator = DualChannelEvaluator()
    
    # 模拟A/B测试
    print("开始模拟A/B测试...")
    
    # 这里应该传入真实的检索系统
    # 暂时使用模拟结果
    mock_results = evaluator.run_ab_test(
        single_channel_system=None,
        dual_channel_system=None
    )
    
    # 生成报告
    report = evaluator.generate_report(mock_results)
    print(report)
    
    # 导出结果
    evaluator.export_to_csv(mock_results)
