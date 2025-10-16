#!/usr/bin/env python3
"""
Research Monitor Server Manager
Handles starting, stopping, and restarting the research monitor server
"""

import os
import signal
import subprocess
import time
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
import json

from config import (
    get_research_monitor_port,
    get_research_monitor_url,
    SERVER_PID_FILE,
    SERVER_LOG_FILE
)

class ServerManager:
    """Manages the Research Monitor server lifecycle"""
    
    def __init__(self):
        self.port = get_research_monitor_port()
        self.url = get_research_monitor_url()
        self.pid_file = Path(SERVER_PID_FILE)
        self.log_file = Path(SERVER_LOG_FILE)
        self.server_script = Path(__file__).parent / "app_v2.py"
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current server status"""
        pid = self._get_server_pid()
        port_in_use = self._is_port_in_use()
        
        if pid and self._is_process_running(pid):
            status = "running"
            process_info = self._get_process_info(pid)
        elif port_in_use:
            status = "port_conflict"
            process_info = None
        else:
            status = "stopped"
            process_info = None
        
        return {
            "status": status,
            "pid": pid,
            "port": self.port,
            "url": self.url,
            "process_info": process_info,
            "pid_file": str(self.pid_file),
            "log_file": str(self.log_file)
        }
    
    def start_server(self, background: bool = True) -> Dict[str, Any]:
        """Start the research monitor server"""
        status = self.get_server_status()
        
        if status["status"] == "running":
            return {"success": False, "message": f"Server already running (PID: {status['pid']})"}
        
        if status["status"] == "port_conflict":
            return {"success": False, "message": f"Port {self.port} is in use by another process"}
        
        # Kill any orphaned processes on the port
        self._kill_processes_on_port()
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env['RESEARCH_MONITOR_PORT'] = str(self.port)
            
            if background:
                # Start server in background
                with open(self.log_file, 'w') as log:
                    process = subprocess.Popen(
                        ['python3', str(self.server_script)],
                        cwd=str(self.server_script.parent),
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True
                    )
                
                # Write PID file
                self.pid_file.write_text(str(process.pid))
                
                # Wait a moment to check if server started successfully
                time.sleep(2)
                
                if self._is_process_running(process.pid) and self._is_port_in_use():
                    return {
                        "success": True,
                        "message": f"Server started successfully (PID: {process.pid})",
                        "pid": process.pid,
                        "url": self.url,
                        "log_file": str(self.log_file)
                    }
                else:
                    return {
                        "success": False,
                        "message": "Server failed to start. Check log file.",
                        "log_file": str(self.log_file)
                    }
            else:
                # Start server in foreground
                return {
                    "success": True,
                    "message": "Starting server in foreground...",
                    "command": f"cd {self.server_script.parent} && python3 {self.server_script}"
                }
                
        except Exception as e:
            return {"success": False, "message": f"Failed to start server: {e}"}
    
    def stop_server(self, force: bool = False) -> Dict[str, Any]:
        """Stop the research monitor server"""
        status = self.get_server_status()
        
        if status["status"] == "stopped":
            return {"success": True, "message": "Server is not running"}
        
        pid = status["pid"]
        if pid:
            try:
                if force:
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGTERM)
                
                # Wait for process to stop
                for _ in range(10):  # Wait up to 10 seconds
                    if not self._is_process_running(pid):
                        break
                    time.sleep(1)
                
                if self._is_process_running(pid):
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
                
                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                
                return {"success": True, "message": f"Server stopped (PID: {pid})"}
                
            except ProcessLookupError:
                # Process already dead
                if self.pid_file.exists():
                    self.pid_file.unlink()
                return {"success": True, "message": "Server was not running"}
            except Exception as e:
                return {"success": False, "message": f"Failed to stop server: {e}"}
        
        # Kill any processes on the port
        killed = self._kill_processes_on_port()
        if killed:
            return {"success": True, "message": f"Killed {killed} processes on port {self.port}"}
        
        return {"success": True, "message": "No server processes found"}
    
    def restart_server(self) -> Dict[str, Any]:
        """Restart the research monitor server"""
        stop_result = self.stop_server()
        if not stop_result["success"]:
            return stop_result
        
        # Wait a moment before starting
        time.sleep(1)
        
        start_result = self.start_server()
        if start_result["success"]:
            return {
                "success": True,
                "message": f"Server restarted successfully. {start_result['message']}",
                "pid": start_result.get("pid"),
                "url": self.url
            }
        else:
            return start_result
    
    def get_server_logs(self, lines: int = 50) -> str:
        """Get recent server logs"""
        if not self.log_file.exists():
            return "No log file found"
        
        try:
            with open(self.log_file, 'r') as f:
                log_lines = f.readlines()
                return ''.join(log_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def _get_server_pid(self) -> Optional[int]:
        """Get server PID from PID file"""
        if not self.pid_file.exists():
            return None
        
        try:
            pid = int(self.pid_file.read_text().strip())
            return pid if self._is_process_running(pid) else None
        except (ValueError, OSError):
            return None
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running"""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def _is_port_in_use(self) -> bool:
        """Check if the configured port is in use"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', self.port))
                return result == 0
        except Exception:
            return False
    
    def _get_process_info(self, pid: int) -> Dict[str, Any]:
        """Get information about a process"""
        try:
            process = psutil.Process(pid)
            return {
                "pid": pid,
                "name": process.name(),
                "cmdline": " ".join(process.cmdline()),
                "status": process.status(),
                "create_time": process.create_time(),
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent()
            }
        except Exception:
            return {"pid": pid, "error": "Cannot get process info"}
    
    def _kill_processes_on_port(self) -> int:
        """Kill all processes using the configured port"""
        killed = 0
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == self.port and conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        process.terminate()
                        killed += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception:
            pass
        
        return killed

def main():
    """CLI interface for server management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Monitor Server Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "logs"],
                       help="Action to perform")
    parser.add_argument("--force", action="store_true", help="Force kill server")
    parser.add_argument("--foreground", action="store_true", help="Start server in foreground")
    parser.add_argument("--lines", type=int, default=50, help="Number of log lines to show")
    
    args = parser.parse_args()
    
    manager = ServerManager()
    
    if args.action == "status":
        status = manager.get_server_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == "start":
        result = manager.start_server(background=not args.foreground)
        print(json.dumps(result, indent=2))
    
    elif args.action == "stop":
        result = manager.stop_server(force=args.force)
        print(json.dumps(result, indent=2))
    
    elif args.action == "restart":
        result = manager.restart_server()
        print(json.dumps(result, indent=2))
    
    elif args.action == "logs":
        logs = manager.get_server_logs(lines=args.lines)
        print(logs)

if __name__ == "__main__":
    main()