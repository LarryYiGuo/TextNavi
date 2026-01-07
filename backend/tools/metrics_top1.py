#!/usr/bin/env python3
"""
Top-1 accuracy statistics for VLN localization
Reads locate_log.csv and calculates accuracy metrics
"""

import csv
import sys
import os
from pathlib import Path

def calculate_top1_accuracy(log_path: str):
    """Calculate Top-1 accuracy from locate log CSV"""
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        return
    
    print(f"📊 Analyzing Top-1 accuracy from: {log_path}")
    print("=" * 60)
    
    try:
        with open(log_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Collect statistics
            stats = {
                "total_labeled": 0,
                "correct_predictions": 0,
                "incorrect_predictions": 0,
                "by_provider": {},
                "by_site": {},
                "confidence_ranges": {
                    "high": {"count": 0, "correct": 0},      # > 0.7
                    "medium": {"count": 0, "correct": 0},    # 0.4-0.7
                    "low": {"count": 0, "correct": 0}        # < 0.4
                },
                "margin_ranges": {
                    "large": {"count": 0, "correct": 0},     # > 0.15
                    "medium": {"count": 0, "correct": 0},    # 0.07-0.15
                    "small": {"count": 0, "correct": 0}      # < 0.07
                }
            }
            
            for row_num, row in enumerate(reader, 1):
                # Skip rows without ground truth
                if not row.get("gt_node_id") or row["gt_node_id"].strip() == "":
                    continue
                
                stats["total_labeled"] += 1
                
                # Check if prediction was correct
                is_correct = row.get("correct", "").lower() in ("true", "1", "yes")
                if is_correct:
                    stats["correct_predictions"] += 1
                else:
                    stats["incorrect_predictions"] += 1
                
                # Statistics by provider
                provider = row.get("provider", "unknown")
                if provider not in stats["by_provider"]:
                    stats["by_provider"][provider] = {"total": 0, "correct": 0}
                stats["by_provider"][provider]["total"] += 1
                if is_correct:
                    stats["by_provider"][provider]["correct"] += 1
                
                # Statistics by site
                site = row.get("site_id", "unknown")
                if site not in stats["by_site"]:
                    stats["by_site"][site] = {"total": 0, "correct": 0}
                stats["by_site"][site]["total"] += 1
                if is_correct:
                    stats["by_site"][site]["correct"] += 1
                
                # Statistics by confidence level
                try:
                    confidence = float(row.get("top1_score", 0))
                    if confidence > 0.7:
                        stats["confidence_ranges"]["high"]["count"] += 1
                        if is_correct:
                            stats["confidence_ranges"]["high"]["correct"] += 1
                    elif confidence > 0.4:
                        stats["confidence_ranges"]["medium"]["count"] += 1
                        if is_correct:
                            stats["confidence_ranges"]["medium"]["correct"] += 1
                    else:
                        stats["confidence_ranges"]["low"]["count"] += 1
                        if is_correct:
                            stats["confidence_ranges"]["low"]["correct"] += 1
                except (ValueError, TypeError):
                    pass
                
                # Statistics by margin
                try:
                    margin = float(row.get("margin", 0))
                    if margin > 0.15:
                        stats["margin_ranges"]["large"]["count"] += 1
                        if is_correct:
                            stats["margin_ranges"]["large"]["correct"] += 1
                    elif margin > 0.07:
                        stats["margin_ranges"]["medium"]["count"] += 1
                        if is_correct:
                            stats["margin_ranges"]["medium"]["correct"] += 1
                    else:
                        stats["margin_ranges"]["small"]["count"] += 1
                        if is_correct:
                            stats["margin_ranges"]["small"]["correct"] += 1
                except (ValueError, TypeError):
                    pass
            
            # Print results
            if stats["total_labeled"] == 0:
                print("❌ No labeled rows found (gt_node_id empty)")
                print("💡 To get accuracy metrics, include gt_node_id when calling /api/locate")
                return
            
            # Overall accuracy
            accuracy = stats["correct_predictions"] / stats["total_labeled"] * 100
            print(f"🎯 Overall Top-1 Accuracy: {stats['correct_predictions']}/{stats['total_labeled']} = {accuracy:.2f}%")
            print()
            
            # By provider
            print("📊 By Provider:")
            for provider, data in stats["by_provider"].items():
                if data["total"] > 0:
                    provider_acc = data["correct"] / data["total"] * 100
                    print(f"  {provider}: {data['correct']}/{data['total']} = {provider_acc:.2f}%")
            print()
            
            # By site
            print("🏢 By Site:")
            for site, data in stats["by_site"].items():
                if data["total"] > 0:
                    site_acc = data["correct"] / data["total"] * 100
                    print(f"  {site}: {data['correct']}/{data['total']} = {site_acc:.2f}%")
            print()
            
            # By confidence level
            print("💪 By Confidence Level:")
            for level, data in stats["confidence_ranges"].items():
                if data["count"] > 0:
                    level_acc = data["correct"] / data["count"] * 100
                    print(f"  {level.capitalize()} (>0.7): {data['correct']}/{data['count']} = {level_acc:.2f}%")
            print()
            
            # By margin
            print("📏 By Margin (Top1 - Second):")
            for level, data in stats["margin_ranges"].items():
                if data["count"] > 0:
                    level_acc = data["correct"] / data["count"] * 100
                    if level == "large":
                        print(f"  Large (>0.15): {data['correct']}/{data['count']} = {level_acc:.2f}%")
                    elif level == "medium":
                        print(f"  Medium (0.07-0.15): {data['correct']}/{data['count']} = {level_acc:.2f}%")
                    else:
                        print(f"  Small (<0.07): {data['correct']}/{data['count']} = {level_acc:.2f}%")
            print()
            
            # Sample analysis
            print("🔍 Sample Analysis:")
            print(f"  Total labeled samples: {stats['total_labeled']}")
            print(f"  Correct predictions: {stats['correct_predictions']}")
            print(f"  Incorrect predictions: {stats['incorrect_predictions']}")
            
            if stats["incorrect_predictions"] > 0:
                error_rate = stats["incorrect_predictions"] / stats["total_labeled"] * 100
                print(f"  Error rate: {error_rate:.2f}%")
                
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

def main():
    """Main function"""
    # Default log path
    default_log = "logs/locate_log.csv"
    
    # Get log path from command line or use default
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    else:
        log_path = default_log
    
    # Check if log file exists
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        print(f"💡 Default location: {default_log}")
        print("💡 Usage: python tools/metrics_top1.py [path/to/locate_log.csv]")
        return
    
    # Calculate and display metrics
    calculate_top1_accuracy(log_path)

if __name__ == "__main__":
    main()
