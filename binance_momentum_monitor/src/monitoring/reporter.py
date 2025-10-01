"""
Simple console reporter for API performance metrics
"""

import time
from typing import Dict, List

from .metrics import APIMetrics, get_metrics_collector
from .logger import get_logger


logger = get_logger('api_reporter')


class SimpleAPIReporter:
    """Basic console reporter for API metrics"""
    
    def __init__(self):
        self.last_report_time = time.time()
        
    def report_current_stats(self) -> None:
        """Print current API performance statistics to console"""
        try:
            collector = get_metrics_collector()
            stats = collector.get_basic_stats()
            
            print("\n" + "="*60)
            print("📊 API PERFORMANCE SUMMARY")
            print("="*60)
            print(f"Total Calls:    {stats['total_calls']}")
            print(f"Success Rate:   {stats['success_rate']:.1f}%")
            print(f"Avg Latency:    {stats['avg_duration_ms']:.0f}ms")
            print(f"Error Rate:     {stats['error_rate']:.1f}%")
            print(f"Buffer Usage:   {stats['buffer_usage']}")
            print("="*60)
            
            # Show recent endpoint activity
            self._show_endpoint_breakdown()
            
        except Exception as e:
            logger.error('report_generation_failed', f'Failed to generate API report: {e}')
    
    def _show_endpoint_breakdown(self) -> None:
        """Show breakdown by endpoint for recent calls"""
        try:
            collector = get_metrics_collector()
            recent_metrics = collector.get_recent_metrics(100)
            
            if not recent_metrics:
                print("No recent API calls to report")
                return
            
            # Count calls by endpoint
            endpoint_counts = {}
            endpoint_avg_latency = {}
            endpoint_errors = {}
            
            for metric in recent_metrics:
                endpoint = metric.endpoint
                
                # Count calls
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
                
                # Track latency
                if endpoint not in endpoint_avg_latency:
                    endpoint_avg_latency[endpoint] = []
                endpoint_avg_latency[endpoint].append(metric.duration_ms)
                
                # Count errors
                if not metric.success:
                    endpoint_errors[endpoint] = endpoint_errors.get(endpoint, 0) + 1
            
            print("\n📋 ENDPOINT BREAKDOWN (Last 100 calls):")
            print("-" * 60)
            
            for endpoint in sorted(endpoint_counts.keys()):
                count = endpoint_counts[endpoint]
                avg_ms = sum(endpoint_avg_latency[endpoint]) / len(endpoint_avg_latency[endpoint])
                errors = endpoint_errors.get(endpoint, 0)
                success_rate = ((count - errors) / count) * 100 if count > 0 else 0
                
                print(f"{endpoint:20} | {count:3d} calls | {avg_ms:5.0f}ms avg | {success_rate:5.1f}% success")
            
        except Exception as e:
            logger.debug('endpoint_breakdown_failed', f'Failed to generate endpoint breakdown: {e}')
    
    def log_performance_summary(self) -> None:
        """Log a structured performance summary"""
        try:
            collector = get_metrics_collector()
            stats = collector.get_basic_stats()
            
            if stats['total_calls'] > 0:
                logger.info(
                    'api_performance_summary',
                    f"API Performance: {stats['total_calls']} calls, "
                    f"{stats['success_rate']:.1f}% success, "
                    f"{stats['avg_duration_ms']:.0f}ms avg latency",
                    data=stats
                )
        except Exception as e:
            logger.error('summary_logging_failed', f'Failed to log performance summary: {e}')


# Global reporter instance
_reporter = None


def get_api_reporter() -> SimpleAPIReporter:
    """Get the global API reporter instance"""
    global _reporter
    if _reporter is None:
        _reporter = SimpleAPIReporter()
    return _reporter


def print_api_stats():
    """Convenience function to print current API statistics"""
    reporter = get_api_reporter()
    reporter.report_current_stats()


def log_api_summary():
    """Convenience function to log API performance summary"""
    reporter = get_api_reporter()
    reporter.log_performance_summary()
