"""
Main entry point for Binance Momentum Monitor
"""

import asyncio
import os
from pathlib import Path

from src.core.config import load_config
from src.core.universe import SymbolUniverse
from src.data.rest_client import BinanceRestClient
from src.signals.momentum import MomentumDetector
from src.alerts.manager import AlertManager
from src.alerts.discord import DiscordNotifier
from src.alerts.deduplication import AlertDeduplicationDB
from src.monitoring.logger import get_logger


logger = get_logger('main')


class MomentumScanner:
    """Main scanner orchestrating the alert system"""
    
    def __init__(self, config):
        """
        Initialize momentum scanner
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize components
        self.rest_client = BinanceRestClient(
            rate_limit=config.data.rest.rate_limit
        )
        
        self.universe = SymbolUniverse(
            rest_client=self.rest_client,
            min_hourly_volume=config.universe.min_hourly_volume,
            cache_ttl=config.universe.cache_ttl
        )
        
        self.momentum_detector = MomentumDetector(
            rest_client=self.rest_client,
            timeframe=config.signals.timeframe,
            lookback_periods=config.signals.lookback_periods,
            volume_threshold=config.signals.price_change_threshold * 100,  # Convert to percentage
            price_threshold=config.signals.price_change_threshold * 100
        )
        
        discord_notifier = DiscordNotifier(
            webhook_url=config.alerts.discord_webhook_url
        )
        
        dedup_db = AlertDeduplicationDB()
        
        self.alert_manager = AlertManager(
            discord_notifier=discord_notifier,
            dedup_db=dedup_db,
            cooldown_minutes=config.alerts.cooldown_minutes
        )
        
        self.symbols = []
    
    def initialize_symbols(self) -> None:
        """Fetch and cache liquid perpetual symbols"""
        self.symbols = self.universe.get_liquid_perpetuals()
        logger.info(
            'symbols_initialized',
            f'Initialized with {len(self.symbols)} symbols',
            data={'symbol_count': len(self.symbols)}
        )
    
    async def scan_symbol(self, symbol: str) -> None:
        """
        Scan a single symbol for momentum signals
        
        Args:
            symbol: Symbol to scan
        """
        # Get current 24hr volume for dynamic thresholding
        symbol_info = self.universe.get_symbol_info(symbol)
        if not symbol_info:
            return
        
        avg_hourly_volume = symbol_info.avg_hourly_volume
        
        # Analyze for momentum
        signal = self.momentum_detector.analyze_symbol(
            symbol,
            avg_hourly_volume
        )
        
        if signal:
            # Send alert if conditions met
            self.alert_manager.send_alert(signal)
    
    async def run_scan_cycle(self) -> None:
        """Execute one complete scan of all symbols"""
        logger.info(
            'scan_cycle_start',
            f'Starting scan cycle for {len(self.symbols)} symbols...'
        )
        
        for symbol in self.symbols:
            await self.scan_symbol(symbol)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        logger.info('scan_cycle_complete', 'Scan cycle completed')
    
    async def run(self) -> None:
        """Main execution loop"""
        self.initialize_symbols()
        
        logger.info(
            'scanner_started',
            f'Starting momentum scanner with {self.config.signals.timeframe} timeframe',
            data={
                'timeframe': self.config.signals.timeframe,
                'lookback_periods': self.config.signals.lookback_periods,
                'symbol_count': len(self.symbols)
            }
        )
        
        # Initial cleanup
        self.alert_manager.cleanup_old_alerts()
        
        scan_interval = 300  # 5 minutes
        
        while True:
            try:
                await self.run_scan_cycle()
            except Exception as e:
                logger.error(
                    'scan_cycle_error',
                    'Error in scan cycle',
                    data={'error': str(e)},
                    exc_info=True
                )
            
            logger.info(
                'waiting',
                f'Waiting {scan_interval}s until next scan...'
            )
            await asyncio.sleep(scan_interval)


async def main() -> None:
    """Application entry point"""
    # Load configuration
    config_path = os.getenv('CONFIG_PATH')
    if config_path:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(
                'config_not_found',
                f'Config file not found at {config_path}, using environment variables'
            )
            config_path = None
    else:
        # Try default location
        default_config = Path(__file__).parent / 'config' / 'default.yaml'
        if default_config.exists():
            config_path = str(default_config)
        else:
            config_path = None
    
    try:
        config = load_config(config_path)
        logger.info(
            'config_loaded',
            f'Configuration loaded successfully',
            data={
                'source': 'file' if config_path else 'environment',
                'timeframe': config.signals.timeframe
            }
        )
    except Exception as e:
        logger.error(
            'config_load_failed',
            'Failed to load configuration',
            data={'error': str(e)},
            exc_info=True
        )
        return
    
    # Create and run scanner
    scanner = MomentumScanner(config)
    await scanner.run()


if __name__ == "__main__":
    asyncio.run(main())
