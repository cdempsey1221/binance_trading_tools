"""
Momentum signal detection
"""

from typing import Optional

import pandas as pd

from ..core.types import MomentumSignal
from ..data.rest_client import BinanceRestClient
from ..monitoring.logger import get_logger


logger = get_logger('momentum_detector')


class MomentumDetector:
    """Detects momentum signals based on volume and price"""
    
    def __init__(
        self,
        rest_client: BinanceRestClient,
        timeframe: str,
        lookback_periods: int,
        volume_threshold: float,
        price_threshold: float
    ):
        """
        Initialize momentum detector
        
        Args:
            rest_client: REST API client
            timeframe: Candlestick timeframe
            lookback_periods: Number of periods to look back
            volume_threshold: Volume spike threshold percentage
            price_threshold: Price change threshold percentage
        """
        self.rest_client = rest_client
        self.timeframe = timeframe
        self.lookback_periods = lookback_periods
        self.volume_threshold = volume_threshold
        self.price_threshold = price_threshold
    
    def analyze_symbol(
        self,
        symbol: str,
        avg_24hr_volume: float
    ) -> Optional[MomentumSignal]:
        """
        Analyze a symbol for momentum signals
        
        Args:
            symbol: Trading pair symbol
            avg_24hr_volume: Average hourly volume over 24 hours
            
        Returns:
            MomentumSignal if conditions met, None otherwise
        """
        # Dynamic threshold based on liquidity
        volume_threshold = (
            self.volume_threshold
            if avg_24hr_volume > 10000
            else 250
        )
        
        # Fetch candlestick data
        klines = self.rest_client.get_klines(
            symbol,
            self.timeframe,
            self.lookback_periods + 1
        )
        
        if not klines:
            return None
        
        # Parse into DataFrame
        df = pd.DataFrame(
            klines,
            columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume',
                'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        )
        
        # Convert to numeric types
        df['volume'] = pd.to_numeric(df['volume'])
        df['open'] = pd.to_numeric(df['open'])
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculate volume spike
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]
        
        if avg_volume == 0:
            return None
        
        volume_spike_pct = (current_volume / avg_volume - 1) * 100
        
        # Calculate price change
        open_price = df['open'].iloc[-1]
        close_price = df['close'].iloc[-1]
        
        if open_price == 0:
            return None
        
        price_change_pct = (close_price / open_price - 1) * 100
        
        # Check both conditions
        volume_condition = volume_spike_pct >= volume_threshold
        price_condition = price_change_pct >= self.price_threshold
        
        if volume_condition and price_condition:
            logger.info(
                'momentum_detected',
                f'Momentum signal for {symbol}',
                data={
                    'symbol': symbol,
                    'volume_spike_pct': volume_spike_pct,
                    'price_change_pct': price_change_pct
                }
            )
            
            return MomentumSignal(
                symbol=symbol,
                volume_spike_pct=volume_spike_pct,
                price_change_pct=price_change_pct,
                candle_timestamp=int(df['timestamp'].iloc[-1]),
                timeframe=self.timeframe
            )
        
        return None
    
    def get_kline_dataframe(self, symbol: str, limit: int) -> Optional[pd.DataFrame]:
        """
        Get kline data as DataFrame
        
        Args:
            symbol: Trading pair symbol
            limit: Number of klines to fetch
            
        Returns:
            DataFrame with kline data or None
        """
        klines = self.rest_client.get_klines(symbol, self.timeframe, limit)
        
        if not klines:
            return None
        
        df = pd.DataFrame(
            klines,
            columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume',
                'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        )
        
        # Convert numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        
        return df
