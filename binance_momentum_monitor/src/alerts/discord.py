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
                f'Failed to send alert for {signal.symbol}',                data={'error': str(e)}
            )
            return False
    
    def _format_alert(self, signal: MomentumSignal) -> str:
        """
        Format momentum signal as comprehensive Discord message
        
        Args:
            signal: MomentumSignal to format
            
        Returns:
            Formatted message string with multi-timeframe analysis
        """
        # Header with symbol and momentum score
        score_display = f"{signal.momentum_score}/10" if signal.momentum_score is not None else "N/A"
        stage_emoji = {
            'early': '🌱',
            'developing': '📈',
            'mature': '🔥',
            'none': '⚪'
        }
        stage = signal.momentum_stage or 'none'
        
        message = (
            f"🚨 **MOMENTUM ALERT** 🚨\n"
            f"**{signal.symbol}** @ ${signal.current_price:.6f}\n"
            f"{stage_emoji.get(stage, '⚪')} Stage: **{stage.upper()}** | Score: **{score_display}**\n"
            f"───────────────────────────\n"
        )
        
        # Multi-timeframe price analysis
        message += "**📊 PRICE MOVEMENT**\n"
        if signal.price_change_current_bar is not None:
            sign = "+" if signal.price_change_current_bar >= 0 else ""
            message += f"Current Bar (15m): {sign}{signal.price_change_current_bar:.2f}%\n"
        
        if signal.price_change_1hour is not None and signal.price_change_1hour != 0:
            sign = "+" if signal.price_change_1hour >= 0 else ""
            message += f"1-Hour Trend: {sign}{signal.price_change_1hour:.2f}%\n"
        
        if signal.price_change_2hour is not None and signal.price_change_2hour != 0:
            sign = "+" if signal.price_change_2hour >= 0 else ""
            message += f"2-Hour Trend: {sign}{signal.price_change_2hour:.2f}%\n"
        
        if signal.price_change_4hour is not None and signal.price_change_4hour != 0:
            sign = "+" if signal.price_change_4hour >= 0 else ""
            message += f"4-Hour Trend: {sign}{signal.price_change_4hour:.2f}%\n"
        
        # Volume metrics
        message += "\n**📈 VOLUME METRICS**\n"
        sign = "+" if signal.volume_spike_pct >= 0 else ""
        message += f"Volume Spike: {sign}{signal.volume_spike_pct:.1f}%\n"
        
        if signal.volume_building is not None:
            building_status = "✅ Building" if signal.volume_building else "❌ Not Building"
            message += f"Volume Status: {building_status}\n"
        
        if signal.volume_zscore is not None:
            message += f"Volume Z-Score: {signal.volume_zscore:.2f}σ\n"
        
        # TBQR buying pressure analysis
        if signal.tbqr_current is not None:
            tbqr_pct = signal.tbqr_current * 100
            
            # Determine buying pressure interpretation with emoji
            if signal.tbqr_current > 0.60:
                pressure_emoji = "🟢🟢"
                pressure_label = "Very Strong"
            elif signal.tbqr_current > 0.55:
                pressure_emoji = "🟢"
                pressure_label = "Strong"
            elif signal.tbqr_current > 0.50:
                pressure_emoji = "🔵"
                pressure_label = "Moderate"
            elif signal.tbqr_current > 0.45:
                pressure_emoji = "🟡"
                pressure_label = "Weak"
            else:
                pressure_emoji = "🔴"
                pressure_label = "Bearish"
            
            message += f"Buy Pressure (TQBR): {pressure_emoji} **{pressure_label}** ({tbqr_pct:.1f}%)\n"
            
            # Add Z-score if available (statistical significance)
            if signal.tbqr_zscore is not None:
                if signal.tbqr_zscore > 2.0:
                    zscore_note = "⚡ Highly significant"
                elif signal.tbqr_zscore > 1.0:
                    zscore_note = "Notable"
                elif signal.tbqr_zscore < -1.0:
                    zscore_note = "Below average"
                else:
                    zscore_note = "Normal"
                message += f"  └─ Significance: {signal.tbqr_zscore:.1f}σ ({zscore_note})\n"
            
            # Add delta/acceleration if available
            if signal.tbqr_delta is not None and abs(signal.tbqr_delta) > 0.02:
                delta_sign = "+" if signal.tbqr_delta > 0 else ""
                accel_emoji = "📈" if signal.tbqr_delta > 0 else "📉"
                message += f"  └─ Acceleration: {accel_emoji} {delta_sign}{signal.tbqr_delta:.3f}\n"
        
        # Signal quality indicators
        message += "\n**✨ SIGNAL QUALITY**\n"
        
        if signal.trends_aligned is not None:
            trend_status = "✅ Aligned" if signal.trends_aligned else "⚠️ Conflicting"
            message += f"Trend Alignment: {trend_status}\n"
        
        if signal.volume_price_sync is not None:
            sync_status = "✅ Synchronized" if signal.volume_price_sync else "⚠️ Diverging"
            message += f"Vol-Price Sync: {sync_status}\n"
        
        if signal.volatility is not None:
            message += f"Volatility (ATR): {signal.volatility:.2f}%\n"
        
        # EMA trend analysis (Stage 1: data collection)
        if signal.ema_21_daily is not None:
            message += "\n**🎯 EMA TREND (Daily)**\n"
            
            # EMA values
            message += f"21 EMA: ${signal.ema_21_daily:.6f}\n"
            if signal.ema_50_daily is not None:
                message += f"50 EMA: ${signal.ema_50_daily:.6f}\n"
            
            # Price position and trend bias
            if signal.price_vs_ema_21:
                position_emoji = "🟢" if signal.price_vs_ema_21 == "above" else "🔴" if signal.price_vs_ema_21 == "below" else "⚪"
                position_text = signal.price_vs_ema_21.upper()
                message += f"Position: {position_emoji} **{position_text}** 21 EMA\n"
            
            if signal.ema_trend_bias and signal.ema_trend_bias != "neutral":
                bias_emoji = "📈" if signal.ema_trend_bias == "bullish" else "📉" if signal.ema_trend_bias == "bearish" else "➡️"
                bias_text = signal.ema_trend_bias.upper()
                message += f"Bias: {bias_emoji} **{bias_text}**"
                
                # Add percentage distance from EMA
                if signal.current_price and signal.ema_21_daily:
                    distance_pct = ((signal.current_price - signal.ema_21_daily) / signal.ema_21_daily) * 100
                    sign = "+" if distance_pct > 0 else ""
                    message += f" ({sign}{distance_pct:.2f}% from EMA)"
                
                message += "\n"
        
        # Timeframe footer
        message += f"\n⏰ Timeframe: **{signal.timeframe}**"
        message += f"───────────────────────────\n\n"
        
        # Add optional legacy enrichment data
        if signal.atr_normalized_return is not None:
            message += f"\nATR Normalized: {signal.atr_normalized_return:.2f}σ"
        
        if signal.signal_strength is not None:
            message += f"\nLegacy Strength: {signal.signal_strength:.1f}/10"
        
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
