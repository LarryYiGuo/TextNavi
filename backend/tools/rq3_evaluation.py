#!/usr/bin/env python3
"""
RQ3 Evaluation Script for VLN4VI
Analyzes trust and error handling metrics:
- Misbelief Rate
- Clarification Rounds & Success
- Error Recovery Time
"""

import csv
import json
import sys
import statistics as stats
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

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

def load_clarification_log(clar_file: str):
    """Load and parse clarification log CSV"""
    rows = []
    try:
        with open(clar_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        print(f"✅ Loaded {len(rows)} rows from {clar_file}")
    except FileNotFoundError:
        print(f"⚠️  Clarification log file not found: {clar_file}")
        return []
    except Exception as e:
        print(f"❌ Error reading clarification log: {e}")
        return []
    
    return rows

def load_recovery_log(recovery_file: str):
    """Load and parse recovery log CSV"""
    rows = []
    try:
        with open(recovery_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        print(f"✅ Loaded {len(rows)} rows from {recovery_file}")
    except FileNotFoundError:
        print(f"⚠️  Recovery log file not found: {recovery_file}")
        return []
    except Exception as e:
        print(f"❌ Error reading recovery log: {e}")
        return []
    
    return rows

def calculate_misbelief_rate(rows):
    """Calculate misbelief rate - users following wrong instructions without clarification"""
    print("\n" + "="*60)
    print("⚠️  MISBELIEF RATE ANALYSIS")
    print("="*60)
    
    # Filter rows with ground truth and misbelief data
    labeled_rows = [row for row in rows if row.get("gt_node_id") and row["gt_node_id"].strip()]
    
    if not labeled_rows:
        print("❌ No labeled samples found (gt_node_id empty)")
        return None
    
    total_labeled = len(labeled_rows)
    misbelief_count = 0
    clarification_triggered_count = 0
    
    for row in labeled_rows:
        # Check if clarification was triggered
        clarification_triggered = row.get("clarification_triggered", "").lower() in ("true", "1", "yes")
        if clarification_triggered:
            clarification_triggered_count += 1
        
        # Check if misbelief occurred
        misbelief = row.get("misbelief", "").lower() in ("true", "1", "yes")
        if misbelief:
            misbelief_count += 1
    
    misbelief_rate = (misbelief_count / total_labeled) * 100 if total_labeled > 0 else 0
    clarification_rate = (clarification_triggered_count / total_labeled) * 100 if total_labeled > 0 else 0
    
    print(f"📊 Total labeled samples: {total_labeled}")
    print(f"⚠️  Misbelief occurrences: {misbelief_count}")
    print(f"🔍 Clarification triggered: {clarification_triggered_count}")
    print(f"📈 Misbelief rate: {misbelief_count}/{total_labeled} = {misbelief_rate:.2f}%")
    print(f"📈 Clarification trigger rate: {clarification_triggered_count}/{total_labeled} = {clarification_rate:.2f}%")
    
    # Analyze misbelief patterns
    if misbelief_count > 0:
        print(f"\n🔍 Misbelief analysis:")
        print(f"  • Users following wrong instructions without clarification: {misbelief_count}")
        print(f"  • Users who triggered clarification: {clarification_triggered_count}")
        print(f"  • Users who followed correct instructions: {total_labeled - misbelief_count - clarification_triggered_count}")
    
    return {
        "total_labeled": total_labeled,
        "misbelief_count": misbelief_count,
        "clarification_triggered_count": clarification_triggered_count,
        "misbelief_rate": misbelief_rate,
        "clarification_rate": clarification_rate
    }

def calculate_clarification_metrics(clar_rows):
    """Calculate clarification rounds and success rate"""
    print("\n" + "="*60)
    print("🔍 CLARIFICATION DIALOGUE ANALYSIS")
    print("="*60)
    
    if not clar_rows:
        print("❌ No clarification data available")
        return None
    
    # Group by clarification_id
    clarification_sessions = defaultdict(list)
    for row in clar_rows:
        clarification_id = row.get("clarification_id", "")
        if clarification_id:
            clarification_sessions[clarification_id].append(row)
    
    if not clarification_sessions:
        print("❌ No clarification sessions found")
        return None
    
    print(f"📊 Total clarification sessions: {len(clarification_sessions)}")
    
    # Analyze each session
    total_rounds_list = []
    successful_sessions = 0
    total_sessions = 0
    
    for session_id, session_rows in clarification_sessions.items():
        # Find session end row
        end_rows = [row for row in session_rows if row.get("total_rounds") and row["total_rounds"].strip()]
        
        if end_rows:
            end_row = end_rows[-1]
            total_rounds = int(end_row.get("total_rounds", 0))
            clarification_success = end_row.get("clarification_success", "").lower() in ("true", "1", "yes")
            
            total_rounds_list.append(total_rounds)
            total_sessions += 1
            
            if clarification_success:
                successful_sessions += 1
            
            print(f"  Session {session_id}: {total_rounds} rounds, Success: {clarification_success}")
    
    if total_sessions > 0:
        avg_rounds = stats.mean(total_rounds_list) if total_rounds_list else 0
        success_rate = (successful_sessions / total_sessions) * 100
        
        print(f"\n📈 Clarification Performance:")
        print(f"  • Average rounds per session: {avg_rounds:.1f}")
        print(f"  • Successful clarifications: {successful_sessions}/{total_sessions} = {success_rate:.2f}%")
        print(f"  • Total rounds across all sessions: {sum(total_rounds_list)}")
        
        # Round distribution
        round_distribution = Counter(total_rounds_list)
        print(f"\n📊 Round distribution:")
        for rounds, count in sorted(round_distribution.items()):
            percentage = (count / total_sessions) * 100
            print(f"  • {rounds} rounds: {count} sessions ({percentage:.1f}%)")
        
        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": success_rate,
            "avg_rounds": avg_rounds,
            "total_rounds": sum(total_rounds_list),
            "round_distribution": dict(round_distribution)
        }
    
    return None

def calculate_error_recovery_metrics(recovery_rows):
    """Calculate error recovery time metrics"""
    print("\n" + "="*60)
    print("⚠️  ERROR RECOVERY TIME ANALYSIS")
    print("="*60)
    
    if not recovery_rows:
        print("❌ No error recovery data available")
        return None
    
    # Filter completed recoveries
    completed_recoveries = [row for row in recovery_rows if row.get("recovery_duration_ms") and row["recovery_duration_ms"].strip()]
    
    if not completed_recoveries:
        print("❌ No completed error recoveries found")
        return None
    
    print(f"📊 Total completed recoveries: {len(completed_recoveries)}")
    
    # Extract recovery durations
    recovery_times = []
    for row in completed_recoveries:
        try:
            duration = int(row["recovery_duration_ms"])
            recovery_times.append(duration)
        except (ValueError, TypeError):
            continue
    
    if not recovery_times:
        print("❌ No valid recovery time data")
        return None
    
    # Calculate statistics
    mean_time = stats.mean(recovery_times)
    median_time = stats.median(recovery_times)
    min_time = min(recovery_times)
    max_time = max(recovery_times)
    
    try:
        p90 = stats.quantiles(recovery_times, n=10)[8]
        p95 = stats.quantiles(recovery_times, n=20)[18]
    except:
        p90 = p95 = "N/A"
    
    print(f"\n⏱️  Recovery Time Statistics:")
    print(f"  • Mean recovery time: {mean_time:.1f} ms ({mean_time/1000:.2f} s)")
    print(f"  • Median recovery time: {median_time:.1f} ms ({median_time/1000:.2f} s)")
    print(f"  • P90 recovery time: {p90:.1f} ms ({p90/1000:.2f} s)" if p90 != "N/A" else "  • P90 recovery time: N/A")
    print(f"  • P95 recovery time: {p95:.1f} ms ({p95/1000:.2f} s)" if p95 != "N/A" else "  • P95 recovery time: N/A")
    print(f"  • Min recovery time: {min_time} ms ({min_time/1000:.2f} s)")
    print(f"  • Max recovery time: {max_time} ms ({max_time/1000:.2f} s)")
    
    # Time distribution
    time_ranges = {
        "0-1s": 0,
        "1-5s": 0,
        "5-10s": 0,
        "10-30s": 0,
        "30s+": 0
    }
    
    for time_ms in recovery_times:
        time_s = time_ms / 1000
        if time_s < 1:
            time_ranges["0-1s"] += 1
        elif time_s < 5:
            time_ranges["1-5s"] += 1
        elif time_s < 10:
            time_ranges["5-10s"] += 1
        elif time_s < 30:
            time_ranges["10-30s"] += 1
        else:
            time_ranges["30s+"] += 1
    
    print(f"\n📈 Recovery time distribution:")
    for range_name, count in time_ranges.items():
        if count > 0:
            percentage = (count / len(recovery_times)) * 100
            print(f"  • {range_name}: {count} recoveries ({percentage:.1f}%)")
    
    return {
        "total_recoveries": len(recovery_times),
        "mean_time": mean_time,
        "median_time": median_time,
        "p90": p90,
        "p95": p95,
        "min_time": min_time,
        "max_time": max_time,
        "time_distribution": time_ranges
    }

def analyze_by_session(rows, clar_rows, recovery_rows):
    """Analyze RQ3 metrics by session"""
    print("\n" + "="*60)
    print("📊 RQ3 ANALYSIS BY SESSION")
    print("="*60)
    
    # Group by session
    sessions = defaultdict(lambda: {"locate": [], "clarification": [], "recovery": []})
    
    for row in rows:
        session_id = row.get("session_id", "unknown")
        sessions[session_id]["locate"].append(row)
    
    for row in clar_rows:
        session_id = row.get("session_id", "unknown")
        sessions[session_id]["clarification"].append(row)
    
    for row in recovery_rows:
        session_id = row.get("session_id", "unknown")
        sessions[session_id]["recovery"].append(row)
    
    if len(sessions) <= 1:
        print("📝 Only one session found, skipping session analysis")
        return
    
    print(f"📊 Found {len(sessions)} sessions:")
    
    for session_id, session_data in sessions.items():
        print(f"\n🔬 Session: {session_id}")
        
        # Locate metrics
        locate_rows = session_data["locate"]
        labeled_count = sum(1 for row in locate_rows if row.get("gt_node_id") and row["gt_node_id"].strip())
        if labeled_count > 0:
            misbelief_count = sum(1 for row in locate_rows if row.get("misbelief", "").lower() in ("true", "1", "yes"))
            misbelief_rate = (misbelief_count / labeled_count) * 100
            print(f"   Labeled samples: {labeled_count}")
            print(f"   Misbelief rate: {misbelief_count}/{labeled_count} = {misbelief_rate:.2f}%")
        
        # Clarification metrics
        clar_sessions = len(set(row.get("clarification_id", "") for row in session_data["clarification"] if row.get("clarification_id")))
        if clar_sessions > 0:
            print(f"   Clarification sessions: {clar_sessions}")
        
        # Recovery metrics
        recovery_count = len(session_data["recovery"])
        if recovery_count > 0:
            print(f"   Error recoveries: {recovery_count}")

def generate_rq3_summary(misbelief_metrics, clarification_metrics, recovery_metrics):
    """Generate RQ3 summary report"""
    print("\n" + "="*60)
    print("📋 RQ3 SUMMARY REPORT")
    print("="*60)
    
    print("⚠️  Trust & Error Handling Performance:")
    
    if misbelief_metrics:
        print(f"  • Misbelief rate: {misbelief_metrics['misbelief_rate']:.2f}%")
        print(f"  • Clarification trigger rate: {misbelief_metrics['clarification_rate']:.2f}%")
    
    if clarification_metrics:
        print(f"  • Clarification success rate: {clarification_metrics['success_rate']:.2f}%")
        print(f"  • Average clarification rounds: {clarification_metrics['avg_rounds']:.1f}")
    
    if recovery_metrics:
        print(f"  • Average error recovery time: {recovery_metrics['mean_time']/1000:.2f} seconds")
        print(f"  • Total error recoveries: {recovery_metrics['total_recoveries']}")
    
    # Performance assessment
    print("\n🏆 RQ3 Performance Assessment:")
    
    if misbelief_metrics:
        if misbelief_metrics['misbelief_rate'] < 10:
            print("  ✅ Excellent trust management (low misbelief rate)")
        elif misbelief_metrics['misbelief_rate'] < 25:
            print("  🟡 Good trust management (moderate misbelief rate)")
        else:
            print("  🔴 Needs improvement in trust management (high misbelief rate)")
    
    if clarification_metrics:
        if clarification_metrics['success_rate'] >= 80:
            print("  ✅ Excellent clarification effectiveness")
        elif clarification_metrics['success_rate'] >= 60:
            print("  🟡 Good clarification effectiveness")
        else:
            print("  🔴 Needs improvement in clarification effectiveness")
    
    if recovery_metrics:
        if recovery_metrics['mean_time'] < 5000:  # 5 seconds
            print("  ✅ Fast error recovery")
        elif recovery_metrics['mean_time'] < 15000:  # 15 seconds
            print("  🟡 Acceptable error recovery time")
        else:
            print("  🔴 Slow error recovery, consider optimization")

def main():
    """Main RQ3 evaluation function"""
    print("🔍 VLN4VI RQ3 Evaluation - Trust & Error Handling")
    print("=" * 60)
    
    # Get file paths from command line or use defaults
    if len(sys.argv) > 1:
        loc_file = sys.argv[1]
    else:
        loc_file = "logs/locate_log.csv"
    
    if len(sys.argv) > 2:
        clar_file = sys.argv[2]
    else:
        clar_file = "logs/clarification_log.csv"
    
    if len(sys.argv) > 3:
        recovery_file = sys.argv[3]
    else:
        recovery_file = "logs/recovery_log.csv"
    
    # Check if main log file exists
    if not Path(loc_file).exists():
        print(f"❌ Locate log file not found: {loc_file}")
        print("💡 Usage: python tools/rq3_evaluation.py [locate_log.csv] [clarification_log.csv] [recovery_log.csv]")
        return
    
    # Load data
    rows = load_locate_log(loc_file)
    clar_rows = load_clarification_log(clar_file)
    recovery_rows = load_recovery_log(recovery_file)
    
    if not rows:
        print("❌ No data to analyze")
        return
    
    # Calculate RQ3 metrics
    misbelief_metrics = calculate_misbelief_rate(rows)
    clarification_metrics = calculate_clarification_metrics(clar_rows)
    recovery_metrics = calculate_error_recovery_metrics(recovery_rows)
    
    # Analyze by session
    analyze_by_session(rows, clar_rows, recovery_rows)
    
    # Generate summary
    generate_rq3_summary(misbelief_metrics, clarification_metrics, recovery_metrics)
    
    print("\n" + "="*60)
    print("✅ RQ3 Evaluation complete!")
    print("="*60)
    
    # Save results to JSON for further analysis
    results = {
        "misbelief": misbelief_metrics,
        "clarification": clarification_metrics,
        "recovery": recovery_metrics,
        "timestamp": str(Path(loc_file).stat().st_mtime) if Path(loc_file).exists() else None
    }
    
    output_file = "logs/rq3_evaluation_results.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 RQ3 results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save RQ3 results: {e}")

if __name__ == "__main__":
    main()
