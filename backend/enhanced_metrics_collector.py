"""
增强指标收集器 (Enhanced Metrics Collector)
实现实时数据收集、数据导出和分析功能
"""

import json
import csv
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import sqlite3
import os

# ============================================================================
# 指标类型定义 (Metric Type Definition)
# ============================================================================

class MetricType(Enum):
    """指标类型枚举"""
    USER_BEHAVIOR = "user_behavior"
    SYSTEM_PERFORMANCE = "system_performance"
    EVALUATION_DATA = "evaluation_data"
    ACCESSIBILITY_TEST = "accessibility_test"
    USER_NEED_VALIDATION = "user_need_validation"

class DataPriority(Enum):
    """数据优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MetricData:
    """指标数据结构"""
    metric_id: str
    metric_type: MetricType
    session_id: str
    user_id: Optional[str]
    timestamp: str
    data: Dict[str, Any]
    priority: DataPriority = DataPriority.NORMAL
    tags: List[str] = None

@dataclass
class CollectionConfig:
    """收集配置"""
    auto_save_interval: int = 60  # 秒
    max_buffer_size: int = 1000
    enable_real_time_processing: bool = True
    enable_database_storage: bool = True
    enable_file_storage: bool = True
    storage_path: str = "metrics_data"

# ============================================================================
# 增强指标收集器 (Enhanced Metrics Collector)
# ============================================================================

class EnhancedMetricsCollector:
    """增强指标收集器"""
    
    def __init__(self, config: CollectionConfig = None):
        self.config = config or CollectionConfig()
        self.data_buffer = queue.Queue(maxsize=self.config.max_buffer_size)
        self.session_data = {}
        self.real_time_processors = {}
        self.collection_stats = {
            "total_collected": 0,
            "total_processed": 0,
            "total_stored": 0,
            "errors": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        # 初始化存储
        self._initialize_storage()
        
        # 启动后台处理线程
        if self.config.enable_real_time_processing:
            self._start_background_processing()
    
    def _initialize_storage(self):
        """初始化存储系统"""
        # 创建存储目录
        if self.config.enable_file_storage:
            os.makedirs(self.config.storage_path, exist_ok=True)
            os.makedirs(os.path.join(self.config.storage_path, "sessions"), exist_ok=True)
            os.makedirs(os.path.join(self.config.storage_path, "exports"), exist_ok=True)
        
        # 初始化数据库
        if self.config.enable_database_storage:
            self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = os.path.join(self.config.storage_path, "metrics.db")
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # 创建指标表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建会话表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            self.config.enable_database_storage = False
    
    def _start_background_processing(self):
        """启动后台处理线程"""
        self.processing_thread = threading.Thread(target=self._background_processor, daemon=True)
        self.processing_thread.start()
        
        # 启动自动保存线程
        if self.config.auto_save_interval > 0:
            self.save_thread = threading.Thread(target=self._auto_save_processor, daemon=True)
            self.save_thread.start()
    
    def _background_processor(self):
        """后台数据处理线程"""
        while True:
            try:
                # 从缓冲区获取数据
                metric_data = self.data_buffer.get(timeout=1)
                
                # 实时处理
                self._process_metric_data(metric_data)
                
                # 存储数据
                self._store_metric_data(metric_data)
                
                # 更新统计
                self.collection_stats["total_processed"] += 1
                
                self.data_buffer.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in background processor: {e}")
                self.collection_stats["errors"] += 1
    
    def _auto_save_processor(self):
        """自动保存处理线程"""
        while True:
            try:
                time.sleep(self.config.auto_save_interval)
                self._save_session_data()
            except Exception as e:
                print(f"Error in auto save processor: {e}")
    
    def collect_real_time_data(self, data_type: MetricType, session_id: str, 
                              data: Dict[str, Any], priority: DataPriority = DataPriority.NORMAL,
                              tags: List[str] = None, user_id: Optional[str] = None) -> bool:
        """实时数据收集"""
        try:
            # 创建指标数据
            metric_data = MetricData(
                metric_id=f"{data_type.value}_{int(time.time() * 1000)}",
                metric_type=data_type,
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.utcnow().isoformat(),
                data=data,
                priority=priority,
                tags=tags or []
            )
            
            # 添加到缓冲区
            try:
                self.data_buffer.put_nowait(metric_data)
                self.collection_stats["total_collected"] += 1
                
                # 更新会话数据
                if session_id not in self.session_data:
                    self.session_data[session_id] = {
                        "start_time": metric_data.timestamp,
                        "metrics": [],
                        "user_id": user_id,
                        "status": "active"
                    }
                
                self.session_data[session_id]["metrics"].append(metric_data)
                
                return True
                
            except queue.Full:
                # 缓冲区满，丢弃数据
                print(f"Data buffer full, dropping metric: {metric_data.metric_id}")
                return False
                
        except Exception as e:
            print(f"Error collecting data: {e}")
            self.collection_stats["errors"] += 1
            return False
    
    def _process_metric_data(self, metric_data: MetricData):
        """处理指标数据"""
        # 调用注册的实时处理器
        if metric_data.metric_type in self.real_time_processors:
            try:
                processor = self.real_time_processors[metric_data.metric_type]
                processor(metric_data)
            except Exception as e:
                print(f"Error in real-time processor for {metric_data.metric_type}: {e}")
        
        # 根据优先级进行特殊处理
        if metric_data.priority == DataPriority.CRITICAL:
            self._handle_critical_data(metric_data)
        elif metric_data.priority == DataPriority.HIGH:
            self._handle_high_priority_data(metric_data)
    
    def _handle_critical_data(self, metric_data: MetricData):
        """处理关键数据"""
        # 立即保存到文件
        if self.config.enable_file_storage:
            critical_file = os.path.join(
                self.config.storage_path, 
                "sessions", 
                f"{metric_data.session_id}_critical.jsonl"
            )
            
            try:
                with open(critical_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(metric_data), ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Failed to save critical data: {e}")
    
    def _handle_high_priority_data(self, metric_data: MetricData):
        """处理高优先级数据"""
        # 可以添加特殊处理逻辑，如立即通知、特殊存储等
        pass
    
    def _store_metric_data(self, metric_data: MetricData):
        """存储指标数据"""
        # 存储到数据库
        if self.config.enable_database_storage:
            try:
                self.cursor.execute('''
                    INSERT INTO metrics 
                    (metric_id, metric_type, session_id, user_id, timestamp, data, priority, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric_data.metric_id,
                    metric_data.metric_type.value,
                    metric_data.session_id,
                    metric_data.user_id,
                    metric_data.timestamp,
                    json.dumps(metric_data.data, ensure_ascii=False),
                    metric_data.priority.value,
                    json.dumps(metric_data.tags, ensure_ascii=False)
                ))
                
                self.conn.commit()
                self.collection_stats["total_stored"] += 1
                
            except Exception as e:
                print(f"Failed to store metric data in database: {e}")
        
        # 存储到文件
        if self.config.enable_file_storage:
            try:
                session_file = os.path.join(
                    self.config.storage_path, 
                    "sessions", 
                    f"{metric_data.session_id}.jsonl"
                )
                
                with open(session_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(metric_data), ensure_ascii=False) + '\n')
                    
            except Exception as e:
                print(f"Failed to store metric data in file: {e}")
    
    def register_real_time_processor(self, metric_type: MetricType, processor: Callable[[MetricData], None]):
        """注册实时处理器"""
        self.real_time_processors[metric_type] = processor
    
    def get_session_metrics(self, session_id: str) -> List[MetricData]:
        """获取会话指标"""
        if session_id in self.session_data:
            return self.session_data[session_id]["metrics"]
        return []
    
    def get_metrics_by_type(self, metric_type: MetricType, session_id: Optional[str] = None) -> List[MetricData]:
        """根据类型获取指标"""
        metrics = []
        
        for session_id_key, session_info in self.session_data.items():
            if session_id and session_id_key != session_id:
                continue
            
            for metric in session_info["metrics"]:
                if metric.metric_type == metric_type:
                    metrics.append(metric)
        
        return metrics
    
    def get_metrics_by_time_range(self, start_time: str, end_time: str, 
                                 session_id: Optional[str] = None) -> List[MetricData]:
        """根据时间范围获取指标"""
        metrics = []
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        for session_id_key, session_info in self.session_data.items():
            if session_id and session_id_key != session_id:
                continue
            
            for metric in session_info["metrics"]:
                metric_dt = datetime.fromisoformat(metric.timestamp)
                if start_dt <= metric_dt <= end_dt:
                    metrics.append(metric)
        
        return metrics
    
    def export_data_to_csv(self, filename: str, data_type: Optional[MetricType] = None, 
                          session_id: Optional[str] = None, time_range: Optional[Tuple[str, str]] = None):
        """导出数据到CSV文件"""
        try:
            # 确定要导出的数据
            if data_type and session_id:
                metrics = self.get_metrics_by_type(data_type, session_id)
            elif data_type:
                metrics = self.get_metrics_by_type(data_type)
            elif session_id:
                metrics = self.get_session_metrics(session_id)
            elif time_range:
                metrics = self.get_metrics_by_time_range(time_range[0], time_range[1])
            else:
                # 导出所有数据
                metrics = []
                for session_info in self.session_data.values():
                    metrics.extend(session_info["metrics"])
            
            if not metrics:
                print("No metrics to export")
                return False
            
            # 确定输出路径
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            output_path = os.path.join(self.config.storage_path, "exports", filename)
            
            # 写入CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # 获取所有可能的字段
                all_fields = set()
                for metric in metrics:
                    all_fields.update(metric.data.keys())
                
                fieldnames = ['metric_id', 'metric_type', 'session_id', 'user_id', 'timestamp', 'priority', 'tags'] + list(all_fields)
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for metric in metrics:
                    row = {
                        'metric_id': metric.metric_id,
                        'metric_type': metric.metric_type.value,
                        'session_id': metric.session_id,
                        'user_id': metric.user_id,
                        'timestamp': metric.timestamp,
                        'priority': metric.priority.value,
                        'tags': ','.join(metric.tags) if metric.tags else ''
                    }
                    
                    # 添加数据字段
                    for field in all_fields:
                        row[field] = metric.data.get(field, '')
                    
                    writer.writerow(row)
            
            print(f"Data exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to export data to CSV: {e}")
            return False
    
    def export_data_to_json(self, filename: str, data_type: Optional[MetricType] = None, 
                           session_id: Optional[str] = None, time_range: Optional[Tuple[str, str]] = None):
        """导出数据到JSON文件"""
        try:
            # 确定要导出的数据
            if data_type and session_id:
                metrics = self.get_metrics_by_type(data_type, session_id)
            elif data_type:
                metrics = self.get_metrics_by_type(data_type)
            elif session_id:
                metrics = self.get_session_metrics(session_id)
            elif time_range:
                metrics = self.get_metrics_by_time_range(time_range[0], time_range[1])
            else:
                # 导出所有数据
                metrics = []
                for session_info in self.session_data.values():
                    metrics.extend(session_info["metrics"])
            
            if not metrics:
                print("No metrics to export")
                return False
            
            # 确定输出路径
            if not filename.endswith('.json'):
                filename += '.json'
            
            output_path = os.path.join(self.config.storage_path, "exports", filename)
            
            # 转换为可序列化的格式
            export_data = []
            for metric in metrics:
                metric_dict = asdict(metric)
                # 确保datetime对象被正确序列化
                export_data.append(metric_dict)
            
            # 写入JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"Data exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to export data to JSON: {e}")
            return False
    
    def generate_analytics_report(self, session_id: str) -> Dict[str, Any]:
        """生成分析报告"""
        if session_id not in self.session_data:
            return {"error": "Session not found"}
        
        session_info = self.session_data[session_id]
        metrics = session_info["metrics"]
        
        if not metrics:
            return {"error": "No metrics available for this session"}
        
        # 按类型分组
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)
        
        # 计算统计信息
        report = {
            "session_id": session_id,
            "user_id": session_info["user_id"],
            "start_time": session_info["start_time"],
            "end_time": session_info.get("end_time"),
            "status": session_info["status"],
            "total_metrics": len(metrics),
            "metrics_by_type": {},
            "timeline_analysis": {},
            "priority_distribution": {},
            "tags_analysis": {}
        }
        
        # 按类型分析
        for metric_type, type_metrics in metrics_by_type.items():
            report["metrics_by_type"][metric_type] = {
                "count": len(type_metrics),
                "percentage": len(type_metrics) / len(metrics) * 100,
                "latest_timestamp": max(m.timestamp for m in type_metrics),
                "earliest_timestamp": min(m.timestamp for m in type_metrics)
            }
        
        # 时间线分析
        if metrics:
            timestamps = [datetime.fromisoformat(m.timestamp) for m in metrics]
            report["timeline_analysis"] = {
                "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds(),
                "metrics_per_minute": len(metrics) / ((max(timestamps) - min(timestamps)).total_seconds() / 60),
                "peak_activity_time": max(timestamps).isoformat()
            }
        
        # 优先级分布
        priority_counts = {}
        for metric in metrics:
            priority = metric.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        report["priority_distribution"] = priority_counts
        
        # 标签分析
        all_tags = []
        for metric in metrics:
            if metric.tags:
                all_tags.extend(metric.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        report["tags_analysis"] = {
            "unique_tags": len(set(all_tags)),
            "tag_frequency": tag_counts,
            "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        return report
    
    def _save_session_data(self):
        """保存会话数据"""
        for session_id, session_info in self.session_data.items():
            if session_info["status"] == "active":
                try:
                    session_file = os.path.join(
                        self.config.storage_path, 
                        "sessions", 
                        f"{session_id}.jsonl"
                    )
                    
                    # 只保存未保存的指标
                    saved_metrics = set()
                    if os.path.exists(session_file):
                        with open(session_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    metric_data = json.loads(line.strip())
                                    saved_metrics.add(metric_data["metric_id"])
                                except:
                                    continue
                    
                    # 保存新指标
                    with open(session_file, 'a', encoding='utf-8') as f:
                        for metric in session_info["metrics"]:
                            if metric.metric_id not in saved_metrics:
                                f.write(json.dumps(asdict(metric), ensure_ascii=False) + '\n')
                    
                except Exception as e:
                    print(f"Failed to save session data for {session_id}: {e}")
    
    def close_session(self, session_id: str, end_time: Optional[str] = None):
        """关闭会话"""
        if session_id in self.session_data:
            self.session_data[session_id]["status"] = "closed"
            self.session_data[session_id]["end_time"] = end_time or datetime.utcnow().isoformat()
            
            # 保存最终数据
            self._save_session_data()
            
            # 更新数据库中的会话状态
            if self.config.enable_database_storage:
                try:
                    self.cursor.execute('''
                        UPDATE sessions 
                        SET end_time = ?, status = ? 
                        WHERE session_id = ?
                    ''', (self.session_data[session_id]["end_time"], "closed", session_id))
                    self.conn.commit()
                except Exception as e:
                    print(f"Failed to update session status in database: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取收集统计信息"""
        stats = self.collection_stats.copy()
        stats["current_time"] = datetime.utcnow().isoformat()
        stats["active_sessions"] = sum(1 for s in self.session_data.values() if s["status"] == "active")
        stats["total_sessions"] = len(self.session_data)
        stats["buffer_size"] = self.data_buffer.qsize()
        
        # 计算运行时间
        start_time = datetime.fromisoformat(stats["start_time"])
        current_time = datetime.utcnow()
        stats["uptime_seconds"] = (current_time - start_time).total_seconds()
        stats["uptime_hours"] = stats["uptime_seconds"] / 3600
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """清理旧数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 清理内存中的旧数据
        sessions_to_remove = []
        for session_id, session_info in self.session_data.items():
            if session_info["status"] == "closed":
                end_time = datetime.fromisoformat(session_info.get("end_time", session_info["start_time"]))
                if end_time < cutoff_date:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_data[session_id]
        
        # 清理数据库中的旧数据
        if self.config.enable_database_storage:
            try:
                cutoff_str = cutoff_date.isoformat()
                self.cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_str,))
                self.cursor.execute('DELETE FROM sessions WHERE end_time < ? AND status = "closed"', (cutoff_str,))
                self.conn.commit()
            except Exception as e:
                print(f"Failed to cleanup old database data: {e}")
        
        print(f"Cleaned up data older than {days_to_keep} days")
    
    def __del__(self):
        """析构函数"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except:
            pass

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建收集器配置
    config = CollectionConfig(
        auto_save_interval=30,
        max_buffer_size=500,
        enable_real_time_processing=True,
        enable_database_storage=True,
        enable_file_storage=True,
        storage_path="test_metrics_data"
    )
    
    # 创建增强指标收集器
    collector = EnhancedMetricsCollector(config)
    
    # 注册实时处理器
    def user_behavior_processor(metric_data: MetricData):
        print(f"Processing user behavior: {metric_data.metric_id}")
    
    def system_performance_processor(metric_data: MetricData):
        print(f"Processing system performance: {metric_data.metric_id}")
    
    collector.register_real_time_processor(MetricType.USER_BEHAVIOR, user_behavior_processor)
    collector.register_real_time_processor(MetricType.SYSTEM_PERFORMANCE, system_performance_processor)
    
    # 模拟数据收集
    session_id = "test_session_001"
    
    # 收集用户行为数据
    collector.collect_real_time_data(
        MetricType.USER_BEHAVIOR,
        session_id,
        {
            "action": "photo_capture",
            "confidence": 0.85,
            "location": "entrance",
            "timestamp": datetime.utcnow().isoformat()
        },
        priority=DataPriority.HIGH,
        tags=["navigation", "localization"]
    )
    
    # 收集系统性能数据
    collector.collect_real_time_data(
        MetricType.SYSTEM_PERFORMANCE,
        session_id,
        {
            "response_time": 1.2,
            "memory_usage": 45.6,
            "cpu_usage": 23.4,
            "status": "normal"
        },
        priority=DataPriority.NORMAL,
        tags=["performance", "monitoring"]
    )
    
    # 收集评估数据
    collector.collect_real_time_data(
        MetricType.EVALUATION_DATA,
        session_id,
        {
            "evaluation_type": "nasa_tlx",
            "mental_demand": 3,
            "physical_demand": 2,
            "temporal_demand": 4,
            "performance": 4,
            "effort": 3,
            "frustration": 2
        },
        priority=DataPriority.NORMAL,
        tags=["evaluation", "nasa_tlx"]
    )
    
    # 等待数据处理
    time.sleep(2)
    
    # 获取会话指标
    session_metrics = collector.get_session_metrics(session_id)
    print(f"Session metrics count: {len(session_metrics)}")
    
    # 生成分析报告
    report = collector.generate_analytics_report(session_id)
    print("Analytics Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 导出数据
    collector.export_data_to_csv("test_session_metrics.csv", session_id=session_id)
    collector.export_data_to_json("test_session_metrics.json", session_id=session_id)
    
    # 获取收集统计
    stats = collector.get_collection_stats()
    print("\nCollection Stats:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 关闭会话
    collector.close_session(session_id)
    
    print("\nTest completed successfully!")
