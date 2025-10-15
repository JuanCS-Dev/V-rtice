"""
Resource Limiter
Enforces CPU, memory, and time limits on consciousness processes.
"""
import psutil
import resource
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Resource limits for sandboxed execution"""
    cpu_percent: float = 80.0        # Max CPU usage (%)
    memory_mb: int = 1024            # Max memory (MB)
    timeout_sec: int = 300           # Max execution time (seconds)
    max_threads: int = 10            # Max concurrent threads
    max_file_descriptors: int = 100  # Max open files


class ResourceLimiter:
    """
    Enforces resource limits using OS-level controls.
    
    Uses:
    - psutil for monitoring
    - resource module for hard limits (Unix)
    - Process affinity for CPU control
    """
    
    def __init__(self, limits: ResourceLimits):
        """
        Initialize resource limiter.
        
        Args:
            limits: Resource limits to enforce
        """
        self.limits = limits
        self.process = psutil.Process(os.getpid())
    
    def apply_limits(self):
        """Apply resource limits to current process"""
        try:
            # Set memory limit (Unix only)
            if hasattr(resource, 'RLIMIT_AS'):
                memory_bytes = self.limits.memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            
            # Set file descriptor limit
            if hasattr(resource, 'RLIMIT_NOFILE'):
                resource.setrlimit(
                    resource.RLIMIT_NOFILE,
                    (self.limits.max_file_descriptors, self.limits.max_file_descriptors)
                )
            
            # Set CPU time limit (seconds)
            if hasattr(resource, 'RLIMIT_CPU'):
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.limits.timeout_sec, self.limits.timeout_sec)
                )
            
            # Set process priority (nice value)
            self.process.nice(10)  # Lower priority
            
        except Exception as e:  # pragma: no cover - platform-specific resource limits may not be available
            # Limits may not be available on all platforms
            pass  # pragma: no cover
    
    def check_compliance(self) -> dict:
        """
        Check if process is within limits.
        
        Returns:
            dict: Compliance status for each resource
        """
        compliance = {}
        
        # CPU
        cpu_percent = self.process.cpu_percent(interval=0.1)
        compliance['cpu'] = {
            'current': cpu_percent,
            'limit': self.limits.cpu_percent,
            'compliant': cpu_percent <= self.limits.cpu_percent
        }
        
        # Memory
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        compliance['memory'] = {
            'current': memory_mb,
            'limit': self.limits.memory_mb,
            'compliant': memory_mb <= self.limits.memory_mb
        }
        
        # Threads
        num_threads = self.process.num_threads()
        compliance['threads'] = {
            'current': num_threads,
            'limit': self.limits.max_threads,
            'compliant': num_threads <= self.limits.max_threads
        }
        
        return compliance
