"""
综合测试脚本 (Comprehensive Testing Script)
验证所有DG优化功能的完整性和正确性
"""

import asyncio
import json
import time
import requests
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================================================
# 测试配置 (Test Configuration)
# ============================================================================

BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = f"test_session_{int(time.time())}"
TEST_USER_ID = "test_user_001"

# ============================================================================
# 测试结果记录器 (Test Result Logger)
# ============================================================================

class TestResultLogger:
    """测试结果记录器"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def log_test(self, test_name: str, status: str, details: str = "", duration: float = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        # 打印测试结果
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if duration > 0:
            print(f"   Duration: {duration:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.results if r["status"] == "WARNING"])
        
        total_duration = time.time() - self.start_time
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warning_tests": warning_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "results": self.results
        }
    
    def save_results(self, filename: str = "test_results.json"):
        """保存测试结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.get_summary(), f, indent=2, ensure_ascii=False)
            print(f"✅ Test results saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save test results: {e}")

# ============================================================================
# 综合测试器 (Comprehensive Tester)
# ============================================================================

class ComprehensiveTester:
    """综合测试器"""
    
    def __init__(self):
        self.logger = TestResultLogger()
        self.session_id = TEST_SESSION_ID
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Starting comprehensive testing...")
        print(f"📋 Test Session ID: {self.session_id}")
        print("=" * 60)
        
        # 1. 基础连接测试
        await self.test_basic_connectivity()
        
        # 2. 数据库功能测试
        await self.test_database_functionality()
        
        # 3. DG评估功能测试
        await self.test_dg_evaluation()
        
        # 4. 用户需求验证测试
        await self.test_user_needs_validation()
        
        # 5. 可访问性测试
        await self.test_accessibility_features()
        
        # 6. IndoorGML功能测试
        await self.test_indoor_gml_features()
        
        # 7. 指标收集测试
        await self.test_metrics_collection()
        
        # 8. 性能测试
        await self.test_performance()
        
        # 9. 集成测试
        await self.test_integration()
        
        # 10. 错误处理测试
        await self.test_error_handling()
        
        # 输出测试摘要
        self.print_test_summary()
        
        # 保存测试结果
        self.logger.save_results()
    
    async def test_basic_connectivity(self):
        """测试基础连接性"""
        print("\n🔌 Testing Basic Connectivity...")
        
        # 测试健康检查端点
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/health/enhanced", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.logger.log_test(
                    "Health Check Endpoint",
                    "PASS",
                    f"Response: {data.get('status', 'unknown')}",
                    duration
                )
            else:
                self.logger.log_test(
                    "Health Check Endpoint",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Health Check Endpoint",
                "FAIL",
                f"Connection error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_database_functionality(self):
        """测试数据库功能"""
        print("\n🗄️ Testing Database Functionality...")
        
        # 测试指标收集端点
        start_time = time.time()
        try:
            test_metric = {
                "metric_id": f"test_metric_{int(time.time())}",
                "metric_type": "test",
                "session_id": self.session_id,
                "user_id": TEST_USER_ID,
                "timestamp": datetime.now().isoformat(),
                "data": {"test": "data"},
                "priority": "normal",
                "tags": ["test", "database"]
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/metrics/collect",
                json=test_metric,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "Database Metrics Collection",
                    "PASS",
                    "Metric collected successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "Database Metrics Collection",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Database Metrics Collection",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_dg_evaluation(self):
        """测试DG评估功能"""
        print("\n📊 Testing DG Evaluation...")
        
        # 测试DG1评估记录
        start_time = time.time()
        try:
            dg1_data = {
                "session_id": self.session_id,
                "design_goal": "DG1",
                "evaluation_type": "hardware_setup",
                "evaluation_data": {
                    "setup_time": 120,
                    "hardware_connected": True,
                    "camera_working": True
                },
                "score": 0.85
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/evaluation/record",
                json=dg1_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "DG1 Evaluation Recording",
                    "PASS",
                    "DG1 evaluation recorded successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "DG1 Evaluation Recording",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "DG1 Evaluation Recording",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
        
        # 测试DG3评估记录
        start_time = time.time()
        try:
            dg3_data = {
                "session_id": self.session_id,
                "design_goal": "DG3",
                "evaluation_type": "localization_accuracy",
                "evaluation_data": {
                    "confidence_score": 0.82,
                    "response_time": 1.5,
                    "accuracy_verified": True
                },
                "score": 0.82
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/evaluation/record",
                json=dg3_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "DG3 Evaluation Recording",
                    "PASS",
                    "DG3 evaluation recorded successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "DG3 Evaluation Recording",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "DG3 Evaluation Recording",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_user_needs_validation(self):
        """测试用户需求验证"""
        print("\n👥 Testing User Needs Validation...")
        
        # 测试N2用户需求记录
        start_time = time.time()
        try:
            n2_data = {
                "session_id": self.session_id,
                "user_need": "N2",
                "metric_name": "positioning_accuracy",
                "value": 0.82,
                "satisfaction_score": 0.85
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/user_needs/record",
                json=n2_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "N2 User Need Validation",
                    "PASS",
                    "N2 validation recorded successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "N2 User Need Validation",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "N2 User Need Validation",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
        
        # 测试用户需求矩阵获取
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/api/dg/user_needs/matrix",
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.logger.log_test(
                    "User Needs Matrix",
                    "PASS",
                    f"Matrix retrieved with {len(data.get('mappings', []))} mappings",
                    duration
                )
            else:
                self.logger.log_test(
                    "User Needs Matrix",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "User Needs Matrix",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_accessibility_features(self):
        """测试可访问性功能"""
        print("\n♿ Testing Accessibility Features...")
        
        # 测试WCAG合规性检查
        start_time = time.time()
        try:
            wcag_data = {
                "session_id": self.session_id,
                "test_type": "wcag_compliance",
                "test_data": {
                    "contrast_ratio": 4.5,
                    "font_size": 16,
                    "keyboard_navigation": True
                }
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/accessibility/check",
                json=wcag_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "WCAG Compliance Check",
                    "PASS",
                    "WCAG compliance checked successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "WCAG Compliance Check",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "WCAG Compliance Check",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_indoor_gml_features(self):
        """测试IndoorGML功能"""
        print("\n🗺️ Testing IndoorGML Features...")
        
        # 测试IndoorGML生成
        start_time = time.time()
        try:
            gml_data = {
                "session_id": self.session_id,
                "site_data": {
                    "site_id": "test_site_001",
                    "site_name": "Test Building",
                    "floors": 3,
                    "total_area": 5000
                },
                "landmarks": [
                    {"id": "L1", "name": "Main Entrance", "type": "entrance"},
                    {"id": "L2", "name": "Elevator", "type": "facility"}
                ],
                "connections": [
                    {"from": "L1", "to": "L2", "type": "corridor"}
                ]
            }
            
            response = requests.post(
                f"{BASE_URL}/api/dg/indoor_gml/generate",
                json=gml_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "IndoorGML Generation",
                    "PASS",
                    "IndoorGML generated successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "IndoorGML Generation",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "IndoorGML Generation",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_metrics_collection(self):
        """测试指标收集功能"""
        print("\n📈 Testing Metrics Collection...")
        
        # 测试指标导出
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/api/dg/metrics/export/{self.session_id}",
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "Metrics Export",
                    "PASS",
                    "Metrics exported successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "Metrics Export",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Metrics Export",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
        
        # 测试指标分析
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/api/dg/metrics/analytics/{self.session_id}",
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.log_test(
                    "Metrics Analytics",
                    "PASS",
                    "Analytics generated successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "Metrics Analytics",
                    "FAIL",
                    f"Status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Metrics Analytics",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_performance(self):
        """测试性能"""
        print("\n⚡ Testing Performance...")
        
        # 测试响应时间
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/health/enhanced", timeout=10)
            duration = time.time() - start_time
            
            if duration < 1.0:  # 期望响应时间小于1秒
                self.logger.log_test(
                    "Response Time Performance",
                    "PASS",
                    f"Response time: {duration:.3f}s",
                    duration
                )
            elif duration < 2.0:
                self.logger.log_test(
                    "Response Time Performance",
                    "WARNING",
                    f"Response time: {duration:.3f}s (acceptable but slow)",
                    duration
                )
            else:
                self.logger.log_test(
                    "Response Time Performance",
                    "FAIL",
                    f"Response time: {duration:.3f}s (too slow)",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Response Time Performance",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_integration(self):
        """测试集成功能"""
        print("\n🔗 Testing Integration...")
        
        # 测试完整的用户流程
        start_time = time.time()
        try:
            # 1. 创建会话
            session_data = {
                "session_id": self.session_id,
                "user_id": TEST_USER_ID,
                "start_time": datetime.now().isoformat()
            }
            
            # 2. 记录用户行为
            behavior_data = {
                "metric_id": f"behavior_{int(time.time())}",
                "metric_type": "user_behavior",
                "session_id": self.session_id,
                "data": {"action": "photo_capture", "confidence": 0.75}
            }
            
            # 3. 记录DG评估
            dg_data = {
                "session_id": self.session_id,
                "design_goal": "DG2",
                "evaluation_type": "semantic_mapping",
                "evaluation_data": {"map_quality": "high", "landmarks": 15},
                "score": 0.88
            }
            
            # 执行集成测试
            responses = []
            
            # 发送行为数据
            response1 = requests.post(
                f"{BASE_URL}/api/dg/metrics/collect",
                json=behavior_data,
                timeout=10
            )
            responses.append(response1.status_code)
            
            # 发送DG评估
            response2 = requests.post(
                f"{BASE_URL}/api/dg/evaluation/record",
                json=dg_data,
                timeout=10
            )
            responses.append(response2.status_code)
            
            duration = time.time() - start_time
            
            if all(code == 200 for code in responses):
                self.logger.log_test(
                    "Integration Test",
                    "PASS",
                    "All integration steps completed successfully",
                    duration
                )
            else:
                self.logger.log_test(
                    "Integration Test",
                    "FAIL",
                    f"Some steps failed: {responses}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Integration Test",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n🚨 Testing Error Handling...")
        
        # 测试无效的会话ID
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/api/dg/metrics/export/invalid_session_id",
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 404 or response.status_code == 400:
                self.logger.log_test(
                    "Error Handling - Invalid Session",
                    "PASS",
                    f"Properly handled invalid session: {response.status_code}",
                    duration
                )
            else:
                self.logger.log_test(
                    "Error Handling - Invalid Session",
                    "WARNING",
                    f"Unexpected status code: {response.status_code}",
                    duration
                )
        except Exception as e:
            self.logger.log_test(
                "Error Handling - Invalid Session",
                "FAIL",
                f"Error: {str(e)}",
                time.time() - start_time
            )
    
    def print_test_summary(self):
        """打印测试摘要"""
        summary = self.logger.get_summary()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Warnings: {summary['warning_tests']} ⚠️")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print("=" * 60)
        
        if summary['failed_tests'] > 0:
            print("\n❌ FAILED TESTS:")
            for result in summary['results']:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test_name']}: {result['details']}")
        
        if summary['warning_tests'] > 0:
            print("\n⚠️ WARNING TESTS:")
            for result in summary['results']:
                if result['status'] == 'WARNING':
                    print(f"  - {result['test_name']}: {result['details']}")

# ============================================================================
// 主函数 (Main Function)
# ============================================================================

async def main():
    """主函数"""
    print("🚀 VLN4VI Comprehensive Testing Suite")
    print("Testing all DG optimization features...")
    
    tester = ComprehensiveTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
