#!/usr/bin/env python3
"""
Orchestrator Server Manager - Centralized server management for Claude Code subagents
Ensures single shared Research Monitor server and provides endpoint to subagents
"""

import os
import sys
import time
import signal
import subprocess
import requests
import json
from pathlib import Path
from typing import Optional, Dict
from research_api import ResearchAPI, ResearchAPIError

class OrchestratorServerManager:
    """Manages the shared Research Monitor server for all subagents"""
    
    def __init__(self, port: int = 5558):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.api_key = os.environ.get('RESEARCH_MONITOR_API_KEY', 'test-key')
        self.server_process = None
        self.server_pid_file = Path('.research_monitor_pid')
        
    def is_server_running(self) -> bool:
        """Check if Research Monitor server is already running"""
        try:
            response = requests.get(f"{self.base_url}/api/server/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def start_server(self) -> Dict:
        """Start Research Monitor server if not already running"""
        if self.is_server_running():
            print(f"Research Monitor already running on port {self.port}")
            return {
                'status': 'already_running',
                'endpoint': self.base_url,
                'message': 'Server was already running'
            }
        
        # Start server process
        try:
            os.chdir('research_monitor')
            env = os.environ.copy()
            env['RESEARCH_MONITOR_PORT'] = str(self.port)
            env['RESEARCH_MONITOR_API_KEY'] = self.api_key
            
            # Start server in background
            self.server_process = subprocess.Popen([
                sys.executable, 'app_v2.py'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Save PID for cleanup
            with open(self.server_pid_file, 'w') as f:
                f.write(str(self.server_process.pid))
            
            # Wait for server to be ready
            max_retries = 30  # 15 seconds
            for _ in range(max_retries):
                if self.is_server_running():
                    print(f"Research Monitor started successfully on port {self.port}")
                    return {
                        'status': 'started',
                        'endpoint': self.base_url,
                        'pid': self.server_process.pid,
                        'message': f'Server started on port {self.port}'
                    }
                time.sleep(0.5)
            
            # Server failed to start
            self.cleanup_server()
            return {
                'status': 'failed',
                'message': 'Server failed to start within timeout period'
            }
            
        except Exception as e:
            self.cleanup_server()
            return {
                'status': 'error',
                'message': f'Failed to start server: {str(e)}'
            }
        finally:
            os.chdir('..')
    
    def stop_server(self) -> Dict:
        """Gracefully stop the Research Monitor server"""
        if not self.is_server_running():
            self.cleanup_server()
            return {
                'status': 'not_running',
                'message': 'Server was not running'
            }
        
        try:
            # Try graceful shutdown first
            api = ResearchAPI(self.base_url, self.api_key)
            response = api.shutdown_server()
            
            # Wait for shutdown
            for _ in range(20):  # 10 seconds
                if not self.is_server_running():
                    self.cleanup_server()
                    print("Research Monitor stopped gracefully")
                    return {
                        'status': 'stopped',
                        'message': 'Server stopped gracefully'
                    }
                time.sleep(0.5)
            
            # Force kill if graceful shutdown failed
            return self.force_stop_server()
            
        except Exception as e:
            print(f"Error during graceful shutdown: {e}, trying force stop")
            return self.force_stop_server()
    
    def force_stop_server(self) -> Dict:
        """Force stop the server process"""
        try:
            # Try to kill by PID file
            if self.server_pid_file.exists():
                with open(self.server_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already dead
            
            # Kill any process on the port
            subprocess.run(['pkill', '-f', f'RESEARCH_MONITOR_PORT={self.port}'], 
                         capture_output=True)
            
            self.cleanup_server()
            return {
                'status': 'force_stopped',
                'message': 'Server force stopped'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to force stop server: {str(e)}'
            }
    
    def cleanup_server(self):
        """Clean up server process and PID file"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
            self.server_process = None
        
        if self.server_pid_file.exists():
            self.server_pid_file.unlink()
    
    def restart_server(self) -> Dict:
        """Restart the Research Monitor server"""
        stop_result = self.stop_server()
        time.sleep(2)  # Brief pause between stop and start
        start_result = self.start_server()
        
        return {
            'status': 'restarted',
            'stop_result': stop_result,
            'start_result': start_result,
            'endpoint': self.base_url if start_result['status'] in ['started', 'already_running'] else None
        }
    
    def get_server_endpoint(self) -> Optional[str]:
        """Get the server endpoint URL for subagents"""
        if self.is_server_running():
            return self.base_url
        return None
    
    def ensure_server_running(self) -> str:
        """Ensure server is running and return endpoint URL"""
        if not self.is_server_running():
            result = self.start_server()
            if result['status'] not in ['started', 'already_running']:
                raise RuntimeError(f"Failed to start server: {result['message']}")
        
        return self.base_url

# ===== ORCHESTRATOR FUNCTIONS =====

def start_shared_server(port: int = 5558) -> Dict:
    """Start the shared Research Monitor server for all subagents"""
    manager = OrchestratorServerManager(port)
    return manager.start_server()

def stop_shared_server(port: int = 5558) -> Dict:
    """Stop the shared Research Monitor server"""
    manager = OrchestratorServerManager(port)
    return manager.stop_server()

def get_shared_server_endpoint(port: int = 5558) -> Optional[str]:
    """Get the shared server endpoint for subagents"""
    manager = OrchestratorServerManager(port)
    return manager.get_server_endpoint()

def ensure_shared_server(port: int = 5558) -> str:
    """Ensure shared server is running and return endpoint"""
    manager = OrchestratorServerManager(port)
    return manager.ensure_server_running()

# ===== COMMAND LINE INTERFACE =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Orchestrator Server Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'health'], 
                      help='Action to perform')
    parser.add_argument('--port', type=int, default=5558, 
                      help='Port number (default: 5558)')
    
    args = parser.parse_args()
    manager = OrchestratorServerManager(args.port)
    
    if args.action == 'start':
        result = manager.start_server()
        print(json.dumps(result, indent=2))
    
    elif args.action == 'stop':
        result = manager.stop_server()
        print(json.dumps(result, indent=2))
    
    elif args.action == 'restart':
        result = manager.restart_server()
        print(json.dumps(result, indent=2))
    
    elif args.action == 'status':
        running = manager.is_server_running()
        print(json.dumps({
            'running': running,
            'endpoint': manager.base_url if running else None,
            'port': args.port
        }, indent=2))
    
    elif args.action == 'health':
        if manager.is_server_running():
            try:
                api = ResearchAPI(manager.base_url, manager.api_key)
                health = api.health_check()
                print(json.dumps(health, indent=2))
            except Exception as e:
                print(json.dumps({'error': str(e)}, indent=2))
        else:
            print(json.dumps({'error': 'Server not running'}, indent=2))