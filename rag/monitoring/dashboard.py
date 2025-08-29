"""
Monitoring Dashboard for RAG System

Web-based dashboard for real-time monitoring of research quality metrics.
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime
from typing import Optional


class MonitoringDashboard:
    """
    Web dashboard for RAG monitoring.
    """
    
    def __init__(self, monitor, port: int = 8002):
        """
        Initialize dashboard.
        
        Args:
            monitor: RAGResearchMonitor instance
            port: Port to serve dashboard
        """
        self.monitor = monitor
        self.port = port
        self.app = FastAPI(title="RAG Research Monitor")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.get("/")
        async def dashboard():
            """Serve dashboard HTML."""
            return HTMLResponse(self._get_dashboard_html())
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get current metrics."""
            return self.monitor.get_metrics_summary()
        
        @self.app.get("/api/research_quality")
        async def get_research_quality():
            """Get research quality metrics."""
            return self.monitor.get_research_quality_stats()
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get active alerts."""
            return self.monitor.check_research_quality_alerts()
        
        @self.app.get("/api/coverage_gaps")
        async def get_coverage_gaps():
            """Get coverage gap analysis."""
            return self.monitor.analyze_coverage_gaps()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            try:
                while True:
                    # Send updates every second
                    await websocket.send_json({
                        'timestamp': datetime.now().isoformat(),
                        'metrics': self.monitor.get_metrics_summary()
                    })
                    await asyncio.sleep(1)
            except:
                pass
    
    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>RAG Research Monitor</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .status-good { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-error { color: #f44336; }
        .alert-box {
            background: #fff3cd;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 RAG Research Quality Monitor</h1>
        <p>Real-time monitoring of retrieval quality, consistency, and completeness</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Recall Rate</div>
            <div class="metric-value" id="recall">--</div>
            <div class="progress-bar">
                <div class="progress-fill" id="recall-bar"></div>
            </div>
            <small>Target: >95%</small>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Consistency</div>
            <div class="metric-value" id="consistency">--</div>
            <div class="progress-bar">
                <div class="progress-fill" id="consistency-bar"></div>
            </div>
            <small>Target: >99%</small>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Completeness</div>
            <div class="metric-value" id="completeness">--</div>
            <div class="progress-bar">
                <div class="progress-fill" id="completeness-bar"></div>
            </div>
            <small>Target: >98%</small>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value" id="response-time">--</div>
            <small>Target: <5.0s</small>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Quality Assessment</div>
            <div class="metric-value" id="quality">--</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Queries/Min</div>
            <div class="metric-value" id="qpm">--</div>
        </div>
    </div>
    
    <div class="metric-card">
        <h3>⚠️ Active Alerts</h3>
        <div id="alerts"></div>
    </div>
    
    <div class="metric-card">
        <h3>📊 Coverage Analysis</h3>
        <div id="coverage"></div>
    </div>

    <script>
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                // Update research metrics
                const research = data.research_quality.research_metrics;
                if (research) {
                    updateMetric('recall', research.avg_recall, 0.95);
                    updateMetric('consistency', research.consistency_rate, 0.99);
                    updateMetric('completeness', research.avg_completeness, 0.98);
                }
                
                // Update performance metrics
                const perf = data.research_quality.performance_metrics;
                if (perf) {
                    document.getElementById('response-time').textContent = 
                        perf.avg_response_time.toFixed(2) + 's';
                    document.getElementById('qpm').textContent = 
                        perf.queries_per_minute.toFixed(1);
                }
                
                // Update quality assessment
                const quality = data.research_quality.quality_assessment;
                if (quality) {
                    const elem = document.getElementById('quality');
                    elem.textContent = quality;
                    elem.className = 'metric-value ' + 
                        (quality === 'EXCELLENT' ? 'status-good' :
                         quality === 'GOOD' ? 'status-warning' : 'status-error');
                }
                
                // Update alerts
                updateAlerts(data.alerts);
                
                // Update coverage
                updateCoverage(data.coverage_gaps);
                
            } catch (error) {
                console.error('Error updating metrics:', error);
            }
        }
        
        function updateMetric(id, value, target) {
            const valueElem = document.getElementById(id);
            const barElem = document.getElementById(id + '-bar');
            
            valueElem.textContent = (value * 100).toFixed(1) + '%';
            valueElem.className = 'metric-value ' + 
                (value >= target ? 'status-good' : 
                 value >= target * 0.95 ? 'status-warning' : 'status-error');
            
            if (barElem) {
                barElem.style.width = (value * 100) + '%';
            }
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p>No active alerts ✅</p>';
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div class="alert-box">
                    <strong>${alert.level}:</strong> ${alert.message}
                </div>
            `).join('');
        }
        
        function updateCoverage(coverage) {
            const container = document.getElementById('coverage');
            if (!coverage) {
                container.innerHTML = '<p>No coverage data available</p>';
                return;
            }
            
            container.innerHTML = `
                <p>Coverage Score: ${(coverage.coverage_score * 100).toFixed(1)}%</p>
                <p>Low Result Queries: ${coverage.low_result_queries ? coverage.low_result_queries.length : 0}</p>
                <p>Failed Queries: ${coverage.failed_queries ? coverage.failed_queries.length : 0}</p>
                ${coverage.recommendations ? '<p>Recommendations:</p><ul>' + 
                    coverage.recommendations.map(r => `<li>${r}</li>`).join('') + '</ul>' : ''}
            `;
        }
        
        // Update every 2 seconds
        setInterval(updateMetrics, 2000);
        updateMetrics(); // Initial update
    </script>
</body>
</html>
"""
    
    def run(self):
        """Start dashboard server."""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)