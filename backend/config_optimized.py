#!/usr/bin/env python3
"""Optimized configuration for improved confidence and success rate"""

import os
from typing import Dict, Any

def get_env_var(key: str, default: str) -> str:
    """Get environment variable with fallback"""
    return os.getenv(key, default)

# 🔧 OPTIMIZED: RAG Fusion Scoring Parameters for 70%+ confidence
# Enhanced weights for better discrimination between scenes

# Base model weights (4o models)
RANK_ALPHA_4O = float(get_env_var("RANK_ALPHA_4O", "0.4"))      # Increased from 0.3
RANK_BETA_4O = float(get_env_var("RANK_BETA_4O", "0.15"))       # Increased from 0.10
RANK_GAMMA_4O = float(get_env_var("RANK_GAMMA_4O", "0.12"))     # Increased from 0.08

# Finetuned model weights
RANK_ALPHA_FT = float(get_env_var("RANK_ALPHA_FT", "0.85"))     # Increased from 0.8
RANK_BETA_FT = float(get_env_var("RANK_BETA_FT", "0.20"))       # Increased from 0.10
RANK_GAMMA_FT = float(get_env_var("RANK_GAMMA_FT", "0.15"))     # Increased from 0.08

# Legacy support
RANK_ALPHA = float(get_env_var("RANK_ALPHA", "0.85"))
RANK_BETA = float(get_env_var("RANK_BETA", "0.20"))
RANK_GAMMA = float(get_env_var("RANK_GAMMA", "0.15"))

# 🔧 OPTIMIZED: Low Confidence Thresholds for better accuracy
LOWCONF_SCORE_TH = float(get_env_var("LOWCONF_SCORE_TH", "0.45"))      # Increased from 0.30
LOWCONF_MARGIN_TH = float(get_env_var("LOWCONF_MARGIN_TH", "0.08"))   # Increased from 0.05

# 🔧 NEW: Enhanced scoring parameters
ENHANCED_KEYWORD_BONUS = float(get_env_var("ENHANCED_KEYWORD_BONUS", "0.25"))  # Bonus for enhanced keywords
COLOR_BONUS = float(get_env_var("COLOR_BONUS", "0.20"))                        # Bonus for color matches
SHAPE_BONUS = float(get_env_var("SHAPE_BONUS", "0.18"))                        # Bonus for shape matches
POSITION_BONUS = float(get_env_var("POSITION_BONUS", "0.15"))                  # Bonus for position matches
QUANTITY_BONUS = float(get_env_var("QUANTITY_BONUS", "0.12"))                 # Bonus for quantity matches

# 🔧 NEW: Scene-specific thresholds
SCENE_A_MS_THRESHOLD = float(get_env_var("SCENE_A_MS_THRESHOLD", "0.70"))
SCENE_B_STUDIO_THRESHOLD = float(get_env_var("SCENE_B_STUDIO_THRESHOLD", "0.75"))

# 🔧 NEW: Enhanced retrieval parameters
ENHANCED_RETRIEVAL_TOP_K = int(get_env_var("ENHANCED_RETRIEVAL_TOP_K", "20"))  # Increased from 15
ENHANCED_RETRIEVAL_MIN_SCORE = float(get_env_var("ENHANCED_RETRIEVAL_MIN_SCORE", "0.35"))

# 🔧 NEW: BM25 + Embedding fusion weights
BM25_WEIGHT = float(get_env_var("BM25_WEIGHT", "0.60"))           # BM25 weight
EMBEDDING_WEIGHT = float(get_env_var("EMBEDDING_WEIGHT", "0.40")) # Embedding weight

# 🔧 NEW: Semantic similarity thresholds
SEMANTIC_SIMILARITY_THRESHOLD = float(get_env_var("SEMANTIC_SIMILARITY_THRESHOLD", "0.65"))
KEYWORD_OVERLAP_THRESHOLD = float(get_env_var("KEYWORD_OVERLAP_THRESHOLD", "0.30"))

def get_rank_alpha(provider: str = "ft") -> float:
    """Get rank alpha based on provider"""
    if provider.lower() == "base" or provider.lower() == "4o":
        return RANK_ALPHA_4O
    elif provider.lower() == "ft":
        return RANK_ALPHA_FT
    else:
        return RANK_ALPHA

def get_rank_beta(provider: str = "ft") -> float:
    """Get rank beta based on provider"""
    if provider.lower() == "base" or provider.lower() == "4o":
        return RANK_BETA_4O
    elif provider.lower() == "ft":
        return RANK_BETA_FT
    else:
        return RANK_BETA

def get_rank_gamma(provider: str = "ft") -> float:
    """Get rank gamma based on provider"""
    if provider.lower() == "base" or provider.lower() == "4o":
        return RANK_GAMMA_4O
    elif provider.lower() == "ft":
        return RANK_GAMMA_FT
    else:
        return RANK_GAMMA

def get_scene_threshold(site_id: str) -> float:
    """Get scene-specific confidence threshold"""
    if site_id == "SCENE_A_MS":
        return SCENE_A_MS_THRESHOLD
    elif site_id == "SCENE_B_STUDIO":
        return SCENE_B_STUDIO_THRESHOLD
    else:
        return 0.70  # Default threshold

def validate_config() -> list:
    """Validate configuration parameters"""
    issues = []
    
    # Validate rank parameters
    if not (0.0 <= RANK_ALPHA_4O <= 1.0):
        issues.append(f"RANK_ALPHA_4O must be between 0.0 and 1.0, got {RANK_ALPHA_4O}")
    if not (0.0 <= RANK_ALPHA_FT <= 1.0):
        issues.append(f"RANK_ALPHA_FT must be between 0.0 and 1.0, got {RANK_ALPHA_FT}")
    if not (0.0 <= RANK_BETA <= 1.0):
        issues.append(f"RANK_BETA must be between 0.0 and 1.0, got {RANK_BETA}")
    if not (0.0 <= RANK_GAMMA <= 1.0):
        issues.append(f"RANK_GAMMA must be between 0.0 and 1.0, got {RANK_GAMMA}")
    
    # Validate thresholds
    if not (0.0 <= LOWCONF_SCORE_TH <= 1.0):
        issues.append(f"LOWCONF_SCORE_TH must be between 0.0 and 1.0, got {LOWCONF_SCORE_TH}")
    if not (0.0 <= LOWCONF_MARGIN_TH <= 1.0):
        issues.append(f"LOWCONF_MARGIN_TH must be between 0.0 and 1.0, got {LOWCONF_MARGIN_TH}")
    
    # Validate bonus parameters
    if not (0.0 <= ENHANCED_KEYWORD_BONUS <= 1.0):
        issues.append(f"ENHANCED_KEYWORD_BONUS must be between 0.0 and 1.0, got {ENHANCED_KEYWORD_BONUS}")
    if not (0.0 <= COLOR_BONUS <= 1.0):
        issues.append(f"COLOR_BONUS must be between 0.0 and 1.0, got {COLOR_BONUS}")
    
    return issues

def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    return {
        "RANK_ALPHA_4O": RANK_ALPHA_4O,
        "RANK_ALPHA_FT": RANK_ALPHA_FT,
        "RANK_BETA": RANK_BETA,
        "RANK_GAMMA": RANK_GAMMA,
        "LOWCONF_SCORE_TH": LOWCONF_SCORE_TH,
        "LOWCONF_MARGIN_TH": LOWCONF_MARGIN_TH,
        "ENHANCED_KEYWORD_BONUS": ENHANCED_KEYWORD_BONUS,
        "COLOR_BONUS": COLOR_BONUS,
        "SHAPE_BONUS": SHAPE_BONUS,
        "POSITION_BONUS": POSITION_BONUS,
        "QUANTITY_BONUS": QUANTITY_BONUS,
        "SCENE_A_MS_THRESHOLD": SCENE_A_MS_THRESHOLD,
        "SCENE_B_STUDIO_THRESHOLD": SCENE_B_STUDIO_THRESHOLD,
        "BM25_WEIGHT": BM25_WEIGHT,
        "EMBEDDING_WEIGHT": EMBEDDING_WEIGHT,
        "SEMANTIC_SIMILARITY_THRESHOLD": SEMANTIC_SIMILARITY_THRESHOLD,
        "KEYWORD_OVERLAP_THRESHOLD": KEYWORD_OVERLAP_THRESHOLD
    }

if __name__ == "__main__":
    # Validate configuration
    issues = validate_config()
    if issues:
        print("❌ Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration validation passed")
        print("\n📊 Configuration Summary:")
        summary = get_config_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
