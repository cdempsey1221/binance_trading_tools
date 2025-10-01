"""
API instrumentation decorator for tracking REST API call performance
"""

import time
import sys
from functools import wraps
from typing import Callable, Any, Dict, Optional

from .metrics import APIMetrics, get_metrics_collector
from .logger import get_logger


logger = get_logger('api_instrumentation')


def api_call(
    endpoint: str,
    track_parameters: Optional[list] = None,
    exclude_parameters: Optional[list] = None,
    log_calls: bool = True
):
    """
    Decorator to instrument API calls with performance tracking
    
    Args:
        endpoint: Human-readable endpoint name (e.g., "get_klines")
        track_parameters: List of parameter names to track in metrics
        exclude_parameters: List of parameter names to exclude from tracking
        log_calls: Whether to log individual calls (default: True)
    
    Returns:
        Decorated function with API call instrumentation
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Record start time
            start_time = time.time()
            
            # Initialize metrics record
            metric = APIMetrics(
                endpoint=endpoint,
                timestamp=start_time,
                duration_ms=0.0,
                success=False
            )
            
            # Extract and sanitize parameters
            if track_parameters:
                try:
                    # Combine args and kwargs for parameter extraction
                    func_args = {}
                    
                    # Get function signature for parameter names
                    import inspect
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Extract tracked parameters
                    for param_name in track_parameters:
                        if param_name in bound_args.arguments:
                            value = bound_args.arguments[param_name]
                            # Convert to string for storage, handle special cases
                            if isinstance(value, (str, int, float, bool)):
                                func_args[param_name] = value
                            else:
                                func_args[param_name] = str(value)
                    
                    # Remove excluded parameters
                    if exclude_parameters:
                        for param_name in exclude_parameters:
                            func_args.pop(param_name, None)
                    
                    metric.parameters = func_args
                    
                except Exception as e:
                    # Don't fail the API call if parameter extraction fails
                    logger.debug(f'parameter_extraction_failed', f'Failed to extract parameters for {endpoint}: {e}')
            
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Calculate response time
                end_time = time.time()
                metric.duration_ms = (end_time - start_time) * 1000
                metric.success = True
                
                # Try to extract response size if result is a list/dict
                try:
                    if isinstance(result, list):
                        metric.response_size = len(result)
                    elif isinstance(result, dict):
                        metric.response_size = len(str(result))
                except:
                    pass
                
                # Log successful call
                if log_calls:
                    logger.debug(
                        'api_call_success',
                        f'{endpoint}() -> {metric.duration_ms:.0f}ms',
                        data={
                            'endpoint': endpoint,
                            'duration_ms': metric.duration_ms,
                            'parameters': metric.parameters,
                            'response_size': metric.response_size
                        }
                    )
                
                return result
                
            except Exception as e:
                # Calculate response time even for errors
                end_time = time.time()
                metric.duration_ms = (end_time - start_time) * 1000
                metric.success = False
                metric.error_type = type(e).__name__
                metric.error_message = str(e)
                
                # Extract HTTP status code if available
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    metric.status_code = e.response.status_code
                
                # Log failed call
                if log_calls:
                    logger.warning(
                        'api_call_failed',
                        f'{endpoint}() failed after {metric.duration_ms:.0f}ms: {metric.error_type}',
                        data={
                            'endpoint': endpoint,
                            'duration_ms': metric.duration_ms,
                            'error_type': metric.error_type,
                            'error_message': metric.error_message,
                            'status_code': metric.status_code,
                            'parameters': metric.parameters
                        }
                    )
                
                # Re-raise the original exception
                raise
                
            finally:
                # Always record the metric, regardless of success/failure
                try:
                    collector = get_metrics_collector()
                    collector.record_metric(metric)
                except Exception as metrics_error:
                    # Don't fail the API call if metrics recording fails
                    logger.error(
                        'metrics_recording_failed',
                        f'Failed to record metrics for {endpoint}: {metrics_error}'
                    )
        
        return wrapper
    return decorator


def get_api_stats() -> Dict[str, Any]:
    """
    Get current API performance statistics
    
    Returns:
        Dictionary with API performance metrics
    """
    try:
        collector = get_metrics_collector()
        return collector.get_basic_stats()
    except Exception as e:
        logger.error('stats_retrieval_failed', f'Failed to retrieve API stats: {e}')
        return {
            'error': 'Failed to retrieve stats',
            'total_calls': 0,
            'success_rate': 0.0,
            'avg_duration_ms': 0.0,
            'error_rate': 0.0
        }


def log_api_summary():
    """Log a summary of API performance metrics"""
    try:
        stats = get_api_stats()
        collector = get_metrics_collector()
        
        if stats['total_calls'] > 0:
            logger.info(
                'api_performance_summary',
                f"API Calls: {stats['total_calls']} | "
                f"Success: {stats['success_rate']:.1f}% | "
                f"Avg Latency: {stats['avg_duration_ms']:.0f}ms | "
                f"Buffer: {stats['buffer_usage']}",
                data=stats
            )
        else:
            logger.info('api_performance_summary', 'No API calls recorded yet')
            
    except Exception as e:
        logger.error('summary_logging_failed', f'Failed to log API summary: {e}')
