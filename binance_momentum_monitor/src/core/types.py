"""
Core data types and models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KlineBar:
    """Candlestick/Kline bar data"""
    symbol: str
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    is_final: bool = True


@dataclass
class MomentumSignal:
    """Momentum signal data with comprehensive analysis"""
    # Core identification (required fields first)
    symbol: str
    candle_timestamp: int
    timeframe: str
    
    # Volume metrics (required)
    volume_spike_pct: float
    volume_building: bool
    current_volume: float
    avg_volume: float
    
    # Price metrics - short term (required)
    price_change_pct: float  # Best of 3bars or current
    price_change_current_bar: float
    
    # Price metrics - multi-timeframe (required)
    price_change_1hour: float
    price_change_2hour: float
    price_change_4hour: float
    
    # Momentum analysis (required)
    momentum_score: int
    momentum_stage: str  # early, developing, mature, none
    
    # Quality indicators (required)
    trends_aligned: bool
    volume_price_sync: bool
    volatility: float
    current_price: float
    
    # Score breakdown (required - set to 0 if not available)
    volume_score: float
    price_score: float
    trend_score: float
    quality_score: float
    volatility_score: float
    # EMA trend analysis (optional - Stage 1: data collection only)
    ema_21_daily: Optional[float] = None
    ema_50_daily: Optional[float] = None
    price_vs_ema_21: Optional[str] = None  # 'above', 'below', or 'unknown'
    ema_trend_bias: str = 'neutral'  # 'bullish', 'bearish', or 'neutral'
    
    # TBQR (Taker Buy Quote Ratio) - Buying pressure analysis (optional - data collection)
    tbqr_current: Optional[float] = None  # Current bar's buy/sell ratio (0-1, >0.5 = bullish)
    tbqr_zscore: Optional[float] = None  # Statistical significance vs 20-bar average
    tbqr_delta: Optional[float] = None  # Change from 3-bar average (acceleration)
    quote_volume_zscore: Optional[float] = None  # USD participation level
    
    # Optional fields (all fields with defaults must come last)
    volume_zscore: Optional[float] = None
    signal_strength: Optional[float] = None  # 0-10 scale
    atr_normalized_return: Optional[float] = None
    volume_spike_threshold: Optional[float] = None


@dataclass
class SymbolInfo:
    """Symbol metadata"""
    symbol: str
    contract_type: str
    status: str
    avg_hourly_volume: float
    is_liquid: bool = False


@dataclass
class AlertRecord:
    """Alert record for deduplication"""
    symbol: str
    timeframe: str
    bar_close_time: int
    signature: str
