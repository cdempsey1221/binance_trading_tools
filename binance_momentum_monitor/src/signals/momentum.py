
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
        
        # Get market data (kline - candle data)
        df = self._get_market_data(symbol)
        if df is None:
            return None
        
        # Analyze momentum components
        volume_analysis = self._analyze_volume_pattern(df)
        price_analysis = self._analyze_price_momentum(df)
        volatility = self._calculate_volatility(df)
        
        # NEW: Calculate price acceleration
        acceleration = self._calculate_price_acceleration(df)
        
        # Calculate momentum score with acceleration
        momentum_score = self._calculate_momentum_score(
            volume_analysis,
            price_analysis,
            volatility,
            acceleration  # Pass acceleration to scoring
        )
        
        # Log the analysis (update to include acceleration)
        self._log_momentum_analysis(symbol, volume_analysis, price_analysis, 
                                volatility, momentum_score, acceleration)
        
        # Check if momentum signal conditions are met
        signal_threshold = 4
        
        # Volume requirement: Must have positive volume (not collapsing)
        if volume_analysis['spike_pct'] < -80:
            logger.debug(
                'symbol_analysis_no_signal',
                f'No momentum signal for {symbol} - extremely negative (more than -80%) declining volume trend',
                data={
                    'symbol': symbol,
                    'volume_spike_pct': volume_analysis['spike_pct'],
                    'reason': 'volume_requirement_not_met'
                }
            )
            return None
        
        # Trend alignment check: Short and long-term trends must agree
        change_1h = price_analysis.get('change_1hour', 0)
        change_2h = price_analysis.get('change_2hour', 0)
        change_4h = price_analysis.get('change_4hour', 0)
        
        # Check for major trend conflicts
        has_bullish = any([change_1h > 0.5, change_2h > 0.5, change_4h > 0.5])
        has_bearish = any([change_1h < -0.5, change_2h < -0.5, change_4h < -0.5])
        
        if has_bullish and has_bearish:
            logger.debug(
                'symbol_analysis_no_signal',
                f'No momentum signal for {symbol} - conflicting trends',
                data={
                    'symbol': symbol,
                    'change_1h': change_1h,
                    'change_2h': change_2h,
                    'change_4h': change_4h,
                    'reason': 'trend_conflict'
                }
            )
            return None
        
        if momentum_score >= signal_threshold:
            stage = self._identify_momentum_stage(volume_analysis, price_analysis)
            if stage in ['early', 'developing']:
                return self._create_momentum_signal(
                    symbol, 
                    df,
                    volume_analysis,
                    price_analysis,
                    volatility,
                    momentum_score,
                    acceleration,
                    stage
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
        
        # Short-term: Price change over last 3 bars (45 minutes)
        price_change_3bars = ((last_4_closes[-1] - last_4_opens[-3]) / last_4_opens[-3]) * 100
        
        # Short-term: Current bar change (15 minutes)
        current_bar_change = ((last_4_closes[-1] - last_4_opens[-1]) / last_4_opens[-1]) * 100
        
        # Check if price is trending up (sequential closes)
        price_trending_up = last_4_closes[-1] > last_4_closes[-2] > last_4_closes[-3]
        
        # Medium-term: 1-hour trend (4 × 15-min bars)
        if len(df) >= 5:
            price_change_1hour = ((df['close'].iloc[-1] - df['open'].iloc[-5]) / df['open'].iloc[-5]) * 100
        else:
            price_change_1hour = 0.0
        
        # Longer-term: 2-hour trend (8 × 15-min bars)
        if len(df) >= 9:
            price_change_2hour = ((df['close'].iloc[-1] - df['open'].iloc[-9]) / df['open'].iloc[-9]) * 100
        else:
            price_change_2hour = 0.0
        
        # Longer-term: 4-hour trend (16 × 15-min bars)
        if len(df) >= 17:
            price_change_4hour = ((df['close'].iloc[-1] - df['open'].iloc[-17]) / df['open'].iloc[-17]) * 100
        else:
            price_change_4hour = 0.0
        
        return {
            'change_3bars': float(price_change_3bars),
            'current_bar': float(current_bar_change),
            'trending_up': bool(price_trending_up),
            'change_1hour': float(price_change_1hour),
            'change_2hour': float(price_change_2hour),
            'change_4hour': float(price_change_4hour),
        }
        
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """
        Calculate recent price volatility using True Range method
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Average True Range as percentage of price
        """
        if len(df) < 2:
            return 0.5  # Conservative default
        
        # Calculate True Range for each candle
        # TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Convert to percentage of price
        atr_pct = (true_range / df['close']) * 100
        
        # Use last 10 candles for recent volatility
        recent_atr = atr_pct.iloc[-10:].mean()
        
        return float(recent_atr) if not pd.isna(recent_atr) else 0.5
    
    def _calculate_momentum_score(self, volume_analysis: dict, price_analysis: dict, 
                            volatility: float, acceleration: float) -> int:
        """
        Calculate composite momentum score focused on early momentum detection
        
        Philosophy: Catch momentum as it develops, not after it's mature
        Score range: 0-10 points (threshold: 4)
        """
        score = 0
        
        # ========================================
        # 1. VOLUME ANALYSIS (0-3 points)
        # ========================================
        
        if volume_analysis['building']:
            score += 2
            logger.debug('volume_building_detected', 'Sequential volume increase', 
                        data={'points': 2})
        
        if volume_analysis['spike_pct'] > self.volume_threshold * 2:  # >50%
            score += 1
        elif volume_analysis['spike_pct'] > self.volume_threshold:  # >25%
            score += 0.5
        
        # ========================================
        # 2. PRICE ACCELERATION (0-3 points)
        # ========================================
        
        # Use the calculated acceleration
        if acceleration > 100:  # Strong acceleration
            score += 3
            logger.debug('strong_acceleration_detected', 'Price momentum building rapidly',
                        data={'acceleration': acceleration, 'points': 3})
        elif acceleration > 50:  # Moderate acceleration
            score += 2
            logger.debug('moderate_acceleration_detected', 'Price momentum building',
                        data={'acceleration': acceleration, 'points': 2})
        elif acceleration > 25:  # Mild acceleration
            score += 1
            logger.debug('mild_acceleration_detected', 'Price starting to accelerate',
                        data={'acceleration': acceleration, 'points': 1})
        
        # ========================================
        # 3. TREND ALIGNMENT (0-2 points max)
        # ========================================
        
        if price_analysis.get('change_4hour', 0) > 2.5:
            score += 1
        elif price_analysis.get('change_2hour', 0) > 2.0:
            score += 1
        elif price_analysis.get('change_1hour', 0) > 1.0:
            score += 0.5
        
        if price_analysis['trending_up']:
            score += 1
        
        # ========================================
        # 4. MOMENTUM QUALITY (0-2 points)
        # ========================================
        
        # Breakout from consolidation
        if volatility < 0.5 and price_analysis['current_bar'] > self.price_threshold:
            score += 2
            logger.debug('breakout_detected', 'Low volatility breakout',
                        data={'volatility': volatility, 
                            'price_move': price_analysis['current_bar'], 
                            'points': 2})
        # Volume-price alignment
        elif (volume_analysis['spike_pct'] > 25 and 
            price_analysis['current_bar'] > 0.5):
            score += 1
            logger.debug('volume_price_alignment', 'Volume confirms price',
                        data={'volume_spike': volume_analysis['spike_pct'],
                            'price_move': price_analysis['current_bar'],
                            'points': 1})
        
        # Cap score at 10
        final_score = min(int(score), 10)
        
        logger.debug(
            'momentum_score_calculated',
            f'Total momentum score: {final_score}',
            data={
                'raw_score': score,
                'final_score': final_score,
                'acceleration': acceleration,
                'components': {
                    'volume_building': volume_analysis['building'],
                    'volume_spike': volume_analysis['spike_pct'],
                    'price_3bars': price_analysis['change_3bars'],
                    'current_bar': price_analysis['current_bar'],
                    'acceleration': acceleration
                }
            }
        )
        
        return final_score

    def _is_bullish(self, price_analysis: dict) -> bool:
        """
        Check if the momentum is bullish (positive price movement)
        
        Args:
            price_analysis: Price momentum analysis results
            
        Returns:
            True if bullish momentum detected
        """
        return price_analysis['change_3bars'] > 0 or price_analysis['current_bar'] > 0
    
    def _calculate_price_acceleration(self, df: pd.DataFrame) -> float:
        """Calculate if price movement is accelerating"""
        if len(df) < 6:
            return 0.0
        
        # Calculate rate of change for recent periods
        # ROC for bars -3 to -1 (recent)
        recent_start = df['close'].iloc[-3]
        recent_end = df['close'].iloc[-1]
        recent_bars = 2  # Number of bars between -3 and -1
        recent_roc = ((recent_end - recent_start) / recent_start) / recent_bars if recent_start != 0 else 0
        
        # ROC for bars -6 to -3 (previous)
        prev_start = df['close'].iloc[-6]
        prev_end = df['close'].iloc[-3]
        prev_bars = 3  # Number of bars between -6 and -3
        previous_roc = ((prev_end - prev_start) / prev_start) / prev_bars if prev_start != 0 else 0
        
        # Acceleration = change in rate of change
        if previous_roc != 0:
            acceleration = ((recent_roc - previous_roc) / abs(previous_roc)) * 100
        else:
            # If previous ROC was 0, any positive recent ROC is acceleration
            acceleration = 100.0 if recent_roc > 0 else 0.0
        
        logger.debug(
            'price_acceleration_calculated',
            f'Price acceleration analysis',
            data={
                'recent_roc_per_bar': recent_roc * 100,  # Convert to percentage
                'previous_roc_per_bar': previous_roc * 100,
                'acceleration': acceleration
            }
        )
        
        return float(acceleration)
    
    def _calculate_volume_strength(self, current_vol: float, avg_vol: float, 
                            recent_min: float) -> float:
        """Calculate volume strength relative to recent range"""
        if avg_vol == 0:
            return 0
        
        # How far above recent minimum?
        vol_vs_min = (current_vol - recent_min) / recent_min * 100 if recent_min > 0 else 0
        
        # How does it compare to average?
        vol_vs_avg = (current_vol - avg_vol) / avg_vol * 100
        
        # Combined strength (0-100 scale)
        return min(100, (vol_vs_min * 0.3 + vol_vs_avg * 0.7))
    
    def _identify_momentum_stage(self, volume_analysis: dict, price_analysis: dict) -> str:
        """Identify what stage of momentum we're in"""
        
        if price_analysis['change_4hour'] > 3.0:
            return 'mature'  # Already moved a lot
        elif price_analysis['change_1hour'] > 1.5 and volume_analysis['spike_pct'] > 50:
            return 'developing'  # Building momentum
        elif price_analysis['current_bar'] > 0.5 and price_analysis['trending_up']:
            return 'early'  # Just starting
        else:
            return 'none'

    def _log_momentum_analysis(self, symbol: str, volume_analysis: dict, 
                    price_analysis: dict, volatility: float, score: int, acceleration: float):
        """
        Log detailed momentum analysis for debugging
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
                'price_change_1hour': price_analysis.get('change_1hour', 0),
                'price_change_2hour': price_analysis.get('change_2hour', 0),
                'price_change_4hour': price_analysis.get('change_4hour', 0),
                'price_trending_up': bool(price_analysis['trending_up']),
                'price_acceleration': acceleration,  # NEW
                'avg_volatility': volatility,
                'momentum_score': score,                'current_volume': volume_analysis['current'],
                'recent_avg_volume': volume_analysis['recent_avg']
            }
        )

    def _create_momentum_signal(self, symbol: str, df: pd.DataFrame,
                            volume_analysis: dict, price_analysis: dict,
                            volatility: float, momentum_score: int,
                            acceleration: float, stage: str) -> MomentumSignal:
        """
        Create comprehensive momentum signal object with all analysis data
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with market data
            volume_analysis: Volume pattern analysis results
            price_analysis: Price momentum analysis results
            volatility: Recent market volatility
            momentum_score: Calculated momentum score
            acceleration: Price acceleration metric
            stage: Momentum stage (early/developing/mature/none)
            
        Returns:
            MomentumSignal object with comprehensive data
        """
        best_price_change = max(price_analysis['change_3bars'], price_analysis['current_bar'])
        current_price = float(df['close'].iloc[-1])
        
        # Calculate volume Z-score
        recent_volumes = df['volume'].iloc[-8:].values  # Last 8 periods
        volume_mean = recent_volumes.mean()
        volume_std = recent_volumes.std()
        current_volume = volume_analysis['current']
        volume_zscore = (current_volume - volume_mean) / volume_std if volume_std > 0 else 0
        
        # Check trend alignment
        change_1h = price_analysis.get('change_1hour', 0)
        change_2h = price_analysis.get('change_2hour', 0)
        change_4h = price_analysis.get('change_4hour', 0)
        
        trends_aligned = True
        if change_1h != 0 and change_2h != 0:
            trends_aligned = (change_1h > 0) == (change_2h > 0)
        if trends_aligned and change_2h != 0 and change_4h != 0:
            trends_aligned = (change_2h > 0) == (change_4h > 0)
        
        # Volume-price synchronization
        volume_price_sync = (volume_analysis['spike_pct'] > 0 and 
                        price_analysis['current_bar'] > 0)
        
        logger.info(
            'momentum_detected',
            f'Momentum signal for {symbol}',
            data={
                'symbol': symbol,
                'momentum_score': momentum_score,
                'stage': stage,
                'acceleration': acceleration,
                'volume_spike_pct': volume_analysis['spike_pct'],
                'price_change_3bars': price_analysis['change_3bars'],
                'current_bar_change': price_analysis['current_bar'],
                'timeframe': self.timeframe,
                'trends_aligned': trends_aligned
            }
        )
        
        return MomentumSignal(
            symbol=symbol,
            volume_spike_pct=volume_analysis['spike_pct'],
            price_change_pct=best_price_change,
            candle_timestamp=int(df['timestamp'].iloc[-1]),
            timeframe=self.timeframe,
            # Multi-timeframe price changes
            price_change_1hour=change_1h,
            price_change_2hour=change_2h,
            price_change_4hour=change_4h,
            price_change_current_bar=price_analysis['current_bar'],
            # Volume metrics
            volume_building=volume_analysis['building'],
            volume_zscore=volume_zscore,
            current_volume=current_volume,
            avg_volume=volume_analysis['recent_avg'],
            # Momentum analysis
            momentum_score=momentum_score,
            momentum_stage=stage,
            # Score breakdown (set to 0 since we don't have detailed breakdown)
            volume_score=0,
            price_score=0,
            trend_score=0,
            quality_score=0,
            volatility_score=0,
            # Quality indicators
            trends_aligned=trends_aligned,
            volume_price_sync=volume_price_sync,
            volatility=volatility,
            current_price=current_price
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
