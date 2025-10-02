"""
Structured logging system with JSON output
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured JSON logger"""
    
    def __init__(self, component: str, log_level: str = "INFO"):
        self.component = component
        self.logger = logging.getLogger(component)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def _log(
        self,
        level: str,
        event: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Internal logging method"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'component': self.component,
            'event': event,
            'trace_id': trace_id or str(uuid.uuid4())[:8]
        }
        
        if message:
            log_data['message'] = message
        
        if data:
            log_data['data'] = data
        
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))
    
    def info(
        self,
        event: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Log info level message"""
        self._log('INFO', event, message, data, trace_id)
    
    def warning(
        self,
        event: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Log warning level message"""
        self._log('WARNING', event, message, data, trace_id)
    
    def error(
        self,
        event: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        exc_info: bool = False
    ) -> None:
        """Log error level message"""
        self._log('ERROR', event, message, data, trace_id)
        if exc_info:
            self.logger.exception("")
    
    def debug(
        self,
        event: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Log debug level message"""
        self._log('DEBUG', event, message, data, trace_id)


class StructuredFormatter(logging.Formatter):
    """Formatter that preserves JSON structure"""
    
    def format(self, record):
        return record.getMessage()


def get_logger(component: str, log_level: str = None) -> StructuredLogger:
    """
    Get a structured logger instance
    
    Args:
        component: Component name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        StructuredLogger instance
    """
    
    # Use environment variable if no log_level provided
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    return StructuredLogger(component, log_level)
