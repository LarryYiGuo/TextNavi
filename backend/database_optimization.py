"""
数据库优化脚本 (Database Optimization Script)
扩展现有数据表结构以支持DG优化功能
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# ============================================================================
# 数据库配置 (Database Configuration)
# ============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "dg_optimization.db")
METRICS_DB_PATH = os.path.join(os.path.dirname(__file__), "metrics_data", "metrics.db")

# ============================================================================
# 数据库优化器 (Database Optimizer)
# ============================================================================

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.metrics_conn = None
        self.metrics_cursor = None
    
    def connect_main_db(self):
        """连接主数据库"""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to main database: {DB_PATH}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to main database: {e}")
            return False
    
    def connect_metrics_db(self):
        """连接指标数据库"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(METRICS_DB_PATH), exist_ok=True)
            
            self.metrics_conn = sqlite3.connect(METRICS_DB_PATH)
            self.metrics_cursor = self.metrics_conn.cursor()
            print(f"✅ Connected to metrics database: {METRICS_DB_PATH}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to metrics database: {e}")
            return False
    
    def create_dg_optimization_tables(self):
        """创建DG优化相关的数据表"""
        try:
            # 1. 设计目标评估表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS dg_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    design_goal TEXT NOT NULL,
                    evaluation_type TEXT NOT NULL,
                    evaluation_data TEXT NOT NULL,
                    score REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 用户需求验证表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_needs_validation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_need TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    satisfaction_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 3. 可访问性测试表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS accessibility_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    test_data TEXT NOT NULL,
                    result TEXT NOT NULL,
                    compliance_score REAL,
                    issues_found TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 4. IndoorGML地图表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS indoor_gml_maps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    map_content TEXT NOT NULL,
                    validation_results TEXT,
                    compliance_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 5. 系统性能指标表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL,
                    unit TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 6. 用户行为分析表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_behavior_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    behavior_type TEXT NOT NULL,
                    behavior_data TEXT NOT NULL,
                    analysis_result TEXT,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 7. 导航任务完成表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS navigation_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    start_location TEXT,
                    target_location TEXT,
                    status TEXT DEFAULT 'in_progress',
                    completion_time REAL,
                    success_rate REAL,
                    veering_events INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # 8. 信任度评估表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL,
                    trust_score_before REAL,
                    trust_score_after REAL,
                    trust_change REAL,
                    context TEXT,
                    event_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            self._create_indexes()
            
            self.conn.commit()
            print("✅ DG optimization tables created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create DG optimization tables: {e}")
            return False
    
    def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 为常用查询创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_dg_evaluations_session ON dg_evaluations(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_dg_evaluations_goal ON dg_evaluations(design_goal)",
                "CREATE INDEX IF NOT EXISTS idx_user_needs_session ON user_needs_validation(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_needs_need ON user_needs_validation(user_need)",
                "CREATE INDEX IF NOT EXISTS idx_accessibility_session ON accessibility_tests(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_accessibility_type ON accessibility_tests(test_type)",
                "CREATE INDEX IF NOT EXISTS idx_indoor_gml_session ON indoor_gml_maps(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_system_perf_session ON system_performance(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_behavior_session ON user_behavior_analysis(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_navigation_session ON navigation_tasks(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_trust_session ON trust_assessments(session_id)"
            ]
            
            for index_sql in indexes:
                self.cursor.execute(index_sql)
            
            print("✅ Database indexes created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create indexes: {e}")
    
    def create_metrics_tables(self):
        """创建指标收集相关的数据表"""
        try:
            # 1. 指标数据表
            self.metrics_cursor.execute('''
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
            
            # 2. 会话管理表
            self.metrics_cursor.execute('''
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
            
            # 3. 评估指标表
            self.metrics_cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    unit TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 4. 用户反馈表
            self.metrics_cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    feedback_data TEXT NOT NULL,
                    rating INTEGER,
                    comments TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            self._create_metrics_indexes()
            
            self.metrics_conn.commit()
            print("✅ Metrics tables created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create metrics tables: {e}")
            return False
    
    def _create_metrics_indexes(self):
        """创建指标数据库索引"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)",
                "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_evaluation_session ON evaluation_metrics(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_feedback_session ON user_feedback(session_id)"
            ]
            
            for index_sql in indexes:
                self.metrics_cursor.execute(index_sql)
            
            print("✅ Metrics database indexes created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create metrics indexes: {e}")
    
    def migrate_existing_data(self):
        """迁移现有数据到新的表结构"""
        try:
            print("🔄 Starting data migration...")
            
            # 这里可以添加从现有日志文件迁移数据的逻辑
            # 例如：从CSV文件导入到数据库
            
            print("✅ Data migration completed")
            return True
            
        except Exception as e:
            print(f"❌ Data migration failed: {e}")
            return False
    
    def create_sample_data(self):
        """创建示例数据用于测试"""
        try:
            print("📝 Creating sample data...")
            
            # 示例会话数据
            sample_session = {
                "session_id": "sample_session_001",
                "user_id": "test_user",
                "start_time": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            self.metrics_cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, start_time, status) 
                VALUES (?, ?, ?, ?)
            ''', (
                sample_session["session_id"],
                sample_session["user_id"],
                sample_session["start_time"],
                sample_session["status"]
            ))
            
            # 示例指标数据
            sample_metrics = [
                ("user_behavior", "photo_capture", {"action": "photo_capture", "confidence": 0.85}),
                ("system_performance", "response_time", {"response_time": 1.2, "unit": "seconds"}),
                ("evaluation_data", "nasa_tlx", {"mental_demand": 3, "physical_demand": 2})
            ]
            
            for metric_type, metric_name, data in sample_metrics:
                self.metrics_cursor.execute('''
                    INSERT INTO metrics 
                    (metric_id, metric_type, session_id, timestamp, data, priority, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{metric_type}_{metric_name}_{datetime.utcnow().timestamp()}",
                    metric_type,
                    sample_session["session_id"],
                    datetime.utcnow().isoformat(),
                    json.dumps(data),
                    "normal",
                    json.dumps(["sample", "test"])
                ))
            
            self.metrics_conn.commit()
            print("✅ Sample data created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create sample data: {e}")
            return False
    
    def optimize_database(self):
        """优化数据库性能"""
        try:
            print("🔧 Optimizing database...")
            
            # 分析表
            self.cursor.execute("ANALYZE")
            self.metrics_cursor.execute("ANALYZE")
            
            # 清理碎片
            self.cursor.execute("VACUUM")
            self.metrics_cursor.execute("VACUUM")
            
            # 更新统计信息
            self.cursor.execute("REINDEX")
            self.metrics_cursor.execute("REINDEX")
            
            print("✅ Database optimization completed")
            return True
            
        except Exception as e:
            print(f"❌ Database optimization failed: {e}")
            return False
    
    def get_database_info(self):
        """获取数据库信息"""
        try:
            info = {
                "main_database": {
                    "path": DB_PATH,
                    "tables": [],
                    "size_mb": 0
                },
                "metrics_database": {
                    "path": METRICS_DB_PATH,
                    "tables": [],
                    "size_mb": 0
                }
            }
            
            # 获取主数据库表信息
            if self.conn:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info["main_database"]["tables"] = [row[0] for row in self.cursor.fetchall()]
                
                # 获取数据库大小
                if os.path.exists(DB_PATH):
                    info["main_database"]["size_mb"] = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)
            
            # 获取指标数据库表信息
            if self.metrics_conn:
                self.metrics_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info["metrics_database"]["tables"] = [row[0] for row in self.metrics_cursor.fetchall()]
                
                # 获取数据库大小
                if os.path.exists(METRICS_DB_PATH):
                    info["metrics_database"]["size_mb"] = round(os.path.getsize(METRICS_DB_PATH) / (1024 * 1024), 2)
            
            return info
            
        except Exception as e:
            print(f"❌ Failed to get database info: {e}")
            return {}
    
    def close_connections(self):
        """关闭数据库连接"""
        try:
            if self.conn:
                self.conn.close()
                print("✅ Main database connection closed")
            
            if self.metrics_conn:
                self.metrics_conn.close()
                print("✅ Metrics database connection closed")
                
        except Exception as e:
            print(f"❌ Failed to close connections: {e}")

# ============================================================================
# 主函数 (Main Function)
# ============================================================================

def main():
    """主函数"""
    print("🚀 Starting database optimization...")
    
    optimizer = DatabaseOptimizer()
    
    try:
        # 连接数据库
        if not optimizer.connect_main_db():
            return
        
        if not optimizer.connect_metrics_db():
            return
        
        # 创建DG优化表
        if not optimizer.create_dg_optimization_tables():
            return
        
        # 创建指标表
        if not optimizer.create_metrics_tables():
            return
        
        # 创建示例数据
        if not optimizer.create_sample_data():
            return
        
        # 优化数据库
        if not optimizer.optimize_database():
            return
        
        # 获取数据库信息
        db_info = optimizer.get_database_info()
        print("\n📊 Database Information:")
        print(json.dumps(db_info, indent=2, ensure_ascii=False))
        
        print("\n✅ Database optimization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database optimization failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        optimizer.close_connections()

if __name__ == "__main__":
    main()
