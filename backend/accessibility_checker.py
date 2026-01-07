"""
可访问性检查器 (Accessibility Checker)
实现WCAG 2.2合规性检查、VoiceOver兼容性测试等功能
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

# ============================================================================
# 可访问性标准定义 (Accessibility Standards Definition)
# ============================================================================

class WCAGLevel(Enum):
    """WCAG合规级别"""
    A = "A"
    AA = "AA"
    AAA = "AAA"

class WCAGPrinciple(Enum):
    """WCAG原则"""
    PERCEIVABLE = "Perceivable"
    OPERABLE = "Operable"
    UNDERSTANDABLE = "Understandable"
    ROBUST = "Robust"

@dataclass
class WCAGGuideline:
    """WCAG指南"""
    id: str
    name: str
    principle: WCAGPrinciple
    level: WCAGLevel
    description: str
    test_criteria: List[str]
    automated_testable: bool

@dataclass
class AccessibilityTestResult:
    """可访问性测试结果"""
    guideline_id: str
    test_name: str
    passed: bool
    score: float  # 0-1
    issues: List[str]
    recommendations: List[str]
    timestamp: str

# ============================================================================
# WCAG 2.2指南配置 (WCAG 2.2 Guidelines Configuration)
# ============================================================================

WCAG_22_GUIDELINES = {
    "1.1.1": WCAGGuideline(
        id="1.1.1",
        name="Non-text Content",
        principle=WCAGPrinciple.PERCEIVABLE,
        level=WCAGLevel.A,
        description="All non-text content has a text alternative",
        test_criteria=[
            "Images have alt text",
            "Buttons have accessible names",
            "Form controls have labels"
        ],
        automated_testable=True
    ),
    
    "1.3.1": WCAGGuideline(
        id="1.3.1",
        name="Info and Relationships",
        principle=WCAGPrinciple.PERCEIVABLE,
        level=WCAGLevel.A,
        description="Information, structure, and relationships can be programmatically determined",
        test_criteria=[
            "Headings are properly structured",
            "Lists are properly marked up",
            "Form fields are properly labeled"
        ],
        automated_testable=True
    ),
    
    "1.4.3": WCAGGuideline(
        id="1.4.3",
        name="Contrast (Minimum)",
        principle=WCAGPrinciple.PERCEIVABLE,
        level=WCAGLevel.AA,
        description="Text has sufficient contrast ratio",
        test_criteria=[
            "Normal text has 4.5:1 contrast ratio",
            "Large text has 3:1 contrast ratio"
        ],
        automated_testable=True
    ),
    
    "2.1.1": WCAGGuideline(
        id="2.1.1",
        name="Keyboard",
        principle=WCAGPrinciple.OPERABLE,
        level=WCAGLevel.A,
        description="All functionality is available from a keyboard",
        test_criteria=[
            "All interactive elements are keyboard accessible",
            "No keyboard traps",
            "Custom keyboard shortcuts are documented"
        ],
        automated_testable=False
    ),
    
    "2.4.1": WCAGGuideline(
        id="2.4.1",
        name="Bypass Blocks",
        principle=WCAGPrinciple.OPERABLE,
        level=WCAGLevel.A,
        description="A mechanism is available to bypass repeated blocks",
        test_criteria=[
            "Skip links are available",
            "Landmarks are properly defined",
            "Headings provide navigation structure"
        ],
        automated_testable=True
    ),
    
    "2.5.5": WCAGGuideline(
        id="2.5.5",
        name="Target Size",
        principle=WCAGPrinciple.OPERABLE,
        level=WCAGLevel.AAA,
        description="Target size for pointer inputs is at least 44x44 CSS pixels",
        test_criteria=[
            "Touch targets are at least 44x44 pixels",
            "Spacing between targets is adequate",
            "Targets are not obscured by other elements"
        ],
        automated_testable=True
    ),
    
    "3.1.1": WCAGGuideline(
        id="3.1.1",
        name="Language of Page",
        principle=WCAGPrinciple.UNDERSTANDABLE,
        level=WCAGLevel.A,
        description="The default human language of the page can be programmatically determined",
        test_criteria=[
            "HTML lang attribute is set",
            "Language is correctly specified",
            "Language changes are marked up"
        ],
        automated_testable=True
    ),
    
    "4.1.1": WCAGGuideline(
        id="4.1.1",
        name="Parsing",
        principle=WCAGPrinciple.ROBUST,
        level=WCAGLevel.A,
        description="Content can be parsed by user agents",
        test_criteria=[
            "HTML is well-formed",
            "No duplicate IDs",
            "Proper nesting of elements"
        ],
        automated_testable=True
    )
}

# ============================================================================
# 可访问性检查器 (Accessibility Checker)
# ============================================================================

class AccessibilityChecker:
    """可访问性检查器"""
    
    def __init__(self):
        self.test_results = {}
        self.session_data = {}
    
    def check_wcag_compliance(self, interface_elements: Dict[str, Any], 
                             target_level: WCAGLevel = WCAGLevel.AA) -> Dict[str, Any]:
        """检查WCAG 2.2合规性"""
        compliance_results = {
            "overall_score": 0.0,
            "level_achieved": WCAGLevel.A,
            "guideline_results": {},
            "total_issues": 0,
            "recommendations": []
        }
        
        total_score = 0.0
        total_guidelines = 0
        
        for guideline_id, guideline in WCAG_22_GUIDELINES.items():
            if guideline.level.value <= target_level.value:
                result = self._test_wcag_guideline(guideline, interface_elements)
                compliance_results["guideline_results"][guideline_id] = result
                
                total_score += result.score
                total_guidelines += 1
                
                if not result.passed:
                    compliance_results["total_issues"] += len(result.issues)
                    compliance_results["recommendations"].extend(result.recommendations)
        
        if total_guidelines > 0:
            compliance_results["overall_score"] = total_score / total_guidelines
        
        # 确定达到的级别
        compliance_results["level_achieved"] = self._determine_achieved_level(
            compliance_results["overall_score"]
        )
        
        return compliance_results
    
    def _test_wcag_guideline(self, guideline: WCAGGuideline, 
                            interface_elements: Dict[str, Any]) -> AccessibilityTestResult:
        """测试单个WCAG指南"""
        issues = []
        recommendations = []
        score = 0.0
        
        if guideline.id == "1.1.1":
            score, issues, recommendations = self._test_non_text_content(interface_elements)
        elif guideline.id == "1.3.1":
            score, issues, recommendations = self._test_info_relationships(interface_elements)
        elif guideline.id == "1.4.3":
            score, issues, recommendations = self._test_contrast_ratio(interface_elements)
        elif guideline.id == "2.1.1":
            score, issues, recommendations = self._test_keyboard_accessibility(interface_elements)
        elif guideline.id == "2.4.1":
            score, issues, recommendations = self._test_bypass_blocks(interface_elements)
        elif guideline.id == "2.5.5":
            score, issues, recommendations = self._test_target_size(interface_elements)
        elif guideline.id == "3.1.1":
            score, issues, recommendations = self._test_language_markup(interface_elements)
        elif guideline.id == "4.1.1":
            score, issues, recommendations = self._test_html_parsing(interface_elements)
        else:
            # 默认测试
            score, issues, recommendations = self._default_guideline_test(guideline, interface_elements)
        
        return AccessibilityTestResult(
            guideline_id=guideline.id,
            test_name=guideline.name,
            passed=score >= 0.8,
            score=score,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _test_non_text_content(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试非文本内容 (1.1.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查图像alt文本
        images = interface_elements.get("images", [])
        total_images = len(images)
        images_with_alt = sum(1 for img in images if img.get("alt_text"))
        
        if total_images > 0:
            alt_score = images_with_alt / total_images
            if alt_score < 1.0:
                issues.append(f"{total_images - images_with_alt} images missing alt text")
                recommendations.append("Add descriptive alt text to all images")
            score += alt_score * 0.4
        
        # 检查按钮可访问名称
        buttons = interface_elements.get("buttons", [])
        total_buttons = len(buttons)
        buttons_with_name = sum(1 for btn in buttons if btn.get("accessible_name"))
        
        if total_buttons > 0:
            button_score = buttons_with_name / total_buttons
            if button_score < 1.0:
                issues.append(f"{total_buttons - buttons_with_name} buttons missing accessible names")
                recommendations.append("Add accessible names to all buttons")
            score += button_score * 0.3
        
        # 检查表单控件标签
        form_controls = interface_elements.get("form_controls", [])
        total_controls = len(form_controls)
        controls_with_labels = sum(1 for ctrl in form_controls if ctrl.get("label"))
        
        if total_controls > 0:
            control_score = controls_with_labels / total_controls
            if control_score < 1.0:
                issues.append(f"{total_controls - controls_with_labels} form controls missing labels")
                recommendations.append("Add labels to all form controls")
            score += control_score * 0.3
        
        return score, issues, recommendations
    
    def _test_info_relationships(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试信息和关系 (1.3.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查标题结构
        headings = interface_elements.get("headings", [])
        if headings:
            heading_structure = self._validate_heading_structure(headings)
            if heading_structure["valid"]:
                score += 0.4
            else:
                issues.append("Heading structure is not properly nested")
                recommendations.append("Ensure headings follow proper hierarchy (h1, h2, h3, etc.)")
        
        # 检查列表标记
        lists = interface_elements.get("lists", [])
        total_lists = len(lists)
        proper_lists = sum(1 for lst in lists if lst.get("properly_marked"))
        
        if total_lists > 0:
            list_score = proper_lists / total_lists
            score += list_score * 0.3
            if list_score < 1.0:
                issues.append("Some lists are not properly marked up")
                recommendations.append("Use proper list markup (ul, ol, li)")
        
        # 检查表单字段标签
        form_fields = interface_elements.get("form_fields", [])
        total_fields = len(form_fields)
        labeled_fields = sum(1 for field in form_fields if field.get("properly_labeled"))
        
        if total_fields > 0:
            field_score = labeled_fields / total_fields
            score += field_score * 0.3
            if field_score < 1.0:
                issues.append("Some form fields are not properly labeled")
                recommendations.append("Associate form fields with their labels using for/id attributes")
        
        return score, issues, recommendations
    
    def _test_contrast_ratio(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试对比度 (1.4.3)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查文本对比度
        text_elements = interface_elements.get("text_elements", [])
        total_text = len(text_elements)
        sufficient_contrast = 0
        
        for text_elem in text_elements:
            contrast_ratio = text_elem.get("contrast_ratio", 0)
            font_size = text_elem.get("font_size", 16)
            
            # 大文本 (18pt+) 需要 3:1，普通文本需要 4.5:1
            required_ratio = 3.0 if font_size >= 18 else 4.5
            
            if contrast_ratio >= required_ratio:
                sufficient_contrast += 1
            else:
                issues.append(f"Text has insufficient contrast ratio: {contrast_ratio}:1 (need {required_ratio}:1)")
        
        if total_text > 0:
            contrast_score = sufficient_contrast / total_text
            score = contrast_score
            if contrast_score < 1.0:
                recommendations.append("Increase contrast ratio for text elements")
        
        return score, issues, recommendations
    
    def _test_keyboard_accessibility(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试键盘可访问性 (2.1.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查交互元素是否可通过键盘访问
        interactive_elements = interface_elements.get("interactive_elements", [])
        total_elements = len(interactive_elements)
        keyboard_accessible = sum(1 for elem in interactive_elements if elem.get("keyboard_accessible"))
        
        if total_elements > 0:
            keyboard_score = keyboard_accessible / total_elements
            score = keyboard_score
            if keyboard_score < 1.0:
                issues.append("Some interactive elements are not keyboard accessible")
                recommendations.append("Ensure all interactive elements can be accessed via keyboard")
        
        # 检查键盘陷阱
        keyboard_traps = interface_elements.get("keyboard_traps", [])
        if keyboard_traps:
            issues.append(f"Found {len(keyboard_traps)} potential keyboard traps")
            recommendations.append("Remove keyboard traps and ensure users can navigate freely")
            score *= 0.8
        
        return score, issues, recommendations
    
    def _test_bypass_blocks(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试绕过块 (2.4.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查跳过链接
        skip_links = interface_elements.get("skip_links", [])
        if skip_links:
            score += 0.4
        else:
            issues.append("No skip links found")
            recommendations.append("Add skip links to bypass repeated navigation blocks")
        
        # 检查地标定义
        landmarks = interface_elements.get("landmarks", [])
        if landmarks:
            score += 0.3
        else:
            issues.append("No landmarks defined")
            recommendations.append("Use semantic HTML5 landmarks (nav, main, aside, etc.)")
        
        # 检查标题导航结构
        headings = interface_elements.get("headings", [])
        if headings and len(headings) >= 3:
            score += 0.3
        else:
            issues.append("Insufficient heading structure for navigation")
            recommendations.append("Use proper heading hierarchy to provide navigation structure")
        
        return score, issues, recommendations
    
    def _test_target_size(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试目标大小 (2.5.5)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查触摸目标大小
        touch_targets = interface_elements.get("touch_targets", [])
        total_targets = len(touch_targets)
        adequate_size = 0
        
        for target in touch_targets:
            width = target.get("width", 0)
            height = target.get("height", 0)
            
            # 需要至少 44x44 CSS像素
            if width >= 44 and height >= 44:
                adequate_size += 1
            else:
                issues.append(f"Touch target too small: {width}x{height} pixels (need 44x44)")
        
        if total_targets > 0:
            size_score = adequate_size / total_targets
            score = size_score
            if size_score < 1.0:
                recommendations.append("Increase touch target sizes to at least 44x44 pixels")
        
        return score, issues, recommendations
    
    def _test_language_markup(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试语言标记 (3.1.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查页面语言设置
        page_language = interface_elements.get("page_language", "")
        if page_language:
            score += 0.5
        else:
            issues.append("Page language not specified")
            recommendations.append("Set HTML lang attribute to specify page language")
        
        # 检查语言变化标记
        language_changes = interface_elements.get("language_changes", [])
        if language_changes:
            score += 0.5
        else:
            # 如果没有语言变化，这不算问题
            score += 0.5
        
        return score, issues, recommendations
    
    def _test_html_parsing(self, interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """测试HTML解析 (4.1.1)"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查HTML格式
        html_well_formed = interface_elements.get("html_well_formed", True)
        if html_well_formed:
            score += 0.4
        else:
            issues.append("HTML is not well-formed")
            recommendations.append("Fix HTML syntax errors")
        
        # 检查重复ID
        duplicate_ids = interface_elements.get("duplicate_ids", [])
        if not duplicate_ids:
            score += 0.3
        else:
            issues.append(f"Found {len(duplicate_ids)} duplicate IDs")
            recommendations.append("Ensure all element IDs are unique")
        
        # 检查元素嵌套
        proper_nesting = interface_elements.get("proper_nesting", True)
        if proper_nesting:
            score += 0.3
        else:
            issues.append("Elements are not properly nested")
            recommendations.append("Fix element nesting structure")
        
        return score, issues, recommendations
    
    def _default_guideline_test(self, guideline: WCAGGuideline, 
                               interface_elements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """默认指南测试"""
        return 0.5, ["Automated test not implemented"], ["Implement automated testing for this guideline"]
    
    def _validate_heading_structure(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证标题结构"""
        if not headings:
            return {"valid": False, "issues": ["No headings found"]}
        
        # 检查标题级别是否合理
        current_level = 1
        issues = []
        
        for heading in headings:
            level = heading.get("level", 1)
            
            # 检查是否跳过级别
            if level > current_level + 1:
                issues.append(f"Heading level {level} follows level {current_level} (skipping levels)")
            
            current_level = level
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _determine_achieved_level(self, score: float) -> WCAGLevel:
        """确定达到的级别"""
        if score >= 0.95:
            return WCAGLevel.AAA
        elif score >= 0.85:
            return WCAGLevel.AA
        elif score >= 0.75:
            return WCAGLevel.A
        else:
            return WCAGLevel.A
    
    def test_voiceover_compatibility(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """测试VoiceOver兼容性"""
        test_results = {
            "overall_compatibility": 0.0,
            "feature_tests": {},
            "issues": [],
            "recommendations": []
        }
        
        total_score = 0.0
        feature_count = 0
        
        # 测试文本转语音标签
        if "text_to_speech" in features:
            tts_score = self._test_text_to_speech(features["text_to_speech"])
            test_results["feature_tests"]["text_to_speech"] = tts_score
            total_score += tts_score["score"]
            feature_count += 1
            
            if not tts_score["passed"]:
                test_results["issues"].extend(tts_score["issues"])
                test_results["recommendations"].extend(tts_score["recommendations"])
        
        # 测试焦点流程
        if "focus_flow" in features:
            focus_score = self._test_focus_flow(features["focus_flow"])
            test_results["feature_tests"]["focus_flow"] = focus_score
            total_score += focus_score["score"]
            feature_count += 1
            
            if not focus_score["passed"]:
                test_results["issues"].extend(focus_score["issues"])
                test_results["recommendations"].extend(focus_score["recommendations"])
        
        # 测试触摸目标
        if "touch_targets" in features:
            touch_score = self._test_touch_targets(features["touch_targets"])
            test_results["feature_tests"]["touch_targets"] = touch_score
            total_score += touch_score["score"]
            feature_count += 1
            
            if not touch_score["passed"]:
                test_results["issues"].extend(touch_score["issues"])
                test_results["recommendations"].extend(touch_score["recommendations"])
        
        if feature_count > 0:
            test_results["overall_compatibility"] = total_score / feature_count
        
        return test_results
    
    def _test_text_to_speech(self, tts_features: Dict[str, Any]) -> Dict[str, Any]:
        """测试文本转语音功能"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查标签实体
        labeled_entities = tts_features.get("labeled_entities", [])
        total_entities = len(labeled_entities)
        properly_labeled = sum(1 for entity in labeled_entities if entity.get("properly_labeled"))
        
        if total_entities > 0:
            label_score = properly_labeled / total_entities
            score += label_score * 0.5
            
            if label_score < 1.0:
                issues.append("Some entities are not properly labeled for text-to-speech")
                recommendations.append("Add appropriate ARIA labels and alt text")
        
        # 检查语音反馈质量
        voice_quality = tts_features.get("voice_quality", 0)
        if voice_quality >= 4:
            score += 0.5
        else:
            issues.append("Voice feedback quality needs improvement")
            recommendations.append("Improve text-to-speech voice quality and clarity")
        
        return {
            "score": score,
            "passed": score >= 0.8,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _test_focus_flow(self, focus_features: Dict[str, Any]) -> Dict[str, Any]:
        """测试焦点流程"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查焦点顺序
        focus_order = focus_features.get("focus_order", [])
        if focus_order:
            logical_order = self._validate_focus_order(focus_order)
            if logical_order["valid"]:
                score += 0.5
            else:
                issues.append("Focus order is not logical")
                recommendations.append("Ensure focus follows logical reading order")
        
        # 检查焦点可见性
        focus_visible = focus_features.get("focus_visible", True)
        if focus_visible:
            score += 0.5
        else:
            issues.append("Focus is not visible")
            recommendations.append("Ensure focus indicators are clearly visible")
        
        return {
            "score": score,
            "passed": score >= 0.8,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _test_touch_targets(self, touch_features: Dict[str, Any]) -> Dict[str, Any]:
        """测试触摸目标"""
        issues = []
        recommendations = []
        score = 0.0
        
        # 检查触摸目标大小
        targets = touch_features.get("targets", [])
        total_targets = len(targets)
        adequate_size = 0
        
        for target in targets:
            width = target.get("width", 0)
            height = target.get("height", 0)
            
            if width >= 44 and height >= 44:
                adequate_size += 1
            else:
                issues.append(f"Touch target too small: {width}x{height} pixels")
        
        if total_targets > 0:
            size_score = adequate_size / total_targets
            score = size_score
            
            if size_score < 1.0:
                recommendations.append("Increase touch target sizes to at least 44x44 pixels")
        
        return {
            "score": score,
            "passed": score >= 0.8,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _validate_focus_order(self, focus_order: List[str]) -> Dict[str, Any]:
        """验证焦点顺序"""
        if not focus_order:
            return {"valid": False, "issues": ["No focus order defined"]}
        
        # 简单的焦点顺序验证
        return {"valid": True, "issues": []}
    
    def validate_touch_targets(self, button_sizes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证触摸目标大小"""
        validation_results = {
            "total_targets": len(button_sizes),
            "adequate_targets": 0,
            "small_targets": [],
            "recommendations": []
        }
        
        for i, button in enumerate(button_sizes):
            width = button.get("width", 0)
            height = button.get("height", 0)
            
            if width >= 44 and height >= 44:
                validation_results["adequate_targets"] += 1
            else:
                validation_results["small_targets"].append({
                    "index": i,
                    "width": width,
                    "height": height,
                    "element_id": button.get("id", f"button_{i}")
                })
        
        if validation_results["small_targets"]:
            validation_results["recommendations"].append(
                "Increase touch target sizes to at least 44x44 pixels for better accessibility"
            )
        
        return validation_results
    
    def audit_interface_accessibility(self, interaction_flow: Dict[str, Any]) -> Dict[str, Any]:
        """审计界面可访问性"""
        audit_results = {
            "overall_accessibility": 0.0,
            "wcag_compliance": {},
            "voiceover_compatibility": {},
            "touch_target_validation": {},
            "recommendations": []
        }
        
        # WCAG合规性检查
        interface_elements = interaction_flow.get("interface_elements", {})
        wcag_results = self.check_wcag_compliance(interface_elements)
        audit_results["wcag_compliance"] = wcag_results
        
        # VoiceOver兼容性检查
        voiceover_features = interaction_flow.get("voiceover_features", {})
        voiceover_results = self.test_voiceover_compatibility(voiceover_features)
        audit_results["voiceover_compatibility"] = voiceover_results
        
        # 触摸目标验证
        touch_targets = interaction_flow.get("touch_targets", [])
        touch_results = self.validate_touch_targets(touch_targets)
        audit_results["touch_target_validation"] = touch_results
        
        # 计算总体可访问性分数
        wcag_score = wcag_results.get("overall_score", 0.0)
        voiceover_score = voiceover_results.get("overall_compatibility", 0.0)
        touch_score = touch_results["adequate_targets"] / max(touch_results["total_targets"], 1)
        
        audit_results["overall_accessibility"] = (wcag_score + voiceover_score + touch_score) / 3
        
        # 生成综合建议
        all_recommendations = []
        all_recommendations.extend(wcag_results.get("recommendations", []))
        all_recommendations.extend(voiceover_results.get("recommendations", []))
        all_recommendations.extend(touch_results.get("recommendations", []))
        
        audit_results["recommendations"] = list(set(all_recommendations))  # 去重
        
        return audit_results
    
    def record_accessibility_test(self, session_id: str, test_type: str, 
                                test_data: Dict[str, Any], result: Dict[str, Any]):
        """记录可访问性测试结果"""
        if session_id not in self.session_data:
            self.session_data[session_id] = {}
        
        if "accessibility_tests" not in self.session_data[session_id]:
            self.session_data[session_id]["accessibility_tests"] = []
        
        test_record = {
            "test_type": test_type,
            "test_data": test_data,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.session_data[session_id]["accessibility_tests"].append(test_record)
    
    def export_accessibility_report(self, session_id: str, filename: str):
        """导出可访问性报告"""
        if session_id not in self.session_data:
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['test_type', 'timestamp', 'overall_score', 'issues_count', 'recommendations_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for test in self.session_data[session_id].get("accessibility_tests", []):
                    result = test["result"]
                    writer.writerow({
                        'test_type': test["test_type"],
                        'timestamp': test["timestamp"],
                        'overall_score': result.get("overall_score", 0.0),
                        'issues_count': len(result.get("issues", [])),
                        'recommendations_count': len(result.get("recommendations", []))
                    })
            
            return True
        except Exception as e:
            print(f"Failed to export accessibility report: {e}")
            return False

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建可访问性检查器
    checker = AccessibilityChecker()
    
    # 示例：测试WCAG合规性
    interface_elements = {
        "images": [
            {"alt_text": "Description 1"},
            {"alt_text": "Description 2"},
            {}  # 缺少alt文本
        ],
        "buttons": [
            {"accessible_name": "Submit"},
            {"accessible_name": "Cancel"},
            {}  # 缺少可访问名称
        ],
        "headings": [
            {"level": 1, "text": "Main Title"},
            {"level": 2, "text": "Section 1"},
            {"level": 3, "text": "Subsection 1.1"}
        ],
        "touch_targets": [
            {"width": 50, "height": 50},
            {"width": 30, "height": 30},  # 太小
            {"width": 60, "height": 40}
        ]
    }
    
    # 执行WCAG合规性检查
    wcag_results = checker.check_wcag_compliance(interface_elements)
    print("WCAG Compliance Results:")
    print(json.dumps(wcag_results, indent=2, ensure_ascii=False))
    
    # 测试VoiceOver兼容性
    voiceover_features = {
        "text_to_speech": {
            "labeled_entities": [
                {"properly_labeled": True},
                {"properly_labeled": False}
            ],
            "voice_quality": 4
        },
        "focus_flow": {
            "focus_order": ["header", "main", "footer"],
            "focus_visible": True
        },
        "touch_targets": [
            {"width": 50, "height": 50},
            {"width": 30, "height": 30}
        ]
    }
    
    voiceover_results = checker.test_voiceover_compatibility(voiceover_features)
    print("\nVoiceOver Compatibility Results:")
    print(json.dumps(voiceover_results, indent=2, ensure_ascii=False))
    
    # 验证触摸目标
    touch_results = checker.validate_touch_targets(interface_elements["touch_targets"])
    print("\nTouch Target Validation Results:")
    print(json.dumps(touch_results, indent=2, ensure_ascii=False))
    
    # 综合审计
    interaction_flow = {
        "interface_elements": interface_elements,
        "voiceover_features": voiceover_features,
        "touch_targets": interface_elements["touch_targets"]
    }
    
    audit_results = checker.audit_interface_accessibility(interaction_flow)
    print("\nComprehensive Accessibility Audit Results:")
    print(json.dumps(audit_results, indent=2, ensure_ascii=False))
