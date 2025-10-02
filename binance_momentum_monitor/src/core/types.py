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
    """Momentum signal data"""
    symbol: str
    volume_spike_pct: float
    price_change_pct: float
    candle_timestamp: int
    timeframe: str
    volume_spike_threshold: Optional[float] = None
    atr_normalized_return: Optional[float] = None
    signal_strength: Optional[float] = None


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
