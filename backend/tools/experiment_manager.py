#!/usr/bin/env python3
"""
Experiment Manager for VLN4VI
Helps organize and track experiments with confidence metrics
"""

import csv
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ExperimentManager:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "locate_log.csv"
        
        # Initialize log file if it doesn't exist
        if not self.log_file.exists():
            self._init_log_file()
    
    def _init_log_file(self):
        """Initialize the log file with headers"""
        headers = [
            "ts_iso", "session_id", "site_id", "provider",
            "caption", "top1_id", "top1_score", "second_score", "margin",
            "gt_node_id", "correct", "candidates_json"
        ]
        
        with open(self.log_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        print(f"✅ 创建日志文件: {self.log_file}")
    
    def create_experiment_session(self, session_name: str, description: str = "") -> str:
        """Create a new experiment session"""
        session_id = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session info file
        session_file = self.log_dir / f"session_{session_id}.json"
        session_info = {
            "session_id": session_id,
            "name": session_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "parameters": {},
            "notes": []
        }
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 创建实验会话: {session_id}")
        print(f"📁 会话文件: {session_file}")
        return session_id
    
    def add_experiment_note(self, session_id: str, note: str):
        """Add a note to an experiment session"""
        session_file = self.log_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            print(f"❌ 会话不存在: {session_id}")
            return
        
        with open(session_file, "r", encoding="utf-8") as f:
            session_info = json.load(f)
        
        timestamp = datetime.now().isoformat()
        session_info["notes"].append({
            "timestamp": timestamp,
            "note": note
        })
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 添加笔记到会话 {session_id}: {note}")
    
    def update_experiment_parameters(self, session_id: str, parameters: Dict):
        """Update experiment parameters for a session"""
        session_file = self.log_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            print(f"❌ 会话不存在: {session_id}")
            return
        
        with open(session_file, "r", encoding="utf-8") as f:
            session_info = json.load(f)
        
        session_info["parameters"].update(parameters)
        session_info["updated_at"] = datetime.now().isoformat()
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 更新会话 {session_id} 参数: {parameters}")
    
    def list_experiments(self, show_details: bool = False):
        """List all experiment sessions"""
        session_files = list(self.log_dir.glob("session_*.json"))
        
        if not session_files:
            print("📝 暂无实验会话")
            return
        
        print(f"📊 实验会话列表 (共 {len(session_files)} 个):")
        print("=" * 80)
        
        for session_file in sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True):
            with open(session_file, "r", encoding="utf-8") as f:
                session_info = json.load(f)
            
            session_id = session_info["session_id"]
            name = session_info["name"]
            created_at = session_info["created_at"]
            status = session_info["status"]
            
            # Count samples for this session
            sample_count = self._count_session_samples(session_id)
            
            print(f"🔬 {name}")
            print(f"   ID: {session_id}")
            print(f"   创建时间: {created_at}")
            print(f"   状态: {status}")
            print(f"   样本数量: {sample_count}")
            
            if show_details:
                if session_info.get("description"):
                    print(f"   描述: {session_info['description']}")
                if session_info.get("parameters"):
                    print(f"   参数: {json.dumps(session_info['parameters'], ensure_ascii=False, indent=2)}")
                if session_info.get("notes"):
                    print(f"   笔记数量: {len(session_info['notes'])}")
            
            print("-" * 40)
    
    def _count_session_samples(self, session_id: str) -> int:
        """Count the number of samples for a specific session"""
        if not self.log_file.exists():
            return 0
        
        count = 0
        with open(self.log_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("session_id") == session_id:
                    count += 1
        
        return count
    
    def get_experiment_summary(self, session_id: str):
        """Get detailed summary for a specific experiment session"""
        session_file = self.log_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            print(f"❌ 会话不存在: {session_id}")
            return
        
        with open(session_file, "r", encoding="utf-8") as f:
            session_info = json.load(f)
        
        print(f"📊 实验会话详情: {session_info['name']}")
        print("=" * 60)
        print(f"会话 ID: {session_info['session_id']}")
        print(f"创建时间: {session_info['created_at']}")
        print(f"状态: {session_info['status']}")
        
        if session_info.get("description"):
            print(f"描述: {session_info['description']}")
        
        # Get performance metrics
        metrics = self._get_session_metrics(session_id)
        if metrics:
            print(f"\n📈 性能指标:")
            print(f"  总样本数: {metrics['total_samples']}")
            print(f"  有标签样本: {metrics['labeled_samples']}")
            if metrics['labeled_samples'] > 0:
                accuracy = metrics['correct_predictions'] / metrics['labeled_samples'] * 100
                print(f"  Top-1 准确率: {metrics['correct_predictions']}/{metrics['labeled_samples']} = {accuracy:.2f}%")
        
        # Show parameters
        if session_info.get("parameters"):
            print(f"\n⚙️  实验参数:")
            for key, value in session_info["parameters"].items():
                print(f"  {key}: {value}")
        
        # Show recent notes
        if session_info.get("notes"):
            print(f"\n📝 最近笔记:")
            for note in session_info["notes"][-3:]:  # Show last 3 notes
                timestamp = note["timestamp"][:19]  # Truncate to second precision
                print(f"  [{timestamp}] {note['note']}")
    
    def _get_session_metrics(self, session_id: str) -> Optional[Dict]:
        """Get performance metrics for a specific session"""
        if not self.log_file.exists():
            return None
        
        metrics = {
            "total_samples": 0,
            "labeled_samples": 0,
            "correct_predictions": 0
        }
        
        with open(self.log_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("session_id") == session_id:
                    metrics["total_samples"] += 1
                    
                    if row.get("gt_node_id") and row["gt_node_id"].strip():
                        metrics["labeled_samples"] += 1
                        if row.get("correct", "").lower() in ("true", "1", "yes"):
                            metrics["correct_predictions"] += 1
        
        return metrics
    
    def export_experiment_data(self, session_id: str, output_file: str = None):
        """Export experiment data for a specific session"""
        if not output_file:
            output_file = f"experiment_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not self.log_file.exists():
            print(f"❌ 日志文件不存在: {self.log_file}")
            return
        
        # Filter data for the specific session
        exported_rows = []
        with open(self.log_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("session_id") == session_id:
                    exported_rows.append(row)
        
        if not exported_rows:
            print(f"❌ 会话 {session_id} 没有数据")
            return
        
        # Write to output file
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            if exported_rows:
                writer = csv.DictWriter(f, fieldnames=exported_rows[0].keys())
                writer.writeheader()
                writer.writerows(exported_rows)
        
        print(f"✅ 导出会话 {session_id} 数据到: {output_file}")
        print(f"   导出样本数: {len(exported_rows)}")

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(description="VLN4VI 实验管理器")
    parser.add_argument("action", choices=["create", "list", "show", "note", "export", "params"], 
                       help="要执行的操作")
    parser.add_argument("--session", "-s", help="会话 ID")
    parser.add_argument("--name", "-n", help="会话名称")
    parser.add_argument("--description", "-d", help="会话描述")
    parser.add_argument("--note", help="要添加的笔记")
    parser.add_argument("--parameters", "-p", help="参数字典 (JSON 格式)")
    parser.add_argument("--output", "-o", help="导出文件名")
    parser.add_argument("--details", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    manager = ExperimentManager()
    
    if args.action == "create":
        if not args.name:
            print("❌ 创建会话需要指定名称 (--name)")
            return
        session_id = manager.create_experiment_session(args.name, args.description or "")
        print(f"💡 使用以下会话 ID 进行实验: {session_id}")
    
    elif args.action == "list":
        manager.list_experiments(args.details)
    
    elif args.action == "show":
        if not args.session:
            print("❌ 显示会话需要指定会话 ID (--session)")
            return
        manager.get_experiment_summary(args.session)
    
    elif args.action == "note":
        if not args.session or not args.note:
            print("❌ 添加笔记需要指定会话 ID (--session) 和笔记内容 (--note)")
            return
        manager.add_experiment_note(args.session, args.note)
    
    elif args.action == "params":
        if not args.session or not args.parameters:
            print("❌ 更新参数需要指定会话 ID (--session) 和参数字典 (--parameters)")
            return
        try:
            params = json.loads(args.parameters)
            manager.update_experiment_parameters(args.session, params)
        except json.JSONDecodeError:
            print("❌ 参数字典格式错误，请使用有效的 JSON")
    
    elif args.action == "export":
        if not args.session:
            print("❌ 导出数据需要指定会话 ID (--session)")
            return
        manager.export_experiment_data(args.session, args.output)

if __name__ == "__main__":
    main()
