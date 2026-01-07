"""
Enhanced BLIP prompts for better landmark distinction
Optimized prompts to generate more discriminative descriptions
"""

from typing import List, Dict

class EnhancedBLIPPrompts:
    """
    增强的BLIP提示词系统
    目的：让描述中稳定出现关键地标词汇，提升检索可分性
    """
    
    def __init__(self):
        # 基础提示词模板
        self.base_prompts = {
            "default": "Describe this indoor scene briefly with concrete landmarks and layout.",
            "detailed": "Describe this indoor scene with specific landmarks, furniture, and spatial relationships.",
            "landmark_focused": "Focus on identifying key landmarks, objects, and their spatial arrangement."
        }
        
        # 关键地标词汇提示
        self.landmark_keywords = [
            "floor markings (like a yellow line)",
            "doors and partitions",
            "shelves and storage",
            "QR codes and signs",
            "printers and equipment",
            "sofas and seating",
            "tables and workbenches",
            "chairs blocking paths"
        ]
        
        # 场景特定提示词
        self.scene_specific_prompts = {
            "SCENE_A_MS": {
                "maker_space": "Describe this Maker Space area with 3D printers, workbenches, and tools.",
                "entrance": "Describe the entrance area with benches, recycling bins, and initial landmarks.",
                "printing_zone": "Focus on 3D printers, filament spools, and printing equipment.",
                "electronics_zone": "Describe electronics workbench with oscilloscopes and soldering tools.",
                "storage_zone": "Focus on component drawers, storage shelves, and organization systems.",
                "collaboration_zone": "Describe meeting areas, tables, and collaborative spaces."
            },
            "SCENE_B_STUDIO": {
                "studio_main": "Describe this studio space with equipment, seating, and work areas.",
                "window_area": "Focus on windows, natural light, and window-side furniture.",
                "central_area": "Describe the central workspace and main equipment.",
                "storage_area": "Focus on storage solutions and organizational systems."
            }
        }
        
        # 地标类型提示词
        self.landmark_type_prompts = {
            "yellow_line": "Look for and describe any floor markings, lines, or path indicators.",
            "qr_code": "Identify and describe any QR codes, barcodes, or signage.",
            "drawer": "Describe storage systems, drawers, and organizational furniture.",
            "glass": "Focus on glass partitions, doors, and transparent elements.",
            "seating": "Describe seating arrangements, sofas, chairs, and comfort areas.",
            "obstacles": "Identify any objects blocking paths or creating obstacles."
        }
    
    def get_enhanced_prompt(self, 
                           scene_id: str = "SCENE_A_MS",
                           area_type: str = "default",
                           landmark_focus: str = None) -> str:
        """
        获取增强的BLIP提示词
        
        Args:
            scene_id: 场景ID
            area_type: 区域类型
            landmark_focus: 特定地标类型
        
        Returns:
            增强的提示词
        """
        # 基础提示词
        if area_type in self.scene_specific_prompts.get(scene_id, {}):
            base_prompt = self.scene_specific_prompts[scene_id][area_type]
        else:
            base_prompt = self.base_prompts["detailed"]
        
        # 添加关键地标词汇
        landmark_instruction = " Mention floor markings (like a yellow line), doors, shelves, QR codes, printers, sofas, soft seats, tables, and any chairs blocking a path."
        
        # 添加长度和风格要求
        style_instruction = " Keep 1–2 sentences, noun-heavy, and focus on distinctive visual features."
        
        # 组合完整提示词
        full_prompt = base_prompt + landmark_instruction + style_instruction
        
        # 如果指定了特定地标类型，添加额外提示
        if landmark_focus and landmark_focus in self.landmark_type_prompts:
            full_prompt += " " + self.landmark_type_prompts[landmark_focus]
        
        return full_prompt
    
    def get_adaptive_prompt(self, 
                           query_context: str = "",
                           previous_descriptions: List[str] = None) -> str:
        """
        获取自适应提示词（基于查询上下文）
        
        Args:
            query_context: 查询上下文
            previous_descriptions: 之前的描述列表
        
        Returns:
            自适应的提示词
        """
        # 分析查询上下文，识别关键词汇
        query_lower = query_context.lower()
        
        # 检测查询中的关键地标类型
        detected_landmarks = []
        for landmark_type, keywords in self.landmark_type_prompts.items():
            if any(keyword in query_lower for keyword in keywords.split()):
                detected_landmarks.append(landmark_type)
        
        # 基础提示词
        base_prompt = self.base_prompts["landmark_focused"]
        
        # 添加检测到的地标类型提示
        if detected_landmarks:
            landmark_instruction = f" Pay special attention to: {', '.join(detected_landmarks)}."
        else:
            landmark_instruction = " Focus on identifying key landmarks and spatial relationships."
        
        # 添加多样性要求（避免重复描述）
        if previous_descriptions:
            diversity_instruction = " Provide a fresh perspective and avoid repeating previous descriptions."
        else:
            diversity_instruction = ""
        
        # 组合完整提示词
        full_prompt = base_prompt + landmark_instruction + diversity_instruction + " Keep 1–2 sentences, noun-heavy."
        
        return full_prompt
    
    def get_contextual_prompt(self, 
                             current_location: str = "",
                             target_location: str = "",
                             navigation_context: str = "") -> str:
        """
        获取上下文相关的提示词（基于导航上下文）
        
        Args:
            current_location: 当前位置
            target_location: 目标位置
            navigation_context: 导航上下文
        
        Returns:
            上下文相关的提示词
        """
        # 基础提示词
        base_prompt = "Describe your current location and surroundings to help with navigation."
        
        # 添加位置上下文
        if current_location and target_location:
            location_context = f" You are at {current_location} and need to reach {target_location}."
        elif current_location:
            location_context = f" You are currently at {current_location}."
        else:
            location_context = ""
        
        # 添加导航上下文
        if navigation_context:
            nav_context = f" Navigation context: {navigation_context}."
        else:
            nav_context = ""
        
        # 添加地标识别要求
        landmark_requirement = " Identify key landmarks, obstacles, and spatial relationships that will help with navigation."
        
        # 组合完整提示词
        full_prompt = base_prompt + location_context + nav_context + landmark_requirement + " Keep 1–2 sentences, noun-heavy."
        
        return full_prompt
    
    def get_quality_enhancement_prompt(self, 
                                     description_quality: str = "medium") -> str:
        """
        获取质量增强提示词
        
        Args:
            description_quality: 描述质量 ("low", "medium", "high")
        
        Returns:
            质量增强提示词
        """
        if description_quality == "low":
            enhancement = "Provide a more detailed and specific description. Focus on unique visual features and spatial relationships."
        elif description_quality == "medium":
            enhancement = "Enhance the description with more specific details about landmarks and their arrangement."
        else:  # high
            enhancement = "Maintain the high quality while ensuring all key landmarks are clearly identified."
        
        base_prompt = "Review and improve this scene description: "
        full_prompt = base_prompt + enhancement + " Keep 1–2 sentences, noun-heavy, and focus on distinctive features."
        
        return full_prompt
    
    def get_all_prompts(self) -> Dict[str, str]:
        """获取所有可用的提示词"""
        prompts = {}
        
        # 基础提示词
        prompts.update(self.base_prompts)
        
        # 场景特定提示词
        for scene_id, scene_prompts in self.scene_specific_prompts.items():
            for area_type, prompt in scene_prompts.items():
                prompts[f"{scene_id}_{area_type}"] = prompt
        
        # 地标类型提示词
        prompts.update(self.landmark_type_prompts)
        
        return prompts
    
    def analyze_prompt_effectiveness(self, 
                                   prompt: str, 
                                   generated_description: str,
                                   target_landmarks: List[str]) -> Dict:
        """
        分析提示词效果
        
        Args:
            prompt: 使用的提示词
            generated_description: 生成的描述
            target_landmarks: 目标地标列表
        
        Returns:
            效果分析结果
        """
        description_lower = generated_description.lower()
        
        # 计算地标覆盖率
        detected_landmarks = []
        for landmark in target_landmarks:
            if landmark.lower() in description_lower:
                detected_landmarks.append(landmark)
        
        coverage_rate = len(detected_landmarks) / len(target_landmarks) if target_landmarks else 0
        
        # 计算描述长度
        word_count = len(generated_description.split())
        
        # 计算关键词密度
        keyword_density = sum(1 for keyword in self.landmark_keywords if keyword.lower() in description_lower)
        
        # 评估结果
        if coverage_rate >= 0.8 and word_count >= 15:
            effectiveness = "high"
        elif coverage_rate >= 0.6 and word_count >= 10:
            effectiveness = "medium"
        else:
            effectiveness = "low"
        
        return {
            "prompt": prompt,
            "generated_description": generated_description,
            "target_landmarks": target_landmarks,
            "detected_landmarks": detected_landmarks,
            "coverage_rate": coverage_rate,
            "word_count": word_count,
            "keyword_density": keyword_density,
            "effectiveness": effectiveness
        }
    
    def optimize_prompt(self, 
                       base_prompt: str,
                       effectiveness_results: List[Dict]) -> str:
        """
        基于效果分析优化提示词
        
        Args:
            base_prompt: 基础提示词
            effectiveness_results: 效果分析结果列表
        
        Returns:
            优化后的提示词
        """
        if not effectiveness_results:
            return base_prompt
        
        # 分析高效果提示词的特征
        high_effect_prompts = [r for r in effectiveness_results if r["effectiveness"] == "high"]
        
        if not high_effect_prompts:
            return base_prompt
        
        # 提取高效果提示词中的关键元素
        common_elements = []
        for result in high_effect_prompts:
            prompt = result["prompt"]
            # 这里可以添加更复杂的分析逻辑
            if "landmark" in prompt.lower():
                common_elements.append("landmark focus")
            if "spatial" in prompt.lower():
                common_elements.append("spatial relationships")
            if "specific" in prompt.lower():
                common_elements.append("specific details")
        
        # 优化提示词
        optimized_prompt = base_prompt
        
        if "landmark focus" not in common_elements:
            optimized_prompt += " Focus on identifying key landmarks."
        if "spatial relationships" not in common_elements:
            optimized_prompt += " Describe spatial relationships between objects."
        if "specific details" not in common_elements:
            optimized_prompt += " Provide specific visual details."
        
        return optimized_prompt


# 使用示例
if __name__ == "__main__":
    # 创建提示词系统
    prompt_system = EnhancedBLIPPrompts()
    
    # 获取增强提示词
    enhanced_prompt = prompt_system.get_enhanced_prompt(
        scene_id="SCENE_A_MS",
        area_type="printing_zone"
    )
    print("Enhanced Prompt:", enhanced_prompt)
    
    # 获取自适应提示词
    adaptive_prompt = prompt_system.get_adaptive_prompt(
        query_context="I need to find the yellow line"
    )
    print("Adaptive Prompt:", adaptive_prompt)
    
    # 获取上下文提示词
    contextual_prompt = prompt_system.get_contextual_prompt(
        current_location="3D printer table",
        target_location="atrium"
    )
    print("Contextual Prompt:", contextual_prompt)
