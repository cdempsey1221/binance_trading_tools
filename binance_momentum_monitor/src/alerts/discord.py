"""
Discord webhook integration
"""

import requests
from typing import Optional

from ..core.types import MomentumSignal
from ..monitoring.logger import get_logger


logger = get_logger('discord')


class DiscordNotifier:
    """Handles Discord webhook notifications"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Discord notifier
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_alert(self, signal: MomentumSignal) -> bool:
        """
        Send momentum alert to Discord
        
        Args:
            signal: MomentumSignal containing alert data
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_alert(signal)
        
        logger.info(
            'sending_alert',
            f'Sending alert for {signal.symbol}',
            data={
                'symbol': signal.symbol,
                'volume_spike': signal.volume_spike_pct,
                'price_change': signal.price_change_pct
            }
        )
        
        payload = {"content": message}
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info('alert_sent', f'Alert sent successfully for {signal.symbol}')
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(
                'alert_send_failed',
                f'Failed to send alert for {signal.symbol}',
                data={'error': str(e)}
            )
            return False
    
    def _format_alert(self, signal: MomentumSignal) -> str:
        """
        Format momentum signal as Discord message
        
        Args:
            signal: MomentumSignal to format
            
        Returns:
            Formatted message string
        """
        message = (
            f"🚨 **MOMENTUM ALERT** 🚨\n"
            f"**{signal.symbol}**\n"
            f"Volume: +{signal.volume_spike_pct:.1f}%\n"
            f"Price: +{signal.price_change_pct:.1f}%\n"
            f"Timeframe: {signal.timeframe}"
        )
        
        # Add optional enrichment data
        if signal.volume_zscore is not None:
            message += f"\nVolume Z-Score: {signal.volume_zscore:.2f}"
        
        if signal.atr_normalized_return is not None:
            message += f"\nATR Normalized: {signal.atr_normalized_return:.2f}σ"
        
        if signal.signal_strength is not None:
            message += f"\nSignal Strength: {signal.signal_strength:.1f}/10"
        
        return message
    
    def send_enriched_alert(
        self,
        signal: MomentumSignal,
        context: Optional[dict] = None
    ) -> bool:
        """
        Send enriched alert with additional context
        
        Args:
            signal: MomentumSignal containing alert data
            context: Additional context data
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_enriched_alert(signal, context)
        
        logger.info(
            'sending_enriched_alert',
            f'Sending enriched alert for {signal.symbol}'
        )
        
        payload = {"content": message}
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info('enriched_alert_sent', f'Enriched alert sent for {signal.symbol}')
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(
                'enriched_alert_failed',
                f'Failed to send enriched alert for {signal.symbol}',
                data={'error': str(e)}
            )
            return False
    
    def _format_enriched_alert(
        self,
        signal: MomentumSignal,
        context: Optional[dict] = None
    ) -> str:
        """
        Format enriched alert with context
        
        Args:
            signal: MomentumSignal to format
            context: Additional context data
            
        Returns:
            Formatted enriched message
        """
        message = (
            f"🚨 **MOMENTUM ALERT**: {signal.symbol}\n\n"
            f"📊 **Signal Strength**: {signal.signal_strength or 0:.1f}/10\n"
            f"📈 **Price Move**: +{signal.price_change_pct:.1f}%"
        )
        
        if signal.atr_normalized_return:
            message += f" ({signal.atr_normalized_return:.1f}σ normalized)"
        
        message += f"\n📊 **Volume**: {signal.volume_spike_pct:.0f}% vs avg"
        
        if signal.volume_zscore:
            message += f" (z-score: {signal.volume_zscore:.1f})"
        
        if context:
            message += "\n\n📋 **Context**:"
            
            if 'market_regime' in context:
                message += f"\n- Market: {context['market_regime']}"
            
            if 'correlated_symbols' in context:
                message += f"\n- Correlation: {', '.join(context['correlated_symbols'][:3])}"
            
            if 'spread_pct' in context:
                message += f"\n- Spread: {context['spread_pct']:.2f}%"
            
            if 'win_rate' in context:
                message += f"\n- Win Rate: {context['win_rate']:.0f}% (last {context.get('sample_size', 50)})"
        
        return message
