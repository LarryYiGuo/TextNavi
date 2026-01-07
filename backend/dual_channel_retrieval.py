"""
Dual-channel retrieval with fusion scoring for VLN localization
Supports both natural language and structured text channels
"""

import numpy as np
import json
import pathlib
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import os

try:
    import faiss
    USE_FAISS = True
except ImportError:
    USE_FAISS = False

import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualChannelRetrieval:
    """
    双通道检索系统
    通道A: 拓扑语义 (Sense_A_Finetuned.fixed.jsonl)
    通道B: 视觉细节 (Sense_A_MS_optimized.jsonl)
    """
    
    def __init__(self, 
                 channel_a_data: str = None,
                 channel_b_data: str = None):
        """
        初始化双通道检索系统
        
        Args:
            channel_a_data: 通道A数据文件路径（拓扑语义）
            channel_b_data: 通道B数据文件路径（视觉细节）
        """
        # 设置默认路径
        if channel_a_data is None:
            channel_a_data = os.path.join(os.path.dirname(__file__), "data", "Sense_A_Finetuned.fixed.jsonl")
        if channel_b_data is None:
            channel_b_data = os.path.join(os.path.dirname(__file__), "data", "Sense_A_MS_optimized.jsonl")
            
        self.channel_a_data = channel_a_data
        self.channel_b_data = channel_b_data
        
        # 加载数据
        self.channel_a_nodes = self._load_channel_data(channel_a_data)
        self.channel_b_nodes = self._load_channel_data(channel_b_data)
        
        # 权重配置
        self.w_a = 0.45  # 拓扑语义权重
        self.w_b = 0.55  # 视觉细节权重
        
        # 触发词权重调整
        self.trigger_words = {
            "yellow_line": ["yellow line", "floor stripe", "yellow stripe"],
            "qr_code": ["qr", "qr code", "barcode"],
            "drawer": ["drawer", "component drawer", "storage"],
            "glass_door": ["glass door", "glass partition", "transparent"],
            "soft_seats": ["soft seats", "sofa", "cushion"],
            "chair_blocking": ["chair on the line", "blocking", "obstacle"]
        }
        
        # 区域分类
        self.area_categories = {
            "entrance": ["dp_ms_entrance", "dp_bookshelf_qr"],
            "printing": ["poi_3d_printer_table", "workbench_electronics"],
            "yellow_line": ["yellow_line_segment", "path_marking"],
            "window_side": ["atrium_windows_edge", "poi_small_table"],
            "bookshelf_drawer_glass": ["dp_bookshelf_qr", "poi_component_drawer_wall", "glass_partition_office"]
        }
        
        logger.info(f"双通道检索系统初始化完成: 通道A({len(self.channel_a_nodes)}节点), 通道B({len(self.channel_b_nodes)}节点)")
    
    def _load_channel_data(self, file_path: str) -> Dict:
        """加载通道数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                nodes = {}
                for line in f:
                    if line.strip():
                        node = json.loads(line)
                        nodes[node['id']] = node
            return nodes
        except Exception as e:
            logger.error(f"加载数据文件失败 {file_path}: {e}")
            return {}
    
    def _normalize_scores(self, scores: List[float], method: str = "minmax") -> List[float]:
        """
        分数归一化
        
        Args:
            scores: 原始分数列表
            method: 归一化方法 ("minmax" 或 "temperature")
        
        Returns:
            归一化后的分数列表
        """
        if not scores:
            return []
        
        if method == "minmax":
            scaler = MinMaxScaler()
            scores_array = np.array(scores).reshape(-1, 1)
            normalized = scaler.fit_transform(scores_array).flatten()
            return normalized.tolist()
        
        elif method == "temperature":
            # 温度标定 (softmax with temperature)
            temperature = 0.1
            scores_array = np.array(scores)
            exp_scores = np.exp(scores_array / temperature)
            normalized = exp_scores / np.sum(exp_scores)
            return normalized.tolist()
        
        return scores
    
    def _calculate_adaptive_weights(self, query: str) -> Tuple[float, float]:
        """
        基于查询触发词计算自适应权重
        
        Args:
            query: 查询文本
        
        Returns:
            (w_a, w_b): 调整后的权重
        """
        w_a = self.w_a
        w_b = self.w_b
        
        query_lower = query.lower()
        
        # 检查触发词并调整权重
        for category, words in self.trigger_words.items():
            if any(word in query_lower for word in words):
                # 根据触发词类型调整权重
                if category in ["yellow_line", "qr_code", "drawer"]:
                    # 视觉细节更重要
                    w_b = min(0.7, w_b + 0.08)
                    w_a = max(0.3, w_a - 0.08)
                elif category in ["glass_door", "soft_seats", "chair_blocking"]:
                    # 拓扑语义更重要
                    w_a = min(0.7, w_a + 0.08)
                    w_b = max(0.3, w_b - 0.08)
        
        # 确保权重和为1
        total = w_a + w_b
        w_a /= total
        w_b /= total
        
        logger.info(f"自适应权重调整: w_a={w_a:.3f}, w_b={w_b:.3f}")
        return w_a, w_b
    
    def _merge_candidates(self, 
                         candidates_a: List[Tuple[str, float]], 
                         candidates_b: List[Tuple[str, float]]) -> Dict[str, List[float]]:
        """
        对齐与合并候选结果
        
        Args:
            candidates_a: 通道A候选结果 [(id, score), ...]
            candidates_b: 通道B候选结果 [(id, score), ...]
        
        Returns:
            合并后的候选结果 {id: [score_a, score_b]}
        """
        merged = {}
        
        # 处理通道A
        for node_id, score in candidates_a:
            if node_id not in merged:
                merged[node_id] = [score, 0.0]  # [score_a, score_b]
            else:
                merged[node_id][0] = max(merged[node_id][0], score)
        
        # 处理通道B
        for node_id, score in candidates_b:
            if node_id not in merged:
                merged[node_id] = [0.0, score]  # [score_a, score_b]
            else:
                merged[node_id][1] = max(merged[node_id][1], score)
        
        return merged
    
    def _apply_diversity_reranking(self, 
                                  candidates: List[Tuple[str, float]], 
                                  threshold: float = 0.95) -> List[Tuple[str, float]]:
        """
        多样性重排，去除近重复描述
        
        Args:
            candidates: 候选结果 [(id, score), ...]
            threshold: 余弦相似度阈值
        
        Returns:
            重排后的候选结果
        """
        if len(candidates) <= 1:
            return candidates
        
        # 获取节点描述用于相似度计算
        node_descriptions = {}
        for node_id, _ in candidates:
            desc_a = self.channel_a_nodes.get(node_id, {}).get('nl_text', '')
            desc_b = self.channel_b_nodes.get(node_id, {}).get('nl_text', '')
            node_descriptions[node_id] = f"{desc_a} {desc_b}".strip()
        
        # 计算相似度矩阵
        ids = list(node_descriptions.keys())
        descriptions = list(node_descriptions.values())
        
        # 简单的文本相似度计算（可以替换为更复杂的embedding相似度）
        similarity_matrix = np.zeros((len(ids), len(ids)))
        for i in range(len(ids)):
            for j in range(len(ids)):
                if i != j:
                    # 计算词汇重叠度作为相似度
                    words_i = set(descriptions[i].lower().split())
                    words_j = set(descriptions[j].lower().split())
                    if words_i and words_j:
                        similarity = len(words_i & words_j) / len(words_i | words_j)
                        similarity_matrix[i][j] = similarity
        
        # 应用NMS去除重复
        filtered_candidates = []
        for i, (node_id, score) in enumerate(candidates):
            is_duplicate = False
            for j, (existing_id, existing_score) in enumerate(filtered_candidates):
                if similarity_matrix[i][j] > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_candidates.append((node_id, score))
        
        # 确保区域多样性
        diverse_candidates = self._ensure_area_diversity(filtered_candidates)
        
        return diverse_candidates
    
    def _ensure_area_diversity(self, candidates: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        确保Top-10涵盖不同区域
        
        Args:
            candidates: 候选结果
        
        Returns:
            确保区域多样性的候选结果
        """
        if len(candidates) <= 10:
            return candidates
        
        # 统计各区域的数量
        area_counts = {area: 0 for area in self.area_categories}
        
        diverse_candidates = []
        for node_id, score in candidates:
            # 确定节点所属区域
            node_area = None
            for area, nodes in self.area_categories.items():
                if node_id in nodes:
                    node_area = area
                    break
            
            if node_area and area_counts[node_area] < 3:  # 每个区域最多3个
                diverse_candidates.append((node_id, score))
                area_counts[node_area] += 1
            elif node_area is None:
                # 未分类节点直接添加
                diverse_candidates.append((node_id, score))
            
            if len(diverse_candidates) >= 10:
                break
        
        # 如果还没到10个，添加剩余的
        for node_id, score in candidates:
            if len(diverse_candidates) >= 10:
                break
            if (node_id, score) not in diverse_candidates:
                diverse_candidates.append((node_id, score))
        
        return diverse_candidates[:10]
    
    def retrieve(self, 
                query: str, 
                top_k: int = 10,
                normalize_method: str = "minmax") -> Dict:
        """
        执行双通道检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            normalize_method: 归一化方法
        
        Returns:
            检索结果字典
        """
        logger.info(f"开始双通道检索，查询: {query[:50]}...")
        
        # 1. 计算自适应权重
        w_a, w_b = self._calculate_adaptive_weights(query)
        
        # 2. 分别检索两个通道（这里需要实际的检索逻辑）
        # 暂时使用模拟分数
        candidates_a = self._mock_channel_a_retrieval(query, top_k)
        candidates_b = self._mock_channel_b_retrieval(query, top_k)
        
        # 3. 分数归一化
        scores_a = [score for _, score in candidates_a]
        scores_b = [score for _, score in candidates_b]
        
        normalized_scores_a = self._normalize_scores(scores_a, normalize_method)
        normalized_scores_b = self._normalize_scores(scores_b, normalize_method)
        
        # 更新候选结果分数
        candidates_a = [(id_, score) for (id_, _), score in zip(candidates_a, normalized_scores_a)]
        candidates_b = [(id_, score) for (id_, _), score in zip(candidates_b, normalized_scores_b)]
        
        # 4. 对齐与合并
        merged_candidates = self._merge_candidates(candidates_a, candidates_b)
        
        # 5. 加权求分
        final_scores = {}
        for node_id, (score_a, score_b) in merged_candidates.items():
            final_score = w_a * score_a + w_b * score_b
            final_scores[node_id] = final_score
        
        # 6. 排序
        sorted_candidates = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 7. 多样性重排
        diverse_candidates = self._apply_diversity_reranking(sorted_candidates[:top_k])
        
        # 8. 计算置信度和margin
        confidence = diverse_candidates[0][1] if diverse_candidates else 0.0
        margin = (diverse_candidates[0][1] - diverse_candidates[1][1]) if len(diverse_candidates) > 1 else 0.0
        
        # 9. 确定质量等级
        quality_level = self._determine_quality_level(confidence, margin)
        
        # 10. 构建结果
        result = {
            "query": query,
            "confidence": confidence,
            "margin": margin,
            "quality_level": quality_level,
            "weights": {"w_a": w_a, "w_b": w_b},
            "candidates": [
                {
                    "id": node_id,
                    "score": score,
                    "score_a": merged_candidates.get(node_id, [0.0, 0.0])[0],
                    "score_b": merged_candidates.get(node_id, [0.0, 0.0])[1],
                    "description": self._get_node_description(node_id)
                }
                for node_id, score in diverse_candidates
            ]
        }
        
        logger.info(f"双通道检索完成，置信度: {confidence:.3f}, Margin: {margin:.3f}, 质量等级: {quality_level}")
        return result
    
    def _mock_channel_a_retrieval(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """模拟通道A检索（拓扑语义）"""
        # 这里应该实现实际的检索逻辑
        # 暂时返回模拟结果
        mock_results = [
            ("dp_ms_entrance", 0.85),
            ("poi_3d_printer_table", 0.78),
            ("dp_bookshelf_qr", 0.72),
            ("poi_component_drawer_wall", 0.68),
            ("atrium_entry", 0.65)
        ]
        return mock_results[:top_k]
    
    def _mock_channel_b_retrieval(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """模拟通道B检索（视觉细节）"""
        # 这里应该实现实际的检索逻辑
        # 暂时返回模拟结果
        mock_results = [
            ("poi_3d_printer_table", 0.82),
            ("dp_bookshelf_qr", 0.79),
            ("workbench_electronics", 0.75),
            ("dp_ms_entrance", 0.71),
            ("poi_component_drawer_wall", 0.69)
        ]
        return mock_results[:top_k]
    
    def _get_node_description(self, node_id: str) -> str:
        """获取节点描述"""
        desc_a = self.channel_a_nodes.get(node_id, {}).get('nl_text', '')
        desc_b = self.channel_b_nodes.get(node_id, {}).get('nl_text', '')
        return f"{desc_a} {desc_b}".strip()
    
    def _determine_quality_level(self, confidence: float, margin: float) -> str:
        """
        确定质量等级
        
        Args:
            confidence: 置信度
            margin: Margin值
        
        Returns:
            质量等级
        """
        if confidence >= 0.70 or margin >= 0.25:
            return "✅ 高可用"
        elif confidence >= 0.50 and margin >= 0.10:
            return "⚠️ 需确认"
        else:
            return "❌ 高风险"
    
    def update_weights(self, w_a: float, w_b: float):
        """更新基础权重"""
        self.w_a = w_a
        self.w_b = w_b
        logger.info(f"权重更新: w_a={w_a}, w_b={w_b}")
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "channel_a_nodes": len(self.channel_a_nodes),
            "channel_b_nodes": len(self.channel_b_nodes),
            "current_weights": {"w_a": self.w_a, "w_b": self.w_b},
            "trigger_words": list(self.trigger_words.keys()),
            "area_categories": list(self.area_categories.keys())
        }
