"""
Alert manager with cooldown and deduplication
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from .deduplication import AlertDeduplicationDB
from .discord import DiscordNotifier
from ..core.types import MomentumSignal
from ..monitoring.logger import get_logger


logger = get_logger('alert_manager')


class AlertManager:
    """Manages alert cooldowns, deduplication, and delivery"""
    
    def __init__(
        self,
        discord_notifier: DiscordNotifier,
        dedup_db: AlertDeduplicationDB,
        cooldown_minutes: int
    ):
        """
        Initialize alert manager
        
        Args:
            discord_notifier: Discord notification handler
            dedup_db: Deduplication database
            cooldown_minutes: Cooldown period in minutes
        """
        self.notifier = discord_notifier
        self.dedup_db = dedup_db
        self.cooldown_minutes = cooldown_minutes
        
        # In-memory cooldown tracking
        self.last_alert_times: Dict[str, datetime] = {}
    
    def can_alert(self, symbol: str, timeframe: str, bar_close_time: int) -> bool:
        """
        Check if an alert can be sent
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe of the signal
            bar_close_time: Bar close timestamp
            
        Returns:
            True if alert can be sent, False otherwise
        """
        # Check database deduplication (exact bar)
        if self.dedup_db.alert_exists(symbol, timeframe, bar_close_time):
            logger.debug(
                'alert_deduplicated',
                f'Alert already sent for {symbol} at {bar_close_time}'
            )
            return False
        
        # Check in-memory cooldown
        key = f"{symbol}:{timeframe}"
        if key in self.last_alert_times:
            time_since_last = datetime.now() - self.last_alert_times[key]
            if time_since_last < timedelta(minutes=self.cooldown_minutes):
                logger.debug(
                    'alert_cooldown',
                    f'Cooldown active for {symbol}',
                    data={
                        'time_since_last': time_since_last.total_seconds(),
                        'cooldown_minutes': self.cooldown_minutes
                    }
                )
                return False
        
        return True
    
    def send_alert(self, signal: MomentumSignal, context: Optional[dict] = None) -> bool:
        """
        Send alert if conditions are met
        
        Args:
            signal: MomentumSignal to alert
            context: Optional context data for enrichment
            
        Returns:
            True if alert was sent, False otherwise
        """
        # Check if we can alert
        if not self.can_alert(signal.symbol, signal.timeframe, signal.candle_timestamp):
            return False
        
        # Send notification
        if context:
            success = self.notifier.send_enriched_alert(signal, context)
        else:
            success = self.notifier.send_alert(signal)
        
        if success:
            self._record_alert(signal)
            logger.info(
                'alert_delivered',
                f'Alert sent for {signal.symbol}',
                data={
                    'symbol': signal.symbol,
                    'timeframe': signal.timeframe,
                    'bar_close_time': signal.candle_timestamp
                }
            )
        
        return success
    
    def _record_alert(self, signal: MomentumSignal) -> None:
        """
        Record that an alert was sent
        
        Args:
            signal: MomentumSignal that was alerted
        """
        # Create signature
        signature = f"{signal.symbol}:{signal.timeframe}:{signal.candle_timestamp}"
        
        # Store in database
        self.dedup_db.store_alert(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            bar_close_time=signal.candle_timestamp,
            signature=signature
        )
        
        # Update in-memory cache
        key = f"{signal.symbol}:{signal.timeframe}"
        self.last_alert_times[key] = datetime.now()
    
    def cleanup_old_alerts(self, days: int = 7) -> None:
        """
        Clean up old alert records
        
        Args:
            days: Remove alerts older than this many days
        """
        logger.info('cleaning_old_alerts', f'Removing alerts older than {days} days')
        self.dedup_db.cleanup_old(days)
        logger.info('cleanup_complete', 'Old alerts cleaned up')
