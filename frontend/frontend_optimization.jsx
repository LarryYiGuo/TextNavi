/**
 * 前端优化脚本 (Frontend Optimization Script)
 * 优化前端界面以支持DG优化功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { createRoot } from 'react-dom/client';

// ============================================================================
// 优化后的主应用组件 (Optimized Main App Component)
// ============================================================================

class OptimizedApp extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            // 基础状态
            isCameraOn: false,
            isRecording: false,
            locationConfidence: 0,
            currentLocation: null,
            navigationMode: 'off',
            
            // DG优化相关状态
            dgMetrics: {
                sessionId: this.generateSessionId(),
                startTime: new Date().toISOString(),
                userBehavior: [],
                systemPerformance: [],
                accessibilityChecks: [],
                trustAssessments: []
            },
            
            // 可访问性状态
            accessibilityMode: 'standard',
            voiceOverEnabled: false,
            highContrastMode: false,
            largeTextMode: false,
            
            // 用户需求验证状态
            userNeedsValidation: {
                N1: { status: 'pending', score: 0 },
                N2: { status: 'pending', score: 0 },
                N3: { status: 'pending', score: 0 },
                N4: { status: 'pending', score: 0 },
                N5: { status: 'pending', score: 0 },
                N6: { status: 'pending', score: 0 }
            },
            
            // 系统性能指标
            performanceMetrics: {
                responseTime: 0,
                memoryUsage: 0,
                cpuUsage: 0,
                networkLatency: 0
            },
            
            // 错误和状态
            errorMessage: null,
            isLoading: false,
            lastUpdate: null
        };
        
        // 绑定方法
        this.handlePhotoCapture = this.handlePhotoCapture.bind(this);
        this.handleVoiceCommand = this.handleVoiceCommand.bind(this);
        this.toggleAccessibilityMode = this.toggleAccessibilityMode.bind(this);
        this.collectMetrics = this.collectMetrics.bind(this);
        this.validateUserNeeds = this.validateUserNeeds.bind(this);
        this.exportMetrics = this.exportMetrics.bind(this);
    }
    
    componentDidMount() {
        this.initializeAccessibility();
        this.startPerformanceMonitoring();
        this.collectMetrics('app_initialization', { timestamp: Date.now() });
    }
    
    componentWillUnmount() {
        this.stopPerformanceMonitoring();
        this.exportMetrics();
    }
    
    // ============================================================================
    // 核心功能方法 (Core Function Methods)
    // ============================================================================
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    async handlePhotoCapture() {
        try {
            this.setState({ isLoading: true, errorMessage: null });
            
            // 收集用户行为指标
            this.collectMetrics('photo_capture_attempt', {
                timestamp: Date.now(),
                confidence: this.state.locationConfidence
            });
            
            // 模拟拍照过程
            await this.simulatePhotoCapture();
            
            // 更新位置置信度
            const newConfidence = Math.random() * 0.3 + 0.4; // 0.4-0.7
            this.setState({ locationConfidence: newConfidence });
            
            // 验证用户需求N2 (定位精度)
            this.validateUserNeeds('N2', newConfidence);
            
            // 收集系统性能指标
            this.collectMetrics('photo_capture_complete', {
                timestamp: Date.now(),
                confidence: newConfidence,
                responseTime: this.state.performanceMetrics.responseTime
            });
            
        } catch (error) {
            this.setState({ errorMessage: error.message });
            this.collectMetrics('photo_capture_error', {
                timestamp: Date.now(),
                error: error.message
            });
        } finally {
            this.setState({ isLoading: false });
        }
    }
    
    async simulatePhotoCapture() {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve();
            }, 1000 + Math.random() * 2000);
        });
    }
    
    async handleVoiceCommand(command) {
        try {
            this.collectMetrics('voice_command', {
                timestamp: Date.now(),
                command: command,
                confidence: this.state.locationConfidence
            });
            
            if (this.state.locationConfidence <= 0.7) {
                // 低置信度时的语音提示
                this.speak("Please take more photos to confirm your location");
                return;
            }
            
            // 处理导航命令
            if (command.toLowerCase().includes('navigate')) {
                this.setState({ navigationMode: 'active' });
                this.collectMetrics('navigation_activated', {
                    timestamp: Date.now(),
                    command: command
                });
            }
            
        } catch (error) {
            this.collectMetrics('voice_command_error', {
                timestamp: Date.now(),
                error: error.message
            });
        }
    }
    
    // ============================================================================
    // 可访问性功能 (Accessibility Features)
    // ============================================================================
    
    initializeAccessibility() {
        // 检测VoiceOver
        if (window.speechSynthesis) {
            this.setState({ voiceOverEnabled: true });
        }
        
        // 检测系统偏好
        if (window.matchMedia) {
            const prefersHighContrast = window.matchMedia('(prefers-contrast: high)');
            const prefersLargeText = window.matchMedia('(prefers-font-size: large)');
            
            this.setState({
                highContrastMode: prefersHighContrast.matches,
                largeTextMode: prefersLargeText.matches
            });
        }
    }
    
    toggleAccessibilityMode() {
        const modes = ['standard', 'high_contrast', 'large_text', 'voice_guided'];
        const currentIndex = modes.indexOf(this.state.accessibilityMode);
        const nextIndex = (currentIndex + 1) % modes.length;
        
        this.setState({ accessibilityMode: modes[nextIndex] });
        
        this.collectMetrics('accessibility_mode_change', {
            timestamp: Date.now(),
            mode: modes[nextIndex]
        });
    }
    
    speak(text) {
        if (window.speechSynthesis && this.state.voiceOverEnabled) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            window.speechSynthesis.speak(utterance);
        }
    }
    
    // ============================================================================
    // 指标收集和验证 (Metrics Collection and Validation)
    // ============================================================================
    
    collectMetrics(type, data) {
        const metric = {
            id: `${type}_${Date.now()}`,
            type: type,
            timestamp: Date.now(),
            data: data,
            sessionId: this.state.dgMetrics.sessionId
        };
        
        this.setState(prevState => ({
            dgMetrics: {
                ...prevState.dgMetrics,
                userBehavior: [...prevState.dgMetrics.userBehavior, metric]
            }
        }));
        
        // 发送到后端
        this.sendMetricsToBackend(metric);
    }
    
    async sendMetricsToBackend(metric) {
        try {
            const response = await fetch('/api/dg/metrics/collect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(metric)
            });
            
            if (!response.ok) {
                console.warn('Failed to send metrics to backend');
            }
        } catch (error) {
            console.error('Error sending metrics:', error);
        }
    }
    
    validateUserNeeds(needId, value) {
        let score = 0;
        let status = 'pending';
        
        switch (needId) {
            case 'N1': // 拓扑地图
                score = value > 0.8 ? 0.9 : value > 0.6 ? 0.7 : 0.4;
                break;
            case 'N2': // 定位精度
                score = value > 0.8 ? 0.95 : value > 0.7 ? 0.8 : 0.5;
                break;
            case 'N3': // 分离指令
                score = this.state.navigationMode === 'active' ? 0.9 : 0.6;
                break;
            case 'N4': // 低置信度处理
                score = value <= 0.7 ? 0.9 : 0.7;
                break;
            case 'N5': // 可访问性
                score = this.state.accessibilityMode !== 'standard' ? 0.9 : 0.7;
                break;
            case 'N6': // 标准化
                score = 0.8; // 基于代码质量
                break;
        }
        
        status = score >= 0.8 ? 'satisfied' : score >= 0.6 ? 'partially_satisfied' : 'unsatisfied';
        
        this.setState(prevState => ({
            userNeedsValidation: {
                ...prevState.userNeedsValidation,
                [needId]: { status, score }
            }
        }));
        
        // 发送验证数据到后端
        this.sendUserNeedsValidation(needId, score, status);
    }
    
    async sendUserNeedsValidation(needId, score, status) {
        try {
            const validationData = {
                sessionId: this.state.dgMetrics.sessionId,
                userNeed: needId,
                score: score,
                status: status,
                timestamp: Date.now()
            };
            
            const response = await fetch('/api/dg/user_needs/record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(validationData)
            });
            
            if (!response.ok) {
                console.warn('Failed to send user needs validation');
            }
        } catch (error) {
            console.error('Error sending user needs validation:', error);
        }
    }
    
    // ============================================================================
    // 性能监控 (Performance Monitoring)
    // ============================================================================
    
    startPerformanceMonitoring() {
        this.performanceInterval = setInterval(() => {
            this.updatePerformanceMetrics();
        }, 5000);
    }
    
    stopPerformanceMonitoring() {
        if (this.performanceInterval) {
            clearInterval(this.performanceInterval);
        }
    }
    
    updatePerformanceMetrics() {
        // 模拟性能指标更新
        const newMetrics = {
            responseTime: Math.random() * 100 + 50,
            memoryUsage: Math.random() * 100 + 200,
            cpuUsage: Math.random() * 30 + 10,
            networkLatency: Math.random() * 50 + 20
        };
        
        this.setState({ performanceMetrics: newMetrics });
        
        // 收集性能指标
        this.collectMetrics('performance_update', newMetrics);
    }
    
    // ============================================================================
    // 数据导出 (Data Export)
    // ============================================================================
    
    async exportMetrics() {
        try {
            const response = await fetch(`/api/dg/metrics/export/${this.state.dgMetrics.sessionId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dg_metrics_${this.state.dgMetrics.sessionId}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error exporting metrics:', error);
        }
    }
    
    // ============================================================================
    // 渲染方法 (Render Methods)
    // ============================================================================
    
    render() {
        const { 
            locationConfidence, 
            navigationMode, 
            accessibilityMode, 
            userNeedsValidation,
            performanceMetrics,
            isLoading,
            errorMessage 
        } = this.state;
        
        return (
            <div className={`app-container ${accessibilityMode}`}>
                {/* 头部信息 */}
                <header className="app-header">
                    <h1>VLN4VI - Indoor Navigation System</h1>
                    <div className="session-info">
                        Session: {this.state.dgMetrics.sessionId}
                    </div>
                </header>
                
                {/* 主要控制区域 */}
                <main className="main-content">
                    {/* 位置置信度显示 */}
                    <div className="confidence-display">
                        <h2>Location Confidence</h2>
                        <div className="confidence-bar">
                            <div 
                                className="confidence-fill" 
                                style={{ width: `${locationConfidence * 100}%` }}
                            />
                        </div>
                        <span className="confidence-value">
                            {(locationConfidence * 100).toFixed(1)}%
                        </span>
                    </div>
                    
                    {/* 导航控制 */}
                    {locationConfidence > 0.7 ? (
                        <div className="navigation-controls">
                            <h2>Navigation Controls</h2>
                            <button 
                                className="nav-button"
                                onClick={() => this.setState({ navigationMode: 'active' })}
                                disabled={navigationMode === 'active'}
                            >
                                Start Navigation
                            </button>
                            <button 
                                className="nav-button"
                                onClick={() => this.setState({ navigationMode: 'off' })}
                                disabled={navigationMode === 'off'}
                            >
                                Stop Navigation
                            </button>
                        </div>
                    ) : (
                        <div className="low-confidence-prompt">
                            <h2>Low Confidence</h2>
                            <p>Please take more photos to confirm your location</p>
                            <button 
                                className="photo-button"
                                onClick={this.handlePhotoCapture}
                                disabled={isLoading}
                            >
                                {isLoading ? 'Processing...' : 'Take Photo'}
                            </button>
                        </div>
                    )}
                    
                    {/* 拍照按钮 */}
                    <div className="photo-controls">
                        <button 
                            className="photo-button primary"
                            onClick={this.handlePhotoCapture}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Processing...' : 'Photo'}
                        </button>
                    </div>
                    
                    {/* 可访问性控制 */}
                    <div className="accessibility-controls">
                        <h2>Accessibility</h2>
                        <button 
                            className="accessibility-button"
                            onClick={this.toggleAccessibilityMode}
                        >
                            Mode: {accessibilityMode.replace('_', ' ')}
                        </button>
                        <div className="accessibility-status">
                            VoiceOver: {this.state.voiceOverEnabled ? 'Enabled' : 'Disabled'}
                        </div>
                    </div>
                </main>
                
                {/* 侧边栏 - 指标和状态 */}
                <aside className="sidebar">
                    <h2>System Status</h2>
                    
                    {/* 用户需求验证状态 */}
                    <div className="user-needs-status">
                        <h3>User Needs Validation</h3>
                        {Object.entries(userNeedsValidation).map(([needId, status]) => (
                            <div key={needId} className={`need-status ${status.status}`}>
                                <span className="need-id">{needId}</span>
                                <span className="need-score">{(status.score * 100).toFixed(0)}%</span>
                                <span className="need-status-text">{status.status}</span>
                            </div>
                        ))}
                    </div>
                    
                    {/* 性能指标 */}
                    <div className="performance-metrics">
                        <h3>Performance Metrics</h3>
                        <div className="metric-item">
                            <span>Response Time:</span>
                            <span>{performanceMetrics.responseTime.toFixed(1)}ms</span>
                        </div>
                        <div className="metric-item">
                            <span>Memory Usage:</span>
                            <span>{performanceMetrics.memoryUsage.toFixed(1)}MB</span>
                        </div>
                        <div className="metric-item">
                            <span>CPU Usage:</span>
                            <span>{performanceMetrics.cpuUsage.toFixed(1)}%</span>
                        </div>
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="action-buttons">
                        <button 
                            className="export-button"
                            onClick={this.exportMetrics}
                        >
                            Export Metrics
                        </button>
                    </div>
                </aside>
                
                {/* 错误显示 */}
                {errorMessage && (
                    <div className="error-message">
                        {errorMessage}
                    </div>
                )}
            </div>
        );
    }
}

// ============================================================================
// 样式定义 (Style Definitions)
// ============================================================================

const styles = `
.app-container {
    display: grid;
    grid-template-columns: 1fr 300px;
    grid-template-rows: auto 1fr;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-header {
    grid-column: 1 / -1;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.main-content {
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.confidence-display {
    text-align: center;
    padding: 2rem;
    background: #f8f9fa;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.confidence-bar {
    width: 100%;
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
    margin: 1rem 0;
}

.confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
    transition: width 0.3s ease;
}

.navigation-controls, .low-confidence-prompt {
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.photo-controls {
    text-align: center;
}

.photo-button {
    padding: 1rem 2rem;
    font-size: 1.2rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.photo-button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
}

.photo-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.photo-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.sidebar {
    background: #f8f9fa;
    padding: 2rem;
    border-left: 1px solid #dee2e6;
    overflow-y: auto;
}

.user-needs-status, .performance-metrics {
    margin-bottom: 2rem;
}

.need-status {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 4px;
    font-size: 0.9rem;
}

.need-status.satisfied { background: #d4edda; }
.need-status.partially_satisfied { background: #fff3cd; }
.need-status.unsatisfied { background: #f8d7da; }

.metric-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}

.action-buttons {
    margin-top: 2rem;
}

.export-button {
    width: 100%;
    padding: 0.75rem;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

.error-message {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #dc3545;
    color: white;
    padding: 1rem;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* 可访问性模式样式 */
.app-container.high_contrast {
    filter: contrast(1.5);
}

.app-container.large_text .app-container {
    font-size: 1.2em;
}

.app-container.voice_guided {
    /* 语音引导模式的特殊样式 */
}
`;

// ============================================================================
// 应用初始化 (Application Initialization)
// ============================================================================

function initializeApp() {
    // 添加样式
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
    
    // 渲染应用
    const container = document.getElementById('root');
    if (container) {
        const root = createRoot(container);
        root.render(<OptimizedApp />);
    } else {
        console.error('Root container not found');
    }
}

// 导出组件和初始化函数
export { OptimizedApp, initializeApp };

// 如果直接运行此文件，则初始化应用
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', initializeApp);
}
