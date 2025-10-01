"""
Configuration management with YAML loading and environment variable interpolation
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dataclasses import dataclass, field


@dataclass
class UniverseConfig:
    """Configuration for symbol universe management"""
    cache_ttl: int = 3600
    min_hourly_volume: int = 1000


@dataclass
class WebSocketConfig:
    """WebSocket connection configuration"""
    max_streams_per_connection: int = 1024
    max_messages_per_second: int = 10
    reconnect_delay: int = 5


@dataclass
class RestConfig:
    """REST API configuration"""
    rate_limit: int = 1200  # per minute


@dataclass
class DataConfig:
    """Data layer configuration"""
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    rest: RestConfig = field(default_factory=RestConfig)


@dataclass
class SignalsConfig:
    """Signal detection configuration"""
    timeframe: str = "15m"
    lookback_periods: int = 8
    volume_zscore_threshold: float = 2.0
    price_change_threshold: float = 0.05
    use_atr_normalization: bool = True


@dataclass
class AlertsConfig:
    """Alert system configuration"""
    cooldown_minutes: int = 30
    discord_webhook_url: str = ""


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    metrics_interval: int = 60
    log_level: str = "INFO"


@dataclass
class Config:
    """Main configuration object"""
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    data: DataConfig = field(default_factory=DataConfig)
    signals: SignalsConfig = field(default_factory=SignalsConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Config':
        """
        Load configuration from YAML file with environment variable interpolation
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            Config instance
        """
        with open(yaml_path, 'r') as f:
            raw_content = f.read()
        
        # Interpolate environment variables
        interpolated_content = cls._interpolate_env_vars(raw_content)
        
        # Parse YAML
        data = yaml.safe_load(interpolated_content)
        
        return cls._from_dict(data)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Load configuration from environment variables (fallback)
        
        Returns:
            Config instance with environment variable overrides
        """
        return cls(
            universe=UniverseConfig(
                cache_ttl=int(os.getenv('UNIVERSE_CACHE_TTL', '3600')),
                min_hourly_volume=int(os.getenv('MIN_HOURLY_VOLUME', '1000'))
            ),
            data=DataConfig(
                websocket=WebSocketConfig(
                    max_streams_per_connection=int(os.getenv('WS_MAX_STREAMS', '1024')),
                    max_messages_per_second=int(os.getenv('WS_MAX_MSG_PER_SEC', '10')),
                    reconnect_delay=int(os.getenv('WS_RECONNECT_DELAY', '5'))
                ),
                rest=RestConfig(
                    rate_limit=int(os.getenv('REST_RATE_LIMIT', '1200'))
                )
            ),
            signals=SignalsConfig(
                timeframe=os.getenv('TIMEFRAME', '15m'),
                lookback_periods=int(os.getenv('LOOKBACK_PERIODS', '8')),
                volume_zscore_threshold=float(os.getenv('VOLUME_ZSCORE_THRESHOLD', '2.0')),
                price_change_threshold=float(os.getenv('PRICE_CHANGE_THRESHOLD', '0.05')),
                use_atr_normalization=os.getenv('USE_ATR_NORMALIZATION', 'true').lower() == 'true'
            ),
            alerts=AlertsConfig(
                cooldown_minutes=int(os.getenv('ALERT_COOLDOWN', '30')),
                discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL', '')
            ),
            monitoring=MonitoringConfig(
                metrics_interval=int(os.getenv('METRICS_INTERVAL', '60')),
                log_level=os.getenv('LOG_LEVEL', 'INFO')
            )
        )
    
    @staticmethod
    def _interpolate_env_vars(content: str) -> str:
        """
        Replace ${VAR_NAME} with environment variable values
        
        Args:
            content: Raw YAML content with ${VAR} placeholders
            
        Returns:
            Content with environment variables interpolated
        """
        pattern = re.compile(r'\$\{([^}]+)\}')
        
        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, '')
        
        return pattern.sub(replacer, content)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """
        Construct Config from dictionary
        
        Args:
            data: Dictionary from YAML parsing
            
        Returns:
            Config instance
        """
        universe_data = data.get('universe', {})
        universe = UniverseConfig(
            cache_ttl=universe_data.get('cache_ttl', 3600),
            min_hourly_volume=universe_data.get('min_hourly_volume', 1000)
        )
        
        data_config_data = data.get('data', {})
        ws_data = data_config_data.get('websocket', {})
        rest_data = data_config_data.get('rest', {})
        
        data_config = DataConfig(
            websocket=WebSocketConfig(
                max_streams_per_connection=ws_data.get('max_streams_per_connection', 1024),
                max_messages_per_second=ws_data.get('max_messages_per_second', 10),
                reconnect_delay=ws_data.get('reconnect_delay', 5)
            ),
            rest=RestConfig(
                rate_limit=rest_data.get('rate_limit', 1200)
            )
        )
        
        signals_data = data.get('signals', {})
        signals = SignalsConfig(
            timeframe=signals_data.get('timeframe', '15m'),
            lookback_periods=signals_data.get('lookback_periods', 8),
            volume_zscore_threshold=signals_data.get('volume_zscore_threshold', 2.0),
            price_change_threshold=signals_data.get('price_change_threshold', 0.05),
            use_atr_normalization=signals_data.get('use_atr_normalization', True)
        )
        
        alerts_data = data.get('alerts', {})
        alerts = AlertsConfig(
            cooldown_minutes=alerts_data.get('cooldown_minutes', 30),
            discord_webhook_url=alerts_data.get('discord_webhook_url', '')
        )
        
        monitoring_data = data.get('monitoring', {})
        monitoring = MonitoringConfig(
            metrics_interval=monitoring_data.get('metrics_interval', 60),
            log_level=monitoring_data.get('log_level', 'INFO')
        )
        
        return cls(
            universe=universe,
            data=data_config,
            signals=signals,
            alerts=alerts,
            monitoring=monitoring
        )
    
    def validate(self) -> None:
        """
        Validate configuration values
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.alerts.discord_webhook_url:
            raise ValueError("Discord webhook URL is required")
        
        if self.signals.lookback_periods < 2:
            raise ValueError("Lookback periods must be at least 2")
        
        if self.universe.min_hourly_volume < 0:
            raise ValueError("Min hourly volume must be non-negative")
        
        if self.alerts.cooldown_minutes < 0:
            raise ValueError("Alert cooldown must be non-negative")


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment
    
    Args:
        config_path: Optional path to YAML config file
        
    Returns:
        Validated Config instance
    """
    if config_path and Path(config_path).exists():
        config = Config.from_yaml(config_path)
    else:
        config = Config.from_env()
    
    config.validate()
    return config
