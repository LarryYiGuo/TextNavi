#!/usr/bin/env python3
"""
Comprehensive VLN4VI Metrics Evaluation
Calculates localization success rate, end-to-end latency, and low-confidence trigger rate
"""

import csv
import json
import sys
import statistics as stats
from collections import Counter, defaultdict
from pathlib import Path

def load_locate_log(loc_file: str):
    """Load and parse locate log CSV"""
    rows = []
    try:
        with open(loc_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        print(f"✅ Loaded {len(rows)} rows from {loc_file}")
    except FileNotFoundError:
        print(f"❌ Locate log file not found: {loc_file}")
        return []
    except Exception as e:
        print(f"❌ Error reading locate log: {e}")
        return []
    
    return rows

def load_latency_log(e2e_file: str):
    """Load and parse latency log CSV"""
    lat = []
    try:
        with open(e2e_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat.append(int(row["e2e_latency_ms"]))
                except (ValueError, KeyError):
                    pass
        print(f"✅ Loaded {len(lat)} latency records from {e2e_file}")
    except FileNotFoundError:
        print(f"⚠️  Latency log file not found: {e2e_file}")
        return []
    except Exception as e:
        print(f"❌ Error reading latency log: {e}")
        return []
    
    return lat

def calculate_localization_metrics(rows):
    """Calculate Top-1, Top-2, and ±1-Hop accuracy"""
    print("\n" + "="*60)
    print("🎯 LOCALIZATION SUCCESS RATE")
    print("="*60)
    
    # Filter labeled samples
    labeled_rows = [row for row in rows if row.get("gt_node_id") and row["gt_node_id"].strip()]
    
    if not labeled_rows:
        print("❌ No labeled samples found (gt_node_id empty)")
        print("💡 To get accuracy metrics, include gt_node_id when calling /api/locate")
        return
    
    total_labeled = len(labeled_rows)
    print(f"📊 Total labeled samples: {total_labeled}")
    
    # Calculate hit counts
    hit_top1 = 0
    hit_top2 = 0
    hit_hop1 = 0
    
    for row in labeled_rows:
        if row.get("hit_top1", "").lower() in ("true", "1", "yes"):
            hit_top1 += 1
        if row.get("hit_top2", "").lower() in ("true", "1", "yes"):
            hit_top2 += 1
        if row.get("hit_hop1", "").lower() in ("true", "1", "yes"):
            hit_hop1 += 1
    
    # Calculate accuracies
    top1_acc = (hit_top1 / total_labeled) * 100
    top2_acc = (hit_top2 / total_labeled) * 100
    hop1_acc = (hit_hop1 / total_labeled) * 100
    
    print(f"\n🎯 Top-1 Accuracy: {hit_top1}/{total_labeled} = {top1_acc:.2f}%")
    print(f"🎯 Top-2 Accuracy: {hit_top2}/{total_labeled} = {top2_acc:.2f}%")
    print(f"🎯 ±1-Hop Accuracy: {hit_hop1}/{total_labeled} = {hop1_acc:.2f}%")
    
    # Detailed breakdown
    print(f"\n📋 Detailed Breakdown:")
    print(f"  • Correct Top-1 predictions: {hit_top1}")
    print(f"  • Correct Top-2 predictions: {hit_top2}")
    print(f"  • Within ±1-Hop: {hit_hop1}")
    print(f"  • Total errors: {total_labeled - hit_top1}")
    
    return {
        "total_labeled": total_labeled,
        "hit_top1": hit_top1,
        "hit_top2": hit_top2,
        "hit_hop1": hit_hop1,
        "top1_acc": top1_acc,
        "top2_acc": top2_acc,
        "hop1_acc": hop1_acc
    }

def calculate_low_confidence_rate(rows):
    """Calculate low-confidence trigger rate"""
    print("\n" + "="*60)
    print("⚠️  LOW-CONFIDENCE TRIGGER RATE")
    print("="*60)
    
    total_requests = len(rows)
    low_conf_count = 0
    
    # Count low-confidence requests
    for row in rows:
        if row.get("low_conf", "").lower() in ("true", "1", "yes"):
            low_conf_count += 1
    
    low_conf_rate = (low_conf_count / total_requests) * 100 if total_requests > 0 else 0
    
    print(f"📊 Total requests: {total_requests}")
    print(f"⚠️  Low-confidence requests: {low_conf_count}")
    print(f"📈 Low-confidence trigger rate: {low_conf_count}/{total_requests} = {low_conf_rate:.2f}%")
    
    # Analyze low-confidence reasons
    low_conf_reasons = Counter()
    for row in rows:
        if row.get("low_conf", "").lower() in ("true", "1", "yes"):
            reason = row.get("low_conf_rule", "unknown")
            low_conf_reasons[reason] += 1
    
    if low_conf_reasons:
        print(f"\n🔍 Low-confidence breakdown:")
        for reason, count in low_conf_reasons.most_common():
            percentage = (count / low_conf_count) * 100
            print(f"  • {reason}: {count} ({percentage:.1f}%)")
    
    return {
        "total_requests": total_requests,
        "low_conf_count": low_conf_count,
        "low_conf_rate": low_conf_rate,
        "low_conf_reasons": dict(low_conf_reasons)
    }

def calculate_e2e_latency(lat):
    """Calculate end-to-end latency statistics"""
    print("\n" + "="*60)
    print("⏱️  END-TO-END LATENCY")
    print("="*60)
    
    if not lat:
        print("❌ No latency data available")
        return
    
    # Calculate statistics
    mean_lat = stats.mean(lat)
    median_lat = stats.median(lat)
    min_lat = min(lat)
    max_lat = max(lat)
    
    # Calculate percentiles
    try:
        p90 = stats.quantiles(lat, n=10)[8]
        p95 = stats.quantiles(lat, n=20)[18]
    except:
        p90 = p95 = "N/A"
    
    print(f"📊 Sample count: {len(lat)}")
    print(f"⏱️  Mean latency: {mean_lat:.1f} ms")
    print(f"⏱️  Median (P50): {median_lat:.1f} ms")
    print(f"⏱️  P90 latency: {p90:.1f} ms" if p90 != "N/A" else "⏱️  P90 latency: N/A")
    print(f"⏱️  P95 latency: {p95:.1f} ms" if p95 != "N/A" else "⏱️  P95 latency: N/A")
    print(f"⏱️  Min latency: {min_lat} ms")
    print(f"⏱️  Max latency: {max_lat} ms")
    
    # Latency distribution
    latency_ranges = {
        "0-500ms": 0,
        "500ms-1s": 0,
        "1s-2s": 0,
        "2s-5s": 0,
        "5s+": 0
    }
    
    for l in lat:
        if l < 500:
            latency_ranges["0-500ms"] += 1
        elif l < 1000:
            latency_ranges["500ms-1s"] += 1
        elif l < 2000:
            latency_ranges["1s-2s"] += 1
        elif l < 5000:
            latency_ranges["2s-5s"] += 1
        else:
            latency_ranges["5s+"] += 1
    
    print(f"\n📈 Latency distribution:")
    for range_name, count in latency_ranges.items():
        if count > 0:
            percentage = (count / len(lat)) * 100
            print(f"  • {range_name}: {count} ({percentage:.1f}%)")
    
    return {
        "count": len(lat),
        "mean": mean_lat,
        "median": median_lat,
        "p90": p90,
        "p95": p95,
        "min": min_lat,
        "max": max_lat,
        "distribution": latency_ranges
    }

def analyze_by_session(rows):
    """Analyze metrics by session ID"""
    print("\n" + "="*60)
    print("📊 ANALYSIS BY SESSION")
    print("="*60)
    
    sessions = defaultdict(list)
    for row in rows:
        session_id = row.get("session_id", "unknown")
        sessions[session_id].append(row)
    
    if len(sessions) <= 1:
        print("📝 Only one session found, skipping session analysis")
        return
    
    print(f"📊 Found {len(sessions)} sessions:")
    
    for session_id, session_rows in sessions.items():
        print(f"\n🔬 Session: {session_id}")
        print(f"   Total requests: {len(session_rows)}")
        
        # Count labeled samples for this session
        labeled_count = sum(1 for row in session_rows if row.get("gt_node_id") and row["gt_node_id"].strip())
        if labeled_count > 0:
            hit_top1 = sum(1 for row in session_rows if row.get("hit_top1", "").lower() in ("true", "1", "yes"))
            top1_acc = (hit_top1 / labeled_count) * 100
            print(f"   Labeled samples: {labeled_count}")
            print(f"   Top-1 accuracy: {hit_top1}/{labeled_count} = {top1_acc:.2f}%")
        
        # Count low-confidence requests
        low_conf_count = sum(1 for row in session_rows if row.get("low_conf", "").lower() in ("true", "1", "yes"))
        low_conf_rate = (low_conf_count / len(session_rows)) * 100
        print(f"   Low-confidence rate: {low_conf_count}/{len(session_rows)} = {low_conf_rate:.2f}%")

def generate_summary_report(loc_metrics, low_conf_metrics, latency_metrics):
    """Generate a summary report"""
    print("\n" + "="*60)
    print("📋 SUMMARY REPORT")
    print("="*60)
    
    print("🎯 Localization Performance:")
    if loc_metrics:
        print(f"  • Top-1 Accuracy: {loc_metrics['top1_acc']:.2f}%")
        print(f"  • Top-2 Accuracy: {loc_metrics['top2_acc']:.2f}%")
        print(f"  • ±1-Hop Accuracy: {loc_metrics['hop1_acc']:.2f}%")
    
    print("\n⚠️  Confidence Management:")
    if low_conf_metrics:
        print(f"  • Low-confidence trigger rate: {low_conf_metrics['low_conf_rate']:.2f}%")
        print(f"  • Total requests: {low_conf_metrics['total_requests']}")
    
    print("\n⏱️  System Performance:")
    if latency_metrics:
        print(f"  • Average latency: {latency_metrics['mean']:.1f} ms")
        print(f"  • P90 latency: {latency_metrics['p90']:.1f} ms" if latency_metrics['p90'] != "N/A" else "  • P90 latency: N/A")
        print(f"  • Sample count: {latency_metrics['count']}")
    
    # Performance assessment
    print("\n🏆 Performance Assessment:")
    if loc_metrics and loc_metrics['top1_acc'] >= 80:
        print("  ✅ Excellent localization accuracy")
    elif loc_metrics and loc_metrics['top1_acc'] >= 60:
        print("  🟡 Good localization accuracy")
    else:
        print("  🔴 Needs improvement in localization accuracy")
    
    if latency_metrics and latency_metrics['mean'] < 1000:
        print("  ✅ Fast response time")
    elif latency_metrics and latency_metrics['mean'] < 3000:
        print("  🟡 Acceptable response time")
    else:
        print("  🔴 Slow response time, consider optimization")
    
    if low_conf_metrics and low_conf_metrics['low_conf_rate'] < 20:
        print("  ✅ Good confidence management")
    elif low_conf_metrics and low_conf_metrics['low_conf_rate'] < 40:
        print("  🟡 Moderate confidence management")
    else:
        print("  🔴 High low-confidence rate, consider threshold adjustment")

def main():
    """Main evaluation function"""
    print("🔍 VLN4VI Comprehensive Metrics Evaluation")
    print("=" * 60)
    
    # Get file paths from command line or use defaults
    if len(sys.argv) > 1:
        loc_file = sys.argv[1]
    else:
        loc_file = "logs/locate_log.csv"
    
    if len(sys.argv) > 2:
        e2e_file = sys.argv[2]
    else:
        e2e_file = "logs/latency_log.csv"
    
    # Check if files exist
    if not Path(loc_file).exists():
        print(f"❌ Locate log file not found: {loc_file}")
        print("💡 Usage: python tools/metrics_eval.py [locate_log.csv] [latency_log.csv]")
        return
    
    # Load data
    rows = load_locate_log(loc_file)
    lat = load_latency_log(e2e_file)
    
    if not rows:
        print("❌ No data to analyze")
        return
    
    # Calculate metrics
    loc_metrics = calculate_localization_metrics(rows)
    low_conf_metrics = calculate_low_confidence_rate(rows)
    latency_metrics = calculate_e2e_latency(lat)
    
    # Analyze by session
    analyze_by_session(rows)
    
    # Generate summary
    generate_summary_report(loc_metrics, low_conf_metrics, latency_metrics)
    
    print("\n" + "="*60)
    print("✅ Evaluation complete!")
    print("="*60)
    
    # Save results to JSON for further analysis
    results = {
        "localization": loc_metrics,
        "low_confidence": low_conf_metrics,
        "latency": latency_metrics,
        "timestamp": str(Path(loc_file).stat().st_mtime) if Path(loc_file).exists() else None
    }
    
    output_file = "logs/evaluation_results.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

if __name__ == "__main__":
    main()
