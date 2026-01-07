#!/usr/bin/env python3
"""
VLN4VI 系统启动脚本 (VLN4VI System Startup Script)
启动整个系统，包括后端、前端和数据库优化
"""

import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

# ============================================================================
# 系统配置 (System Configuration)
# ============================================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 后端配置
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_APP = BACKEND_DIR / "app.py"
BACKEND_PORT = 8000

# 前端配置
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_PORT = 3000

# 数据库配置
DATABASE_SCRIPT = BACKEND_DIR / "database_optimization.py"

# 测试配置
TEST_SCRIPT = BACKEND_DIR / "comprehensive_testing.py"

# ============================================================================
# 系统管理器 (System Manager)
# ============================================================================

class SystemManager:
    """系统管理器"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def check_dependencies(self):
        """检查系统依赖"""
        print("🔍 Checking system dependencies...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            return False
        
        # 检查必要的目录
        required_dirs = [BACKEND_DIR, FRONTEND_DIR]
        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"❌ Required directory not found: {dir_path}")
                return False
        
        # 检查必要的文件
        required_files = [BACKEND_APP, DATABASE_SCRIPT]
        for file_path in required_files:
            if not file_path.exists():
                print(f"❌ Required file not found: {file_path}")
                return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def setup_database(self):
        """设置数据库"""
        print("\n🗄️ Setting up database...")
        
        try:
            # 切换到后端目录
            os.chdir(BACKEND_DIR)
            
            # 运行数据库优化脚本
            result = subprocess.run([
                sys.executable, str(DATABASE_SCRIPT)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Database setup completed successfully")
                return True
            else:
                print(f"❌ Database setup failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Database setup timed out")
            return False
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            return False
        finally:
            # 返回项目根目录
            os.chdir(PROJECT_ROOT)
    
    def start_backend(self):
        """启动后端服务"""
        print(f"\n🚀 Starting backend server on port {BACKEND_PORT}...")
        
        try:
            # 切换到后端目录
            os.chdir(BACKEND_DIR)
            
            # 启动FastAPI应用
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app:app",
                "--host", "0.0.0.0",
                "--port", str(BACKEND_PORT),
                "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['backend'] = process
            print(f"✅ Backend server started (PID: {process.pid})")
            
            # 等待服务启动
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
        finally:
            # 返回项目根目录
            os.chdir(PROJECT_ROOT)
    
    def start_frontend(self):
        """启动前端服务"""
        print(f"\n🌐 Starting frontend server on port {FRONTEND_PORT}...")
        
        try:
            # 切换到前端目录
            os.chdir(FRONTEND_DIR)
            
            # 检查是否有package.json
            if not (FRONTEND_DIR / "package.json").exists():
                print("⚠️ No package.json found, skipping frontend startup")
                return True
            
            # 启动前端开发服务器
            process = subprocess.Popen([
                "npm", "start"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['frontend'] = process
            print(f"✅ Frontend server started (PID: {process.pid})")
            
            # 等待服务启动
            time.sleep(10)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
        finally:
            # 返回项目根目录
            os.chdir(PROJECT_ROOT)
    
    def wait_for_services(self):
        """等待服务启动"""
        print("\n⏳ Waiting for services to start...")
        
        # 等待后端服务
        backend_ready = False
        for i in range(30):  # 最多等待30秒
            try:
                import requests
                response = requests.get(f"http://localhost:{BACKEND_PORT}/health/enhanced", timeout=5)
                if response.status_code == 200:
                    backend_ready = True
                    print("✅ Backend service is ready")
                    break
            except:
                pass
            
            if not backend_ready:
                print(f"   Waiting for backend... ({i+1}/30)")
                time.sleep(1)
        
        if not backend_ready:
            print("❌ Backend service failed to start")
            return False
        
        # 等待前端服务（如果启动）
        if 'frontend' in self.processes:
            frontend_ready = False
            for i in range(30):  # 最多等待30秒
                try:
                    import requests
                    response = requests.get(f"http://localhost:{FRONTEND_PORT}", timeout=5)
                    if response.status_code == 200:
                        frontend_ready = True
                        print("✅ Frontend service is ready")
                        break
                except:
                    pass
                
                if not frontend_ready:
                    print(f"   Waiting for frontend... ({i+1}/30)")
                    time.sleep(1)
            
            if not frontend_ready:
                print("⚠️ Frontend service may not be ready")
        
        return True
    
    def run_tests(self):
        """运行测试"""
        print("\n🧪 Running comprehensive tests...")
        
        try:
            # 切换到后端目录
            os.chdir(BACKEND_DIR)
            
            # 运行测试脚本
            result = subprocess.run([
                sys.executable, str(TEST_SCRIPT)
            ], capture_output=True, text=True, timeout=300)  # 5分钟超时
            
            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                print(f"⚠️ Some tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Tests timed out")
            return False
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            return False
        finally:
            # 返回项目根目录
            os.chdir(PROJECT_ROOT)
    
    def monitor_services(self):
        """监控服务状态"""
        print("\n📊 Monitoring services...")
        
        while self.running:
            try:
                # 检查后端状态
                if 'backend' in self.processes:
                    backend_process = self.processes['backend']
                    if backend_process.poll() is not None:
                        print("❌ Backend service stopped unexpectedly")
                        break
                
                # 检查前端状态
                if 'frontend' in self.processes:
                    frontend_process = self.processes['frontend']
                    if frontend_process.poll() is not None:
                        print("❌ Frontend service stopped unexpectedly")
                        break
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(5)
    
    def start(self):
        """启动系统"""
        print("🚀 VLN4VI System Startup")
        print("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            print("❌ System startup failed due to missing dependencies")
            return False
        
        # 设置数据库
        if not self.setup_database():
            print("❌ System startup failed due to database setup failure")
            return False
        
        # 启动后端
        if not self.start_backend():
            print("❌ System startup failed due to backend startup failure")
            return False
        
        # 启动前端
        if not self.start_frontend():
            print("⚠️ Frontend startup failed, continuing with backend only")
        
        # 等待服务启动
        if not self.wait_for_services():
            print("❌ System startup failed due to service startup timeout")
            return False
        
        # 运行测试
        self.run_tests()
        
        # 设置运行标志
        self.running = True
        
        # 显示系统状态
        self.show_system_status()
        
        # 开始监控
        self.monitor_services()
        
        return True
    
    def show_system_status(self):
        """显示系统状态"""
        print("\n" + "=" * 50)
        print("🎉 VLN4VI System is Running!")
        print("=" * 50)
        print(f"Backend API: http://localhost:{BACKEND_PORT}")
        if 'frontend' in self.processes:
            print(f"Frontend UI: http://localhost:{FRONTEND_PORT}")
        print(f"Health Check: http://localhost:{BACKEND_PORT}/health/enhanced")
        print("\nPress Ctrl+C to stop the system")
        print("=" * 50)
    
    def shutdown(self):
        """关闭系统"""
        print("\n🛑 Shutting down VLN4VI system...")
        
        self.running = False
        
        # 停止所有进程
        for name, process in self.processes.items():
            try:
                print(f"   Stopping {name} service...")
                process.terminate()
                process.wait(timeout=10)
                print(f"   ✅ {name} service stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ {name} service did not stop gracefully, forcing...")
                process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping {name} service: {e}")
        
        print("✅ System shutdown completed")

# ============================================================================
# 主函数 (Main Function)
# ============================================================================

def main():
    """主函数"""
    # 创建系统管理器
    manager = SystemManager()
    
    try:
        # 启动系统
        if manager.start():
            print("\n🎉 System startup completed successfully!")
        else:
            print("\n❌ System startup failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Startup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during startup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 确保系统正确关闭
        manager.shutdown()

if __name__ == "__main__":
    main()
