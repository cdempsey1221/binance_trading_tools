"""
Core metrics collection infrastructure for API instrumentation
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque
from threading import Lock


@dataclass
class APIMetrics:
    """Individual API call metrics record"""
    endpoint: str
    timestamp: float
    duration_ms: float
    success: bool
    status_code: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    request_size: int = 0
    response_size: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe collector for API metrics with bounded storage"""
    
    def __init__(self, buffer_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            buffer_size: Maximum number of metrics to keep in memory
        """
        self.buffer_size = buffer_size
        self.metrics: deque = deque(maxlen=buffer_size)
        self.lock = Lock()
        
        # Quick stats for current session
        self.total_calls = 0
        self.total_errors = 0
        self.total_duration_ms = 0.0
        
    def record_metric(self, metric: APIMetrics) -> None:
        """
        Record a new API metric
        
        Args:
            metric: APIMetrics instance to record
        """
        with self.lock:
            self.metrics.append(metric)
            
            # Update running totals
            self.total_calls += 1
            self.total_duration_ms += metric.duration_ms
            
            if not metric.success:
                self.total_errors += 1
    
    def get_recent_metrics(self, count: int = 100) -> List[APIMetrics]:
        """
        Get the most recent metrics
        
        Args:
            count: Number of recent metrics to return
            
        Returns:
            List of recent APIMetrics, newest first
        """
        with self.lock:
            recent = list(self.metrics)[-count:]
            return list(reversed(recent))
    
    def get_metrics_by_endpoint(self, endpoint: str, count: int = 100) -> List[APIMetrics]:
        """
        Get recent metrics for a specific endpoint
        
        Args:
            endpoint: API endpoint name to filter by
            count: Maximum number of metrics to return
            
        Returns:
            List of matching APIMetrics
        """
        with self.lock:
            filtered = [m for m in self.metrics if m.endpoint == endpoint]
            return list(reversed(filtered[-count:]))
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics for the current session
        
        Returns:
            Dictionary with basic performance stats
        """
        with self.lock:
            if self.total_calls == 0:
                return {
                    'total_calls': 0,
                    'success_rate': 0.0,
                    'avg_duration_ms': 0.0,
                    'error_rate': 0.0
                }
            
            return {
                'total_calls': self.total_calls,
                'success_rate': ((self.total_calls - self.total_errors) / self.total_calls) * 100,
                'avg_duration_ms': self.total_duration_ms / self.total_calls,
                'error_rate': (self.total_errors / self.total_calls) * 100,
                'buffer_usage': f"{len(self.metrics)}/{self.buffer_size}"
            }
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics and reset counters"""
        with self.lock:
            self.metrics.clear()
            self.total_calls = 0
            self.total_errors = 0
            self.total_duration_ms = 0.0


# Global metrics collector instance
_metrics_collector = None
_collector_lock = Lock()


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance (singleton pattern)
    
    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        with _collector_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    
    return _metrics_collector


def init_metrics_collector(buffer_size: int = 1000) -> MetricsCollector:
    """
    Initialize the global metrics collector with custom settings
    
    Args:
        buffer_size: Maximum number of metrics to keep in memory
        
    Returns:
        Initialized MetricsCollector instance
    """
    global _metrics_collector
    
    with _collector_lock:
        _metrics_collector = MetricsCollector(buffer_size)
    
    return _metrics_collector
