"""
Momentum signal detection
"""

from typing import Optional

import pandas as pd
import numpy as np

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
            volume_window_hours: Hours to look back for volume calculation            
            volume_threshold: Volume spike threshold percentage
            price_threshold: Price change threshold percentage
        """
        self.rest_client = rest_client
        self.timeframe = timeframe
        self.lookback_periods = lookback_periods
        self.volume_window_hours = volume_window_hours
        self.volume_threshold = volume_threshold
        self.price_threshold = price_threshold
    
    def analyze_symbol(self, symbol: str) -> Optional[MomentumSignal]:
        """
        Analyze a symbol for momentum signals using multi-bar pattern detection
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
        
        # Check liquidity
        if not self._check_liquidity(symbol):
            return None
        
        # Get market data
        df = self._get_market_data(symbol)
        if df is None:
            return None
        
        # Analyze momentum components
        volume_analysis = self._analyze_volume_pattern(df)
        price_analysis = self._analyze_price_momentum(df)
        volatility = self._calculate_volatility(df)
        
        # Calculate momentum score
        momentum_score = self._calculate_momentum_score(
            volume_analysis,
            price_analysis,
            volatility
        )
        
        # Log the analysis
        self._log_momentum_analysis(symbol, volume_analysis, price_analysis, 
                                volatility, momentum_score)
        
        # Check if momentum signal conditions are met
        signal_threshold = 4
        if momentum_score >= signal_threshold and self._is_bullish(price_analysis):
            return self._create_momentum_signal(
                symbol, 
                df,
                volume_analysis,
                price_analysis
            )
        
        logger.debug(
            'symbol_analysis_no_signal',
            f'No momentum signal for {symbol} - score below threshold',
            data={
                'symbol': symbol,
                'momentum_score': momentum_score,
                'signal_threshold': signal_threshold
            }
        )
        
        return None

    def _check_liquidity(self, symbol: str) -> bool:
        """
        Check if symbol meets minimum liquidity requirements
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if liquid enough, False otherwise
        """
        period_volume = self.rest_client.get_volume_for_period(
            symbol, 
            self.volume_window_hours
        )
        
        avg_hourly_volume = period_volume / self.volume_window_hours
        min_liquidity_threshold = 1000  # $1000/hour minimum
        
        if avg_hourly_volume < min_liquidity_threshold:
            logger.debug(
                'symbol_analysis_skip_liquidity',
                f'Skipping {symbol} - insufficient liquidity',
                data={
                    'symbol': symbol,
                    'avg_hourly_volume': avg_hourly_volume,
                    'min_threshold': min_liquidity_threshold
                }
            )
            return False
        
        logger.debug(
            'liquidity_check_passed',
            f'Liquidity check passed for {symbol}',
            data={
                'symbol': symbol,
                'avg_hourly_volume': avg_hourly_volume
            }
        )
        
        return True

    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch and prepare market data for analysis
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            DataFrame with market data or None if insufficient data
        """
        klines_needed = 20
        klines = self.rest_client.get_klines(symbol, self.timeframe, klines_needed)
        
        if not klines or len(klines) < klines_needed:
            logger.debug(
                'symbol_analysis_skip_klines',
                f'Skipping {symbol} - insufficient kline data',
                data={
                    'symbol': symbol,
                    'reason': 'insufficient_klines',
                    'received': len(klines) if klines else 0,
                    'required': klines_needed
                }
            )
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
        numeric_cols = ['volume', 'open', 'high', 'low', 'close', 'quote_volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        
        return df

    def _analyze_volume_pattern(self, df: pd.DataFrame) -> dict:
        """
        Analyze volume patterns for momentum detection
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Dictionary with volume analysis results
        """
        last_4_volumes = df['volume'].iloc[-4:].values
        
        # Check if volume is building
        volume_building = all(
            last_4_volumes[i] > last_4_volumes[i-1] * 0.9  # 10% tolerance
            for i in range(1, len(last_4_volumes))
        )
        
        # Calculate volume spike
        recent_avg_volume = df['volume'].iloc[-9:-1].mean()
        current_volume = last_4_volumes[-1]
        volume_spike_pct = ((current_volume / recent_avg_volume) - 1) * 100 if recent_avg_volume > 0 else 0
        
        return {
            'building': bool(volume_building),
            'spike_pct': float(volume_spike_pct),
            'current': float(current_volume),
            'recent_avg': float(recent_avg_volume)
        }

    def _analyze_price_momentum(self, df: pd.DataFrame) -> dict:
        """
        Analyze price momentum over multiple bars
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Dictionary with price analysis results
        """
        last_4_closes = df['close'].iloc[-4:].values
        last_4_opens = df['open'].iloc[-4:].values
        
        # Price change over last 3 bars
        price_change_3bars = ((last_4_closes[-1] - last_4_opens[-3]) / last_4_opens[-3]) * 100
        
        # Current bar change
        current_bar_change = ((last_4_closes[-1] - last_4_opens[-1]) / last_4_opens[-1]) * 100
        
        # Check if price is trending up
        price_trending_up = last_4_closes[-1] > last_4_closes[-2] > last_4_closes[-3]
        
        return {
            'change_3bars': float(price_change_3bars),
            'current_bar': float(current_bar_change),
            'trending_up': bool(price_trending_up)
        }

    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """
        Calculate recent price volatility for dynamic thresholds
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Average volatility percentage
        """
        recent_changes = []
        for i in range(1, len(df)-1):
            change = abs((df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]) * 100
            recent_changes.append(change)
        
        return float(np.mean(recent_changes)) if recent_changes else 1.0

    def _calculate_momentum_score(self, volume_analysis: dict, price_analysis: dict, 
                                volatility: float) -> int:
        """
        Calculate composite momentum score from various factors
        
        Args:
            volume_analysis: Volume pattern analysis results
            price_analysis: Price momentum analysis results
            volatility: Recent market volatility
            
        Returns:
            Momentum score (higher = stronger signal)
        """
        score = 0
        
        # Volume factors
        if volume_analysis['building']:
            score += 2
        if volume_analysis['spike_pct'] > self.volume_threshold:
            score += 2
        if volume_analysis['spike_pct'] > self.volume_threshold * 2:
            score += 1
        
        # Price factors with volatility adjustment
        adjusted_price_threshold = max(self.price_threshold, volatility * 1.5)
        
        if price_analysis['change_3bars'] > adjusted_price_threshold:
            score += 2
        if price_analysis['current_bar'] > self.price_threshold:
            score += 1
        if price_analysis['trending_up']:
            score += 1
        
        return score

    def _is_bullish(self, price_analysis: dict) -> bool:
        """
        Check if the momentum is bullish (positive price movement)
        
        Args:
            price_analysis: Price momentum analysis results
            
        Returns:
            True if bullish momentum detected
        """
        return price_analysis['change_3bars'] > 0 or price_analysis['current_bar'] > 0

    def _log_momentum_analysis(self, symbol: str, volume_analysis: dict, 
                            price_analysis: dict, volatility: float, score: int):
        """
        Log detailed momentum analysis for debugging
        
        Args:
            symbol: Trading pair symbol
            volume_analysis: Volume pattern analysis results
            price_analysis: Price momentum analysis results
            volatility: Recent market volatility
            score: Calculated momentum score
        """
        logger.debug(
            'momentum_analysis',
            f'Momentum analysis for {symbol}',
            data={
                'symbol': symbol,
                'volume_building': bool(volume_analysis['building']),
                'volume_spike_pct': volume_analysis['spike_pct'],
                'price_change_3bars': price_analysis['change_3bars'],
                'current_bar_change': price_analysis['current_bar'],
                'price_trending_up': bool(price_analysis['trending_up']),
                'avg_volatility': volatility,
                'momentum_score': score,
                'current_volume': volume_analysis['current'],
                'recent_avg_volume': volume_analysis['recent_avg']
            }
        )

    def _create_momentum_signal(self, symbol: str, df: pd.DataFrame,
                            volume_analysis: dict, price_analysis: dict) -> MomentumSignal:
        """
        Create momentum signal object with relevant data
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with market data
            volume_analysis: Volume pattern analysis results
            price_analysis: Price momentum analysis results
            
        Returns:
            MomentumSignal object
        """
        best_price_change = max(price_analysis['change_3bars'], price_analysis['current_bar'])
        
        logger.info(
            'momentum_detected',
            f'Momentum signal for {symbol}',
            data={
                'symbol': symbol,
                'volume_spike_pct': volume_analysis['spike_pct'],
                'price_change_3bars': price_analysis['change_3bars'],
                'current_bar_change': price_analysis['current_bar'],
                'timeframe': self.timeframe
            }
        )
        
        return MomentumSignal(
            symbol=symbol,
            volume_spike_pct=volume_analysis['spike_pct'],
            price_change_pct=best_price_change,
            candle_timestamp=int(df['timestamp'].iloc[-1]),
            timeframe=self.timeframe
        )
    
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
