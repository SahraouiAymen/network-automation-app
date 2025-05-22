import paramiko
import re
import time
import socket
from typing import Dict, Any

class RouterMonitorError(Exception):
    """Base exception for monitoring errors"""
    pass

class SSHRouterMonitor:
    def __init__(self, host: str, username: str, password: str):
        self.host = host  # Accepts both IPs and hostnames
        self.username = username
        self.password = password
        self.ssh = None
        self.channel = None
        self.connected = False

    def connect(self) -> bool:
        """Handle both IP addresses and hostnames with proper DNS resolution"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                timeout=15,
                look_for_keys=False,
                allow_agent=False
            )
            self.channel = self.ssh.invoke_shell()
            self._wait_for_prompt()
            self._exec_command("terminal length 0\n")
            self.connected = True
            return True
        except socket.gaierror as e:
            raise RouterMonitorError(f"DNS resolution failed for '{self.host}'") from e
        except paramiko.AuthenticationException:
            raise RouterMonitorError("Authentication failed") from None
        except Exception as e:
            raise RouterMonitorError(f"Connection failed: {str(e)}") from e

    def _wait_for_prompt(self, timeout: int = 10):
        """Wait for router prompt to appear"""
        end_time = time.time() + timeout
        output = ""
        while time.time() < end_time:
            if self.channel.recv_ready():
                output += self.channel.recv(4096).decode('utf-8', 'ignore')
                if '#' in output or '>' in output:
                    return
            time.sleep(0.1)
        raise RouterMonitorError("Prompt not detected - check credentials")

    def _exec_command(self, command: str, timeout: int = 5) -> str:
        """Execute command and return cleaned output"""
        try:
            self.channel.send(command)
            return self._read_until_prompt(timeout)
        except Exception as e:
            raise RouterMonitorError(f"Command failed: {str(e)}") from e

    def _read_until_prompt(self, timeout: int) -> str:
        """Read output until router prompt appears"""
        end_time = time.time() + timeout
        output = []
        while time.time() < end_time:
            if self.channel.recv_ready():
                data = self.channel.recv(4096).decode('utf-8', 'ignore')
                output.append(data)
                if any(prompt in data for prompt in ('#', '>')):
                    break
            time.sleep(0.1)
        return ''.join(output).replace('\r', '')

    def _parse_cpu(self, output: str) -> float:
        """Parse CPU usage from various router outputs"""
        patterns = [
            r"CPU utilization for five seconds: (\d+%)/.*?",
            r"CPU Total.*?(\d+)%",
            r"Processor load:\s+(\d+)%",
            r"CPU Load \d+ minutes:\s+(\d+)%"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                try:
                    return float(match.group(1).replace('%', ''))
                except (ValueError, IndexError):
                    continue
        raise RouterMonitorError("CPU data not found in output")

    def _parse_memory(self, output: str) -> float:
        """Parse memory usage with unit conversion"""
        patterns = [
            (r"Processor\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", 3),  # Cisco IOS
            (r"(\d+)K\s+(\d+)K\s+(\d+)K", 3),  # Memory in KB
            (r"(\d+)M\s+(\d+)M\s+(\d+)M", 3),  # Memory in MB
        ]

        for pattern, groups in patterns:
            match = re.search(pattern, output)
            if match:
                try:
                    if groups == 3:
                        total = int(match.group(1))
                        used = int(match.group(2))
                        return (used / total) * 100
                except (ValueError, ZeroDivisionError) as e:
                    raise RouterMonitorError("Invalid memory values") from e
        raise RouterMonitorError("Memory data not found in output")

    def _parse_uptime(self, output: str) -> str:
        """Parse uptime from various router formats"""
        patterns = [
            r"uptime is (.+)",
            r"System uptime:\s+(.+)",
            r"Uptime:\s+(.+)",
            r"Router uptime:\s+(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return self._format_uptime(match.group(1))
        return "N/A"

    def _format_uptime(self, raw_uptime: str) -> str:
        """Normalize uptime format"""
        replacements = [
            (r"(\d+) years?", r"\1y"),
            (r"(\d+) weeks?", r"\1w"),
            (r"(\d+) days?", r"\1d"),
            (r"(\d+) hours?", r"\1h"),
            (r"(\d+) minutes?", r"\1m")
        ]
        for pattern, replacement in replacements:
            raw_uptime = re.sub(pattern, replacement, raw_uptime)
        return raw_uptime.replace(",", "").strip()

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics including uptime"""
        if not self.connected:
            raise RouterMonitorError("Not connected to router")

        try:
            cpu_output = self._exec_command("show processes cpu\n", timeout=7)
            mem_output = self._exec_command("show memory statistics\n", timeout=7)
            uptime_output = self._exec_command("show version | include uptime\n", timeout=5)
            
            return {
                'cpu': self._parse_cpu(cpu_output),
                'memory': self._parse_memory(mem_output),
                'uptime': self._parse_uptime(uptime_output)
            }
        except Exception as e:
            raise RouterMonitorError(f"Failed to get stats: {str(e)}") from e

    def disconnect(self):
        """Clean up connections"""
        try:
            if self.channel:
                self.channel.close()
            if self.ssh:
                self.ssh.close()
        except Exception:
            pass
        self.connected = False

def get_router_stats(host: str, username: str, password: str) -> Dict[str, Any]:
    """Retrieve router statistics with comprehensive error handling"""
    monitor = SSHRouterMonitor(host, username, password)
    try:
        monitor.connect()
        return monitor.get_stats()
    except RouterMonitorError as e:
        return {'error': str(e), 'cpu': None, 'memory': None, 'uptime': "N/A"}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'cpu': None, 'memory': None, 'uptime': "N/A"}
    finally:
        monitor.disconnect()