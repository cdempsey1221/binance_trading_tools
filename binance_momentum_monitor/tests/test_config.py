"""
Tests for configuration management
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.core.config import Config, load_config


def test_config_from_env():
    """Test loading config from environment variables"""
    os.environ['DISCORD_WEBHOOK_URL'] = 'https://test.webhook.url'
    os.environ['TIMEFRAME'] = '5m'
    os.environ['LOOKBACK_PERIODS'] = '12'
    
    config = Config.from_env()
    
    assert config.alerts.discord_webhook_url == 'https://test.webhook.url'
    assert config.signals.timeframe == '5m'
    assert config.signals.lookback_periods == 12


def test_config_from_yaml():
    """Test loading config from YAML file"""
    yaml_content = """
universe:
  cache_ttl: 1800
  min_hourly_volume: 2000

signals:
  timeframe: "5m"
  lookback_periods: 10

alerts:
  cooldown_minutes: 15
  discord_webhook_url: "https://test.webhook.url"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        config = Config.from_yaml(temp_path)
        
        assert config.universe.cache_ttl == 1800
        assert config.universe.min_hourly_volume == 2000
        assert config.signals.timeframe == "5m"
        assert config.signals.lookback_periods == 10
        assert config.alerts.cooldown_minutes == 15
    finally:
        os.unlink(temp_path)


def test_config_env_interpolation():
    """Test environment variable interpolation in YAML"""
    os.environ['TEST_WEBHOOK_URL'] = 'https://env.webhook.url'
    
    yaml_content = """
alerts:
  discord_webhook_url: "${TEST_WEBHOOK_URL}"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        config = Config.from_yaml(temp_path)
        assert config.alerts.discord_webhook_url == 'https://env.webhook.url'
    finally:
        os.unlink(temp_path)


def test_config_validation():
    """Test configuration validation"""
    config = Config()
    
    # Should fail - no webhook URL
    with pytest.raises(ValueError, match="Discord webhook URL is required"):
        config.validate()
    
    # Should pass
    config.alerts.discord_webhook_url = 'https://test.url'
    config.validate()  # Should not raise
