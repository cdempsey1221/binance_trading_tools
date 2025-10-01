"""
Tests for alert deduplication
"""

import os
import tempfile

import pytest

from src.alerts.deduplication import AlertDeduplicationDB


def test_alert_storage():
    """Test storing alerts in database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = AlertDeduplicationDB(db_path)
        
        # Store first alert
        result = db.store_alert('BTCUSDT', '15m', 1234567890, 'sig1')
        assert result is True
        
        # Try to store duplicate
        result = db.store_alert('BTCUSDT', '15m', 1234567890, 'sig1')
        assert result is False
    finally:
        os.unlink(db_path)


def test_alert_exists():
    """Test checking if alert exists"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = AlertDeduplicationDB(db_path)
        
        # Store alert
        db.store_alert('ETHUSDT', '15m', 1234567890, 'sig2')
        
        # Check existence
        assert db.alert_exists('ETHUSDT', '15m', 1234567890) is True
        assert db.alert_exists('ETHUSDT', '15m', 9999999999) is False
        assert db.alert_exists('BTCUSDT', '15m', 1234567890) is False
    finally:
        os.unlink(db_path)


def test_cleanup_old_alerts():
    """Test cleaning up old alerts"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = AlertDeduplicationDB(db_path)
        
        # Store alert
        db.store_alert('BTCUSDT', '15m', 1234567890, 'sig3')
        
        # Cleanup (won't remove recent alerts)
        db.cleanup_old(days=0)
        
        # Alert should still exist (created just now)
        # This is a basic test - in production you'd mock time
        assert db.alert_exists('BTCUSDT', '15m', 1234567890) is True
    finally:
        os.unlink(db_path)
