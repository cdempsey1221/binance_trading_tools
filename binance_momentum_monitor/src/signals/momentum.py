"""
Momentum signal detection
"""

from typing import Optional

import pandas as pd

from src.core.types import MomentumSignal
from src.data.rest_client import BinanceRestClient
from src.monitoring.logger import get_logger

logger = get_logger('momentum_detector')

class MomentumDetector:
    """Detects momentum signals based on volume and price"""
    
    def __init__(
        self,
        rest_client: BinanceRestClient,
        timeframe: str,
        lookback_periods: int,
        volume_window_hours: int,
        volume_threshold: float,
        price_threshold: float
    ):
        """
        Initialize momentum detector
        
        Args:
            rest_client: REST API client
            timeframe: Candlestick timeframe
            lookback_periods: Number of periods to look back
            volume_window_hours: Hours to look back for volume calculation            volume_threshold: Volume spike threshold percentage
            price_threshold: Price change threshold percentage
        """
        self.rest_client = rest_client
        self.timeframe = timeframe
        self.lookback_periods = lookback_periods
        self.volume_window_hours = volume_window_hours
        self.volume_threshold = volume_threshold
        self.price_threshold = price_threshold
    
    def analyze_symbol(
        self,
        symbol: str
    ) -> Optional[MomentumSignal]:
        """
        Analyze a symbol for momentum signals
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            MomentumSignal if conditions met, None otherwise
        """
        logger.debug(
            'symbol_analysis_start',
            f'Starting analysis for {symbol}',
            data={
                'symbol': symbol,
                'volume_window_hours': self.volume_window_hours,
                'timeframe': self.timeframe
            }
        )
        
        # Calculate volume for configured window
        period_volume = self.rest_client.get_volume_for_period(
            symbol, 
            self.volume_window_hours
        )
        
        if period_volume is None:
                logger.debug(
                    'symbol_analysis_skip_volume',
                    f'Skipping {symbol} - no volume data available',
                    data={'symbol': symbol, 'reason': 'no_volume_data'}
                )
                return None
        
        logger.debug(
            'volume_data_retrieved',
            f'Volume data for {symbol}',
            data={
                'symbol': symbol,
                'period_volume': period_volume,
                'volume_window_hours': self.volume_window_hours
            }
        )
        
        # Convert to average hourly volume for threshold logic
        avg_hourly_volume = period_volume / self.volume_window_hours
        
        # Dynamic threshold based on liquidity (adjusted for hourly average)
        is_high_liquidity = bool(avg_hourly_volume > 1250)
        
        # Scaled from 10000/8hrs
        volume_threshold = (self.volume_threshold if is_high_liquidity else 250)
        
        logger.debug(
            'threshold_calculation',
            f'Volume threshold calculated for {symbol}',
            data={
                'symbol': symbol,
                'avg_hourly_volume': avg_hourly_volume,
                'volume_threshold': volume_threshold,
                'is_high_liquidity': is_high_liquidity
            }
        )
        
        # Calculate volume spike using same timeframe as volume window
        # For 8-hour window with 15-minute candles: 8 * 60 / 15 = 32 periods
        klines_needed = (self.volume_window_hours * 60) // 15  # 32 for 8 hours
        
        # Fetch candlestick data
        klines = self.rest_client.get_klines(
            symbol,
            self.timeframe,
            klines_needed + 1
        )
        
        if not klines:
            logger.debug(
                'symbol_analysis_skip_klines',
                f'Skipping {symbol} - no kline data available',
                data={
                    'symbol': symbol, 
                    'reason': 'no_klines_data',
                    'timeframe': self.timeframe,
                    'lookback_periods': self.lookback_periods
                }
            )
            return None
        
        logger.debug(
            'klines_data_retrieved',
            f'Retrieved {len(klines)} klines for {symbol}',
            data={
                'symbol': symbol,
                'klines_count': len(klines),
                'timeframe': self.timeframe,
                'lookback_periods': self.lookback_periods
            }
        )
        
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
        
        current_volume = float(df['volume'].iloc[-1])      # Latest 15-minute
        
        # Short-term spike (2-hour comparison)
        short_avg_volume = float(df['volume'].iloc[-9:-1].mean())  # Last 8 periods
        short_spike_pct = float((current_volume / short_avg_volume - 1) * 100)

        # Medium-term spike (if you fetched 33 klines)
        if len(df) >= 33:
            long_avg_volume = float(df['volume'].iloc[:-1].mean())  # 32 periods
            long_spike_pct = float((current_volume / long_avg_volume - 1) * 100)
        else:
            long_spike_pct = short_spike_pct
        
        # Use the short spike for detection (more sensitive)
        volume_spike_pct = short_spike_pct
        avg_volume = short_avg_volume
        
        # But log both for analysis
        logger.debug(
            'volume_spike_calculated',
            f'Volume spike calculated for {symbol}',
            data={
                'symbol': symbol,
                'short_spike_pct': float(short_spike_pct),  # 2-hour
                'long_spike_pct': float(long_spike_pct),    # 8-hour
                'current_volume': float(current_volume),
                'avg_volume': float(avg_volume),
                'long_avg_volume': float(long_avg_volume),
                'volume_threshold': volume_threshold
            }
        )
        
        # Calculate price change
        open_price = df['open'].iloc[-1]
        close_price = df['close'].iloc[-1]
        
        if open_price == 0:
            logger.debug(
                'symbol_analysis_skip_zero_price',
                f'Skipping {symbol} - zero open price',
                data={
                    'symbol': symbol,
                    'reason': 'zero_open_price',
                    'open_price': open_price
                }
            )
            return None
        
        price_change_pct = (close_price / open_price - 1) * 100
        
        logger.debug(
            'price_change_calculated',
            f'Price change calculated for {symbol}',
            data={
                'symbol': symbol,
                'open_price': float(open_price),
                'close_price': float(close_price),
                'price_change_pct': float(price_change_pct),
                'price_threshold': self.price_threshold
            }        )
        
        # Check both conditions
        volume_condition = bool(volume_spike_pct >= volume_threshold)
        price_condition = bool(price_change_pct >= self.price_threshold)
        
        logger.debug(
            'conditions_evaluated',
            f'Momentum conditions evaluated for {symbol}',
            data={
                'symbol': symbol,
                'volume_spike_pct': float(volume_spike_pct),
                'volume_threshold': volume_threshold,
                'volume_condition': volume_condition,
                'price_change_pct': float(price_change_pct),
                'price_threshold': self.price_threshold,
                'price_condition': price_condition,
                'both_conditions_met': volume_condition and price_condition
            }
        )
        
        if volume_condition and price_condition:            
            logger.info(
                'momentum_detected',
                f'Momentum signal for {symbol}',
                data={
                    'symbol': symbol,
                    'volume_spike_pct': float(volume_spike_pct),
                    'price_change_pct': float(price_change_pct),
                    'volume_threshold': volume_threshold,
                    'price_threshold': self.price_threshold,
                    'timeframe': self.timeframe
                }
            )
            
            return MomentumSignal(
                symbol=symbol,
                volume_spike_pct=float(volume_spike_pct),
                price_change_pct=float(price_change_pct),
                candle_timestamp=int(df['timestamp'].iloc[-1]),
                timeframe=self.timeframe
            )
        
        logger.debug(
            'symbol_analysis_no_signal',
            f'No momentum signal for {symbol} - conditions not met',
            data={
                'symbol': symbol,
                'volume_condition': volume_condition,
                'price_condition': price_condition,
                'volume_spike_pct': float(volume_spike_pct),
                'price_change_pct': float(price_change_pct)
            }
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
