#!/usr/bin/env python3
"""Enhanced RAG Fusion Scoring for improved confidence and success rate"""

import re
from typing import List, Dict, Any, Tuple
from config_optimized import (
    get_rank_alpha, get_rank_beta, get_rank_gamma,
    ENHANCED_KEYWORD_BONUS, COLOR_BONUS, SHAPE_BONUS,
    POSITION_BONUS, QUANTITY_BONUS, BM25_WEIGHT, EMBEDDING_WEIGHT,
    SEMANTIC_SIMILARITY_THRESHOLD, KEYWORD_OVERLAP_THRESHOLD
)

class EnhancedRAGScoring:
    """Enhanced RAG fusion scoring with improved discrimination"""
    
    def __init__(self):
        # Color keywords for enhanced matching
        self.color_keywords = {
            "red": ["red", "crimson", "scarlet", "maroon"],
            "orange": ["orange", "amber", "tangerine", "coral"],
            "yellow": ["yellow", "gold", "amber", "lemon"],
            "green": ["green", "emerald", "teal", "lime", "olive"],
            "blue": ["blue", "navy", "azure", "cobalt", "indigo"],
            "purple": ["purple", "violet", "lavender", "magenta"],
            "brown": ["brown", "tan", "beige", "khaki"],
            "black": ["black", "dark", "ebony", "charcoal"],
            "white": ["white", "light", "ivory", "cream"],
            "gray": ["gray", "grey", "silver", "ash"]
        }
        
        # Shape keywords
        self.shape_keywords = {
            "round": ["round", "circular", "oval", "spherical"],
            "square": ["square", "rectangular", "box", "cubic"],
            "triangular": ["triangular", "triangle", "pyramid"],
            "long": ["long", "elongated", "stretched", "narrow"],
            "wide": ["wide", "broad", "expanded", "spread"]
        }
        
        # Position keywords
        self.position_keywords = {
            "left": ["left", "leftward", "left side", "left-hand"],
            "right": ["right", "rightward", "right side", "right-hand"],
            "ahead": ["ahead", "forward", "in front", "ahead of"],
            "behind": ["behind", "back", "rear", "behind you"],
            "above": ["above", "over", "up", "upward"],
            "below": ["below", "under", "down", "downward"]
        }
        
        # Quantity keywords
        self.quantity_keywords = {
            "single": ["single", "one", "1", "individual"],
            "multiple": ["multiple", "several", "many", "numerous"],
            "pair": ["pair", "two", "2", "couple"],
            "row": ["row", "line", "series", "sequence"],
            "stack": ["stack", "pile", "heap", "bundle"]
        }
    
    def extract_enhanced_features(self, text: str) -> Dict[str, List[str]]:
        """Extract enhanced features from text"""
        text_lower = text.lower()
        features = {
            "colors": [],
            "shapes": [],
            "positions": [],
            "quantities": [],
            "enhanced_keywords": []
        }
        
        # Extract colors
        for color, variants in self.color_keywords.items():
            if any(variant in text_lower for variant in variants):
                features["colors"].append(color)
        
        # Extract shapes
        for shape, variants in self.shape_keywords.items():
            if any(variant in text_lower for variant in variants):
                features["shapes"].append(shape)
        
        # Extract positions
        for position, variants in self.position_keywords.items():
            if any(variant in text_lower for variant in variants):
                features["positions"].append(position)
        
        # Extract quantities
        for quantity, variants in self.quantity_keywords.items():
            if any(variant in text_lower for variant in variants):
                features["quantities"].append(quantity)
        
        # Extract enhanced keywords (specific, descriptive terms)
        enhanced_patterns = [
            r'\b(bright|dark|large|small|tall|short|wide|narrow)\b',
            r'\b(industrial|modern|traditional|vintage|contemporary)\b',
            r'\b(metal|wooden|plastic|glass|fabric|leather)\b',
            r'\b(overhead|floor|wall|ceiling|corner|center)\b',
            r'\b(automatic|manual|digital|analog|electronic)\b'
        ]
        
        for pattern in enhanced_patterns:
            matches = re.findall(pattern, text_lower)
            features["enhanced_keywords"].extend(matches)
        
        return features
    
    def calculate_enhanced_score(self, caption: str, candidate: Dict[str, Any], 
                               provider: str, site_id: str) -> float:
        """Calculate enhanced RAG fusion score"""
        
        # Get base scores
        base_score = candidate.get("score", 0.0)
        nl_score = candidate.get("score_nl", 0.0)
        struct_score = candidate.get("score_struct", 0.0)
        
        # Get weights based on provider
        alpha = get_rank_alpha(provider)
        beta = get_rank_beta(provider)
        gamma = get_rank_gamma(provider)
        
        # Base fusion score
        fusion_score = (alpha * nl_score + (1 - alpha) * struct_score)
        
        # Enhanced keyword matching
        caption_features = self.extract_enhanced_features(caption)
        
        # Get candidate text for comparison
        candidate_text = ""
        if "nl_text" in candidate:
            candidate_text += candidate["nl_text"] + " "
        if "struct_text" in candidate:
            candidate_text += candidate["struct_text"] + " "
        
        candidate_features = self.extract_enhanced_features(candidate_text)
        
        # Calculate feature bonuses
        color_bonus = self._calculate_feature_bonus(
            caption_features["colors"], candidate_features["colors"], COLOR_BONUS
        )
        shape_bonus = self._calculate_feature_bonus(
            caption_features["shapes"], candidate_features["shapes"], SHAPE_BONUS
        )
        position_bonus = self._calculate_feature_bonus(
            caption_features["positions"], candidate_features["positions"], POSITION_BONUS
        )
        quantity_bonus = self._calculate_feature_bonus(
            caption_features["quantities"], candidate_features["quantities"], QUANTITY_BONUS
        )
        
        # Enhanced keyword bonus
        enhanced_bonus = self._calculate_enhanced_keyword_bonus(
            caption_features["enhanced_keywords"], candidate_features["enhanced_keywords"]
        )
        
        # Keyword overlap bonus
        keyword_overlap = self._calculate_keyword_overlap(caption, candidate_text)
        keyword_bonus = beta * keyword_overlap
        
        # Bearing/direction bonus (if available)
        bearing_bonus = gamma * candidate.get("bonus_bearing", 0.0)
        
        # Final enhanced score
        enhanced_score = fusion_score + color_bonus + shape_bonus + position_bonus + \
                        quantity_bonus + enhanced_bonus + keyword_bonus + bearing_bonus
        
        # Ensure score is within [0, 1] range
        enhanced_score = max(0.0, min(1.0, enhanced_score))
        
        return enhanced_score
    
    def _calculate_feature_bonus(self, caption_features: List[str], 
                                candidate_features: List[str], bonus_weight: float) -> float:
        """Calculate bonus for specific feature matches"""
        if not caption_features or not candidate_features:
            return 0.0
        
        # Calculate intersection
        intersection = set(caption_features) & set(candidate_features)
        if intersection:
            # Bonus proportional to intersection size
            return bonus_weight * (len(intersection) / max(len(caption_features), len(candidate_features)))
        
        return 0.0
    
    def _calculate_enhanced_keyword_bonus(self, caption_keywords: List[str], 
                                        candidate_keywords: List[str]) -> float:
        """Calculate bonus for enhanced keyword matches"""
        if not caption_keywords or not candidate_keywords:
            return 0.0
        
        # Calculate intersection
        intersection = set(caption_keywords) & set(candidate_keywords)
        if intersection:
            # Bonus proportional to intersection size and keyword specificity
            base_bonus = ENHANCED_KEYWORD_BONUS * (len(intersection) / max(len(caption_keywords), len(candidate_keywords)))
            
            # Additional bonus for specific, descriptive keywords
            specific_keywords = [kw for kw in intersection if len(kw) > 4]
            specificity_bonus = 0.1 * len(specific_keywords)
            
            return base_bonus + specificity_bonus
        
        return 0.0
    
    def _calculate_keyword_overlap(self, caption: str, candidate_text: str) -> float:
        """Calculate keyword overlap between caption and candidate text"""
        if not caption or not candidate_text:
            return 0.0
        
        # Extract meaningful words (length > 3, not common stop words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        caption_words = set(word.lower() for word in re.findall(r'\b\w+\b', caption) 
                           if len(word) > 3 and word.lower() not in stop_words)
        candidate_words = set(word.lower() for word in re.findall(r'\b\w+\b', candidate_text) 
                             if len(word) > 3 and word.lower() not in stop_words)
        
        if not caption_words or not candidate_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = caption_words & candidate_words
        union = caption_words | candidate_words
        
        return len(intersection) / len(union) if union else 0.0
    
    def rank_candidates(self, caption: str, candidates: List[Dict[str, Any]], 
                       provider: str, site_id: str) -> List[Dict[str, Any]]:
        """Rank candidates using enhanced scoring"""
        
        # Calculate enhanced scores for all candidates
        for candidate in candidates:
            candidate["enhanced_score"] = self.calculate_enhanced_score(
                caption, candidate, provider, site_id
            )
        
        # Sort by enhanced score
        ranked_candidates = sorted(candidates, key=lambda x: x["enhanced_score"], reverse=True)
        
        return ranked_candidates
    
    def calculate_confidence_metrics(self, top_candidates: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence metrics for top candidates"""
        if not top_candidates:
            return {"confidence": 0.0, "margin": 0.0, "low_conf": True}
        
        top1_score = top_candidates[0].get("enhanced_score", 0.0)
        top2_score = top_candidates[1].get("enhanced_score", 0.0) if len(top_candidates) > 1 else 0.0
        
        # Confidence is the top1 score
        confidence = top1_score
        
        # Margin is the difference between top1 and top2
        margin = top1_score - top2_score
        
        # Determine if confidence is low
        low_conf = confidence < 0.7 or margin < 0.08
        
        return {
            "confidence": confidence,
            "margin": margin,
            "low_conf": low_conf,
            "top1_score": top1_score,
            "top2_score": top2_score
        }

def create_enhanced_rag_scorer() -> EnhancedRAGScoring:
    """Factory function to create enhanced RAG scorer"""
    return EnhancedRAGScoring()

if __name__ == "__main__":
    # Test the enhanced RAG scoring
    scorer = create_enhanced_rag_scorer()
    
    # Test feature extraction
    test_text = "I see a bright orange 3D printer with blue LED lights on the left side"
    features = scorer.extract_enhanced_features(test_text)
    print("🧪 Testing Enhanced RAG Scoring")
    print("=" * 40)
    print(f"Test text: {test_text}")
    print(f"Extracted features: {features}")
    
    # Test scoring
    test_candidates = [
        {
            "id": "test1",
            "score": 0.6,
            "score_nl": 0.7,
            "score_struct": 0.5,
            "nl_text": "bright orange 3D printer with blue lights",
            "struct_text": "3D printer, orange, blue LED",
            "bonus_bearing": 0.1
        },
        {
            "id": "test2", 
            "score": 0.4,
            "score_nl": 0.5,
            "score_struct": 0.3,
            "nl_text": "generic printer",
            "struct_text": "printer",
            "bonus_bearing": 0.0
        }
    ]
    
    ranked = scorer.rank_candidates("bright orange 3D printer", test_candidates, "ft", "SCENE_A_MS")
    metrics = scorer.calculate_confidence_metrics(ranked)
    
    print(f"\nRanked candidates:")
    for i, candidate in enumerate(ranked):
        print(f"  {i+1}. {candidate['id']}: {candidate['enhanced_score']:.3f}")
    
    print(f"\nConfidence metrics: {metrics}")
