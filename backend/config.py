"""
Configuration for dual-channel retrieval system
"""

import os
from typing import Dict, Any

# Load environment variables
def get_env_var(key: str, default: str = "") -> str:
    return os.getenv(key, default)

# Dual-channel retrieval parameters - optimized for better performance
RANK_ALPHA = float(get_env_var("RANK_ALPHA", "0.8"))
RANK_BETA = float(get_env_var("RANK_BETA", "0.10"))
RANK_GAMMA = float(get_env_var("RANK_GAMMA", "0.08"))
CONFIDENCE_THRESHOLD = float(get_env_var("CONFIDENCE_THRESHOLD", "0.05"))

# Provider-specific alpha values - optimized for better textmap matching
RANK_ALPHA_4O = float(get_env_var("RANK_ALPHA_4O", "0.3"))  # For base/4o models
RANK_ALPHA_FT = float(get_env_var("RANK_ALPHA_FT", "0.8"))  # For finetuned models

def get_alpha_for_provider(provider: str) -> float:
    """Get alpha value based on provider type"""
    if provider in ["base", "4o"]:
        return RANK_ALPHA_4O
    elif provider in ["ft", "finetuned"]:
        return RANK_ALPHA_FT
    else:
        return RANK_ALPHA

# Configuration validation
def validate_config() -> Dict[str, Any]:
    """Validate configuration and return status"""
    issues = []
    
    if not (0.0 <= RANK_ALPHA <= 1.0):
        issues.append(f"RANK_ALPHA must be between 0.0 and 1.0, got {RANK_ALPHA}")
    
    if not (0.0 <= RANK_BETA <= 1.0):
        issues.append(f"RANK_BETA must be between 0.0 and 1.0, got {RANK_BETA}")
    
    if not (0.0 <= RANK_GAMMA <= 1.0):
        issues.append(f"RANK_GAMMA must be between 0.0 and 1.0, got {RANK_GAMMA}")
    
    if not (0.0 <= CONFIDENCE_THRESHOLD <= 1.0):
        issues.append(f"CONFIDENCE_THRESHOLD must be between 0.0 and 1.0, got {CONFIDENCE_THRESHOLD}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "config": {
            "RANK_ALPHA": RANK_ALPHA,
            "RANK_BETA": RANK_BETA,
            "RANK_GAMMA": RANK_GAMMA,
            "CONFIDENCE_THRESHOLD": CONFIDENCE_THRESHOLD,
            "RANK_ALPHA_4O": RANK_ALPHA_4O,
            "RANK_ALPHA_FT": RANK_ALPHA_FT
        }
    }

# Print configuration on import
if __name__ == "__main__":
    status = validate_config()
    print("Dual-Channel Retrieval Configuration:")
    print(f"  Valid: {status['valid']}")
    if not status['valid']:
        print("  Issues:")
        for issue in status['issues']:
            print(f"    - {issue}")
    print("  Current values:")
    for key, value in status['config'].items():
        print(f"    {key}: {value}")
else:
    # Validate on import
    status = validate_config()
    if not status['valid']:
        print("⚠ Configuration validation failed:")
        for issue in status['issues']:
            print(f"  - {issue}")
        print("⚠ Using default values")
